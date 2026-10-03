"""Queries for agents, and the signed-in user's session counts per agent. Flushes; never commits."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session  # sessions isn't a feature yet (#8); read-only here
from app.features.agents.models import Agent


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def catalog(self, *, include_hidden: bool) -> list[Agent]:
        query = select(Agent).where(Agent.retired_at.is_(None))
        if not include_hidden:
            query = query.where(Agent.visibility == "listed")
        return list(await self.session.scalars(query.order_by(*_CATALOG_ORDER)))

    async def every(self) -> list[Agent]:
        """The whole registry, retired and hidden included (operator listing)."""
        return list(await self.session.scalars(select(Agent).order_by(*_CATALOG_ORDER)))

    async def by_slug(self, slug: str, *, for_update: bool = False) -> Agent | None:
        query = select(Agent).where(Agent.slug == slug)
        return await self.session.scalar(query.with_for_update() if for_update else query)

    async def add(self, agent: Agent) -> None:
        self.session.add(agent)
        await self.session.flush()

    async def flush(self) -> None:
        await self.session.flush()

    async def stats(
        self, user_id: uuid.UUID, agent_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[int, datetime | None]]:
        """This user's sessions per agent (archived included, deleted not): count, latest."""
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


_CATALOG_ORDER = (Agent.sort_order, Agent.name, Agent.id)
