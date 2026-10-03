"""Queries for sessions, messages and tool_calls. Every query filters by owner. Flushes; never commits."""

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.chat.models import Message, Session, ToolCall

RUNNING = "streaming"
OPEN = ("streaming", "awaiting_approval")


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------ sessions

    async def live_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> Session | None:
        return await self.session.scalar(
            select(Session).where(
                Session.id == session_id, Session.user_id == user_id, Session.deleted_at.is_(None)
            )
        )

    async def add(self, row: Session | Message | ToolCall) -> None:
        self.session.add(row)
        await self.session.flush()

    async def session_counts(self, session_id: uuid.UUID) -> tuple[int, bool]:
        """(message count, whether a reply is streaming) for SessionSummary."""
        count, running = (
            await self.session.execute(
                select(func.count(), func.count().filter(Message.status == RUNNING)).where(
                    Message.session_id == session_id
                )
            )
        ).one()
        return int(count), bool(running)

    async def agent_stats(
        self, user_id: uuid.UUID, agent_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[int, datetime | None]]:
        """This user's sessions per agent (archived included, deleted not): count, latest."""
        if not agent_ids:
            return {}
        rows = await self.session.execute(
            select(Session.agent_id, func.count(), func.max(Session.last_message_at))
            .where(
                Session.user_id == user_id,
                Session.agent_id.in_(agent_ids),
                Session.deleted_at.is_(None),
            )
            .group_by(Session.agent_id)
        )
        return {agent_id: (count, last) for agent_id, count, last in rows}

    async def touch_session(self, session_id: uuid.UUID, at: datetime) -> None:
        await self.session.execute(
            update(Session).where(Session.id == session_id).values(last_message_at=at)
        )

    # ------------------------------------------------------------------ sends

    async def lock_user_sends(self, user_id: uuid.UUID) -> None:
        """Serialise this user's sends until commit, so the run count and `seq` can't race."""
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 0))"),
            {"k": f"chat.send:{user_id}"},
        )

    async def by_client_message_id(
        self, user_id: uuid.UUID, client_message_id: uuid.UUID
    ) -> Message | None:
        return await self.session.scalar(
            select(Message).where(
                Message.user_id == user_id, Message.client_message_id == client_message_id
            )
        )

    async def reply_to(self, user_id: uuid.UUID, user_message_id: uuid.UUID) -> Message | None:
        return await self.session.scalar(
            select(Message)
            .where(Message.user_id == user_id, Message.reply_to_id == user_message_id)
            .order_by(Message.seq)
            .limit(1)
        )

    async def running_count(self, user_id: uuid.UUID) -> int:
        count = await self.session.scalar(
            select(func.count()).where(Message.user_id == user_id, Message.status == RUNNING)
        )
        return int(count or 0)

    async def open_reply(self, session_id: uuid.UUID) -> Message | None:
        return await self.session.scalar(
            select(Message).where(Message.session_id == session_id, Message.status.in_(OPEN))
        )

    async def next_seq(self, session_id: uuid.UUID) -> int:
        top = await self.session.scalar(
            select(func.max(Message.seq)).where(Message.session_id == session_id)
        )
        return int(top or 0) + 1

    # ------------------------------------------------------------------ reads

    async def message(self, user_id: uuid.UUID, message_id: uuid.UUID) -> Message | None:
        """This user's message in a session that isn't deleted."""
        return await self.session.scalar(
            select(Message)
            .join(Session, Session.id == Message.session_id)
            .where(
                Message.id == message_id,
                Message.user_id == user_id,
                Session.deleted_at.is_(None),
            )
        )

    async def page(
        self, user_id: uuid.UUID, session_id: uuid.UUID, *, before: int | None, limit: int
    ) -> list[Message]:
        """Newest first, `limit + 1` rows (the extra one says whether there are older ones)."""
        query = select(Message).where(Message.session_id == session_id, Message.user_id == user_id)
        if before is not None:
            query = query.where(Message.seq < before)
        return list(await self.session.scalars(query.order_by(Message.seq.desc()).limit(limit + 1)))

    async def tool_calls(
        self, user_id: uuid.UUID, ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, ToolCall]:
        if not ids:
            return {}
        rows = await self.session.scalars(
            select(ToolCall).where(ToolCall.user_id == user_id, ToolCall.id.in_(set(ids)))
        )
        return {row.id: row for row in rows}

    # ------------------------------------------------------------------ the run's writes

    async def update_message(self, message_id: uuid.UUID, **values: Any) -> None:
        await self.session.execute(update(Message).where(Message.id == message_id).values(**values))

    async def update_tool_call(self, tool_call_id: uuid.UUID, **values: Any) -> None:
        await self.session.execute(
            update(ToolCall).where(ToolCall.id == tool_call_id).values(**values)
        )

    async def stop_requested(self, message_id: uuid.UUID) -> bool:
        flag = await self.session.scalar(
            select(Message.cancel_requested_at).where(Message.id == message_id)
        )
        return flag is not None

    async def request_stop(self, message_id: uuid.UUID, at: datetime) -> str | None:
        """Sets the flag on a `streaming` reply (keeping an earlier one); returns the status, or
        None if the message isn't streaming (left alone)."""
        status = await self.session.scalar(
            update(Message)
            .where(Message.id == message_id, Message.status == RUNNING)
            .values(cancel_requested_at=func.coalesce(Message.cancel_requested_at, at))
            .returning(Message.status)
        )
        return status

    async def stale_replies(self, cutoff: datetime, limit: int) -> list[Message]:
        """`streaming` replies whose task stopped writing its heartbeat, oldest first, locked so two
        sweeps (two tasks during a deploy) never take the same row."""
        return list(
            await self.session.scalars(
                select(Message)
                .where(Message.status == RUNNING, Message.heartbeat_at < cutoff)
                .order_by(Message.heartbeat_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        )

    async def cancel_running_tools(self, message_id: uuid.UUID, at: datetime) -> None:
        await self.session.execute(
            update(ToolCall)
            .where(ToolCall.message_id == message_id, ToolCall.status == "running")
            .values(status="cancelled", completed_at=at)
        )
