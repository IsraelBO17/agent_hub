"""Queries for agents. Flushes; never commits."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


_CATALOG_ORDER = (Agent.sort_order, Agent.name, Agent.id)
