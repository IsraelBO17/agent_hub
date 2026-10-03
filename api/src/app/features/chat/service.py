"""Chat rules and transactions: one method per capability block in SPEC.md (feature: chat)."""

import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import request_id_var
from app.core.db import constraint_name
from app.core.errors import ShuttingDown
from app.core.lifecycle import shutting_down
from app.core.service import BaseService
from app.core.settings import Settings
from app.features.agents import public as agents
from app.features.chat import runs
from app.features.chat.exceptions import (
    AgentRetired,
    AgentUnavailable,
    AttachmentsNotSupported,
    EmptyMessage,
    FileNotReady,
    IdempotencyConflict,
    MessageNotFound,
    MessageTooLong,
    QuestionNotOpen,
    RunInProgress,
    SessionNotFound,
    TooManyRuns,
)
from app.features.chat.models import Message, Session, ToolCall
from app.features.chat.repository import ChatRepository
from app.features.chat.runs import RunSettings, RunSpec
from app.features.chat.schemas import (
    MAX_TEXT,
    AgentRefOut,
    MessageOut,
    MessagePage,
    SendMessageRequest,
    SendReplay,
    SessionSummaryOut,
    StopAccepted,
)

TITLE_CHARS = 60  # D21
HISTORY_TURNS = 20  # D18 defaults; an agent's settings may override them
HISTORY_CHARS = 32_000
TRUNCATED = "\n\n… [truncated]"  # ends a turn cut to fit the history budget (D18)


@dataclass(frozen=True)
class Started:
    """A send that committed: the run to start, and the first event's content."""

    spec: RunSpec
    settings: RunSettings
    session: SessionSummaryOut | None  # when this call created it
    user_message: MessageOut


def title_of(text: str) -> str:
    """D21: whitespace collapsed, cut at a word boundary to about 60 characters."""
    flat = " ".join(text.split())
    if len(flat) <= TITLE_CHARS:
        return flat or "New session"
    window = flat[: TITLE_CHARS + 1]
    cut = window.rsplit(" ", 1)[0] if " " in window else ""
    # A word boundary unless that throws away more than half; then a hard cut.
    return (cut if len(cut) >= TITLE_CHARS // 2 else flat[:TITLE_CHARS]).rstrip()


def ref_out(ref: agents.AgentRef) -> AgentRefOut:
    return AgentRefOut(
        id=ref.id,
        slug=ref.slug,
        name=ref.name,
        icon=ref.icon,
        color=ref.color,
        status=ref.status,
        stage=ref.stage,
        retired=ref.retired,
    )


def tool_call_wire(row: ToolCall) -> dict[str, Any]:
    output = row.output or {}
    return {
        "id": str(row.id),
        "toolUseId": row.tool_use_id,
        "name": row.name,
        "status": row.status,
        "summary": row.summary,
        "input": (row.input or {}).get("value"),
        "output": output.get("value"),
        "outputFile": None,  # large outputs as files arrive with the files feature
        "error": output.get("error"),
        "startedAt": row.started_at.isoformat().replace("+00:00", "Z"),
        "completedAt": row.completed_at.isoformat().replace("+00:00", "Z")
        if row.completed_at
        else None,
    }


def message_out(row: Message, tools: dict[uuid.UUID, ToolCall]) -> MessageOut:
    """The wire message: stored tool references hydrated from their rows (P6)."""
    blocks: list[dict[str, Any]] = []
    for block in row.blocks or []:
        if block.get("type") == "tool" and "toolCallId" in block:
            call = tools.get(uuid.UUID(block["toolCallId"]))
            if call is None:  # the row is written with the block; skip rather than break a page
                continue
            blocks.append({"id": block["id"], "type": "tool", "toolCall": tool_call_wire(call)})
        else:
            blocks.append(block)
    return MessageOut(
        id=row.id,
        session_id=row.session_id,
        seq=row.seq,
        role=row.role,
        status=row.status,
        blocks=blocks,
        client_message_id=row.client_message_id,
        reply_to_id=row.reply_to_id,
        agent_version=row.agent_version,
        error=row.error,
        usage=row.usage,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
    )


def tool_ids(rows: Sequence[Message]) -> list[uuid.UUID]:
    return [
        uuid.UUID(b["toolCallId"])
        for row in rows
        for b in row.blocks or []
        if b.get("type") == "tool" and "toolCallId" in b
    ]


def flatten(message: MessageOut) -> str:
    """A turn as plain text for the agent (D18): text kept, thinking dropped, a tool as one line."""
    parts: list[str] = []
    for block in message.blocks:
        if block["type"] == "text" and block.get("text"):
            parts.append(block["text"])
        elif block["type"] == "tool":
            call = block["toolCall"]
            parts.append(f"[tool {call['name']}: {call['summary'] or call['status']}]")
    return "\n\n".join(parts)


def pick_history(
    turns: Iterable[tuple[str, str]], max_turns: int, max_chars: int
) -> list[dict[str, str]]:
    """D18: earlier turns (role, text), newest first in, oldest first out, within the budget.

    The turn that crosses the character budget goes in cut to the room left, keeping its
    start and marked as truncated, and ends the history; so one oversize turn never empties
    it, and the most recent earlier turn is always there. Empty turns are skipped.
    """
    picked: list[dict[str, str]] = []
    used = 0
    for role, text in turns:
        if not text:
            continue
        if len(picked) >= max_turns:
            break
        room = max_chars - used
        if len(text) > room:
            if picked and room <= len(TRUNCATED):
                break  # no room for any of it
            picked.append({"role": role, "text": text[: max(room - len(TRUNCATED), 0)] + TRUNCATED})
            break
        picked.append({"role": role, "text": text})
        used += len(text)
    return picked[::-1]


class ChatService(BaseService):
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        super().__init__(session)
        self.settings = settings
        self.repo = ChatRepository(session)

    # ------------------------------------------------------------------ sends

    async def start(
        self, user_id: uuid.UUID, slug: str, body: SendMessageRequest
    ) -> Started | SendReplay:
        text = self._check_body(body)
        agent = await agents.get_for_send(self.session, slug)  # 404 agent_not_found
        return await self._send(user_id, agent, None, body, text)

    async def send(
        self, user_id: uuid.UUID, session_id: uuid.UUID, body: SendMessageRequest
    ) -> Started | SendReplay:
        text = self._check_body(body)
        chat = await self.repo.live_session(user_id, session_id)
        if chat is None:
            raise SessionNotFound()
        agent = await agents.get_for_send_by_id(self.session, chat.agent_id)
        return await self._send(user_id, agent, chat, body, text)

    def _check_body(self, body: SendMessageRequest) -> str:
        text = body.text or ""
        if len(text) > MAX_TEXT:
            raise MessageTooLong()
        if not text.strip() and not body.file_ids and body.answer is None:
            raise EmptyMessage()
        return text

    async def _send(
        self,
        user_id: uuid.UUID,
        agent: agents.AgentForSend,
        chat: Session | None,
        body: SendMessageRequest,
        text: str,
        *,
        retried: bool = False,
    ) -> Started | SendReplay:
        try:
            async with self.transaction():
                await self.repo.lock_user_sends(user_id)
                replay = await self._replay(user_id, agent, chat, body, text)
                if replay is not None:
                    return replay
                self._refuse(agent, body)
                if await self.repo.running_count(user_id) >= self.settings.max_running_replies:
                    raise TooManyRuns(retry_after=10)
                if chat is not None and await self.repo.open_reply(chat.id) is not None:
                    raise RunInProgress()
                return await self._insert(user_id, agent, chat, body, text)
        except IntegrityError as exc:
            name = constraint_name(exc)
            if name == "uq_messages_user_id_client_message_id" and not retried:
                # Two identical sends at once: the other one won; this one replays it.
                return await self._send(user_id, agent, chat, body, text, retried=True)
            if name == "uq_messages_open_reply_per_session":
                raise RunInProgress() from exc
            raise

    async def _replay(
        self,
        user_id: uuid.UUID,
        agent: agents.AgentForSend,
        chat: Session | None,
        body: SendMessageRequest,
        text: str,
    ) -> SendReplay | None:
        """Rule 4: a resend with the same `clientMessageId` returns what the first one saved."""
        sent = await self.repo.by_client_message_id(user_id, body.client_message_id)
        if sent is None:
            return None
        original = await self.repo.live_session(user_id, sent.session_id)
        same = (
            original is not None
            and original.agent_id == agent.ref.id
            and (chat is None or chat.id == original.id)
            and _text_of(sent) == text
        )
        reply = await self.repo.reply_to(user_id, sent.id)
        if not same or original is None or reply is None:
            raise IdempotencyConflict()
        rows = [sent, reply]
        tools = await self.repo.tool_calls(user_id, tool_ids(rows))
        return SendReplay(
            session=await self._summary(original, agent.ref),
            user_message=message_out(sent, tools),
            assistant_message=message_out(reply, tools),
        )

    def _refuse(self, agent: agents.AgentForSend, body: SendMessageRequest) -> None:
        if shutting_down.is_set():
            raise ShuttingDown(retry_after=5)
        if agent.ref.retired:
            raise AgentRetired()
        if agent.ref.status == "offline":
            raise AgentUnavailable("The agent is offline.")
        if agent.runtime_type != "agentcore" or not agent.runtime_arn:
            raise AgentUnavailable("This agent's runtime type can't be called yet.")
        if body.file_ids:
            if not agent.attachments_enabled:
                raise AttachmentsNotSupported()
            raise FileNotReady("Uploads aren't available yet.")
        if body.answer is not None:
            raise QuestionNotOpen()

    async def _insert(
        self,
        user_id: uuid.UUID,
        agent: agents.AgentForSend,
        chat: Session | None,
        body: SendMessageRequest,
        text: str,
    ) -> Started:
        now = datetime.now(UTC)
        created = chat is None
        history: list[dict[str, str]] = []
        if chat is None:
            chat = Session(
                user_id=user_id,
                agent_id=agent.ref.id,
                title=title_of(text),
                title_source="auto",
                last_message_at=now,
            )
            await self.repo.add(chat)
        else:
            history = await self._history(user_id, chat.id, agent)
            await self.repo.touch_session(chat.id, now)
        seq = await self.repo.next_seq(chat.id)
        user_message = Message(
            session_id=chat.id,
            user_id=user_id,
            seq=seq,
            role="user",
            status="complete",
            blocks=[{"id": "b1", "type": "text", "text": text}],
            client_message_id=body.client_message_id,
            search_text=text,
        )
        await self.repo.add(user_message)
        reply = Message(
            session_id=chat.id,
            user_id=user_id,
            seq=seq + 1,
            role="assistant",
            status="streaming",
            blocks=[],
            reply_to_id=user_message.id,
            agent_version=agent.version,
            started_at=now,
            heartbeat_at=now,
        )
        await self.repo.add(reply)
        await self.session.refresh(user_message)
        await self.session.refresh(reply)
        await self.session.refresh(chat)
        assistant = message_out(reply, {})
        payload = {
            "messages": history,
            "input": text,
            "attachments": [],
            "context": {
                "sessionId": str(chat.id),
                "messageId": str(reply.id),
                "agentVersion": agent.version,
            },
        }
        spec = RunSpec(
            message_id=reply.id,
            session_id=chat.id,
            user_id=user_id,
            request_id=request_id_var.get(),
            runtime_arn=agent.runtime_arn or "",
            qualifier=agent.runtime_qualifier or "DEFAULT",
            payload=payload,
            assistant=assistant,
        )
        limit = agent.settings.get("runTimeLimitSeconds")
        run_settings = RunSettings(
            time_limit_seconds=float(limit)
            if isinstance(limit, int | float)
            else self.settings.stream_time_limit_seconds,
            drain_seconds=self.settings.shutdown_grace_seconds,
        )
        return Started(
            spec=spec,
            settings=run_settings,
            session=await self._summary(chat, agent.ref) if created else None,
            user_message=message_out(user_message, {}),
        )

    async def _history(
        self, user_id: uuid.UUID, session_id: uuid.UUID, agent: agents.AgentForSend
    ) -> list[dict[str, str]]:
        """D18: earlier turns, oldest first, within the agent's budget (turns and characters).

        Read before the new user message is added: that goes as `input`, outside the budget.
        """
        turns = agent.settings.get("historyTurns", HISTORY_TURNS)
        chars = agent.settings.get("historyChars", HISTORY_CHARS)
        rows = await self.repo.page(user_id, session_id, before=None, limit=int(turns) * 2)
        tools = await self.repo.tool_calls(user_id, tool_ids(rows))
        texts = ((row.role, flatten(message_out(row, tools))) for row in rows)  # newest first
        return pick_history(texts, int(turns), int(chars))

    async def _summary(self, chat: Session, ref: agents.AgentRef) -> SessionSummaryOut:
        count, running = await self.repo.session_counts(chat.id)
        return SessionSummaryOut(
            id=chat.id,
            agent=ref_out(ref),
            title=chat.title or "New session",
            title_source=chat.title_source or "auto",
            created_at=chat.created_at,
            last_message_at=chat.last_message_at,
            pinned_at=chat.pinned_at,
            archived_at=chat.archived_at,
            is_running=running,
            pending_approvals=0,  # approvals arrive with D19's slice
            message_count=count,
        )

    # ------------------------------------------------------------------ stop

    async def stop(self, user_id: uuid.UUID, message_id: uuid.UUID) -> StopAccepted:
        """P4: the flag is the signal, read by whichever task runs the reply."""
        message = await self.repo.message(user_id, message_id)
        if message is None:
            raise MessageNotFound()
        async with self.transaction():
            status = await self.repo.request_stop(message.id, datetime.now(UTC))
        if status is None:  # already ended (or a user message): report it as it is
            return StopAccepted(message_id=message.id, status=message.status)
        runs.signal_stop(message.id)  # committed; if this task runs the reply, act now
        return StopAccepted(message_id=message.id, status=status)

    # ------------------------------------------------------------------ reads

    async def get_message(self, user_id: uuid.UUID, message_id: uuid.UUID) -> MessageOut:
        row = await self.repo.message(user_id, message_id)
        if row is None:
            raise MessageNotFound()
        return message_out(row, await self.repo.tool_calls(user_id, tool_ids([row])))

    async def list_messages(
        self, user_id: uuid.UUID, session_id: uuid.UUID, *, before: int | None, limit: int
    ) -> MessagePage:
        if await self.repo.live_session(user_id, session_id) is None:
            raise SessionNotFound()
        rows = await self.repo.page(user_id, session_id, before=before, limit=limit)
        more, rows = len(rows) > limit, rows[:limit]
        rows.reverse()  # oldest first within the page
        tools = await self.repo.tool_calls(user_id, tool_ids(rows))
        return MessagePage(
            items=[message_out(r, tools) for r in rows],
            next_before=rows[0].seq if more and rows else None,
        )


def _text_of(message: Message) -> str:
    return "".join(b.get("text", "") for b in message.blocks or [] if b.get("type") == "text")
