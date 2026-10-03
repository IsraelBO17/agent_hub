"""Agent rules and transactions: one method per capability block in SPEC.md (feature: agents)."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlparse

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import constraint_name
from app.core.errors import Conflict
from app.core.service import BaseService
from app.core.settings import Settings
from app.features.agents.descriptor import (
    AgentCapabilities,
    AgentDescriptor,
    AgentDetails,
    AgentTool,
    Starter,
)
from app.features.agents.exceptions import AgentNotFound
from app.features.agents.models import Agent
from app.features.agents.repository import AgentRepository
from app.features.agents.schemas import AgentList, AgentOut, MyStats


@dataclass(frozen=True)
class Registered:
    """What `hub agents add` did."""

    action: Literal["added", "updated", "unchanged"]
    agent: Agent
    previous_version: str | None = None


def runtime_label(agent: Agent) -> str | None:
    """A short form of the runtime target for display; never the account id."""
    if agent.runtime_arn:
        return "arn:…:runtime/" + agent.runtime_arn.rsplit("/", 1)[-1]
    if agent.runtime_endpoint:
        return urlparse(agent.runtime_endpoint).hostname
    return None


def to_out(agent: Agent, stats: tuple[int, datetime | None]) -> AgentOut:
    details = AgentDetails.model_validate(agent.details)
    if details.runtime_label is None:
        details.runtime_label = runtime_label(agent)
    return AgentOut(
        id=agent.id,
        slug=agent.slug,
        name=agent.name,
        description=agent.description,
        tagline=agent.tagline,
        greeting=agent.greeting,
        icon=agent.icon,
        color=agent.color,
        stage=agent.stage,
        status=agent.status,
        status_changed_at=agent.status_changed_at,
        framework=agent.framework,
        runtime_type=agent.runtime_type,
        version=agent.version,
        deployed_at=agent.deployed_at,
        details=details,
        disclaimer=agent.disclaimer,
        capabilities=AgentCapabilities.model_validate(agent.capabilities),
        tools=[AgentTool.model_validate(t) for t in agent.tools],
        starters=[Starter.model_validate(s) for s in agent.starters],
        retired_at=agent.retired_at,
        my_stats=MyStats(session_count=stats[0], last_active_at=stats[1]),
    )


def columns_of(d: AgentDescriptor) -> dict[str, Any]:
    """The descriptor as `agents` column values; nested objects stored in their wire shape."""
    return {
        "slug": d.slug,
        "name": d.name,
        "description": d.description,
        "tagline": d.tagline,
        "greeting": d.greeting,
        "icon": d.icon,
        "color": d.color,
        "stage": d.stage,
        "visibility": d.visibility,
        "sort_order": d.sort_order,
        "version": d.version,
        "framework": d.framework,
        "runtime_type": d.runtime_type,
        "runtime_arn": d.runtime_arn,
        "runtime_qualifier": d.runtime_qualifier,
        "runtime_endpoint": d.runtime_endpoint,
        "details": d.details.model_dump(),
        "disclaimer": d.disclaimer,
        "capabilities": d.capabilities.model_dump(),
        "tools": [t.model_dump() for t in d.tools],
        "starters": [s.model_dump() for s in d.starters],
    }


NO_STATS: tuple[int, datetime | None] = (0, None)


class AgentService(BaseService):
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        super().__init__(session)
        self.settings = settings
        self.agents = AgentRepository(session)

    async def list_agents(self, user_id: uuid.UUID) -> AgentList:
        # Hidden agents (the Scenario Agent) are for testing: shown everywhere but production.
        agents = await self.agents.catalog(include_hidden=self.settings.env != "prod")
        stats = await self.agents.stats(user_id, [a.id for a in agents])
        return AgentList(items=[to_out(a, stats.get(a.id, NO_STATS)) for a in agents])

    async def get_agent(self, user_id: uuid.UUID, slug: str) -> AgentOut:
        agent = await self.agents.by_slug(slug)
        if agent is None:
            raise AgentNotFound()
        stats = await self.agents.stats(user_id, [agent.id])
        return to_out(agent, stats.get(agent.id, NO_STATS))

    async def register(self, descriptor: AgentDescriptor) -> Registered:
        """Operator command: insert the agent, or update it to match its descriptor. Health
        `status` and `retired_at` are not descriptor fields and are left alone."""
        values = columns_of(descriptor)
        now = datetime.now(UTC)
        try:
            async with self.transaction():
                agent = await self.agents.by_slug(descriptor.slug, for_update=True)
                if agent is None:
                    agent = Agent(**values, deployed_at=now if descriptor.version else None)
                    await self.agents.add(agent)
                    return Registered("added", agent)
                changed = {k: v for k, v in values.items() if getattr(agent, k) != v}
                if not changed:
                    return Registered("unchanged", agent)
                previous = agent.version
                for key, value in changed.items():
                    setattr(agent, key, value)
                if "version" in changed:
                    agent.deployed_at = now  # drives the "Agent updated" divider
                await self.agents.flush()
                return Registered("updated", agent, previous)
        except IntegrityError as exc:
            if constraint_name(exc) == "uq_agents_slug":  # added at the same moment elsewhere
                raise Conflict(detail=f"{descriptor.slug} was just added; run it again") from exc
            raise

    async def registry(self) -> list[Agent]:
        return await self.agents.every()
