"""The agents feature's door (standard §7): what other features may use.

- `get_for_send` / `refs_by_ids`: the agent a message goes to, and the agent fields shown beside
  sessions. Frozen dataclasses, never rows; the caller's session; no commits.
- `provide_session_stats`: the hook behind `myStats`. Sessions belong to the chat feature, which
  already depends on this one, so `main.py` hands its counting function in here instead of agents
  importing chat (no cycle).
"""

import uuid
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.agents.descriptor import SLUG
from app.features.agents.exceptions import AgentNotFound
from app.features.agents.models import Agent
from app.features.agents.repository import AgentRepository

__all__ = [
    "SLUG",
    "AgentForSend",
    "AgentNotFound",
    "AgentRef",
    "AgentStats",
    "SessionStats",
    "get_for_send",
    "get_for_send_by_id",
    "provide_session_stats",
    "refs_by_ids",
]


@dataclass(frozen=True)
class AgentRef:
    """The contract's AgentRef: the agent fields shown next to sessions."""

    id: uuid.UUID
    slug: str
    name: str
    icon: str
    color: str
    status: str
    stage: str
    retired: bool


@dataclass(frozen=True)
class AgentForSend:
    """What sending a message needs to know about its agent."""

    ref: AgentRef
    version: str | None
    runtime_type: str
    runtime_arn: str | None
    runtime_qualifier: str | None
    attachments_enabled: bool
    settings: Mapping[str, Any]  # history budget and run cap overrides (D11, D18), if any


@dataclass(frozen=True)
class AgentStats:
    session_count: int
    last_active_at: datetime | None


SessionStats = Callable[
    [AsyncSession, uuid.UUID, Sequence[uuid.UUID]], Awaitable[Mapping[uuid.UUID, AgentStats]]
]
_session_stats: SessionStats | None = None


def provide_session_stats(fn: SessionStats) -> None:
    """Called once by main.py with the chat feature's counting function."""
    global _session_stats
    _session_stats = fn


def session_stats() -> SessionStats:
    if _session_stats is None:
        raise RuntimeError("main.py must call provide_session_stats() before agents are served")
    return _session_stats


def _ref(agent: Agent) -> AgentRef:
    return AgentRef(
        id=agent.id,
        slug=agent.slug,
        name=agent.name,
        icon=agent.icon,
        color=agent.color,
        status=agent.status,
        stage=agent.stage,
        retired=agent.retired_at is not None,
    )


async def get_for_send(session: AsyncSession, slug: str) -> AgentForSend:
    """Raises AgentNotFound. Retired and offline agents are returned; the caller refuses them."""
    agent = await AgentRepository(session).by_slug(slug)
    if agent is None:
        raise AgentNotFound()
    return await _for_send(agent)


async def get_for_send_by_id(session: AsyncSession, agent_id: uuid.UUID) -> AgentForSend:
    agent = await session.get(Agent, agent_id)
    if agent is None:  # sessions reference agents with ON DELETE RESTRICT, so this is a bug
        raise AgentNotFound()
    return await _for_send(agent)


async def _for_send(agent: Agent) -> AgentForSend:
    attachments = (agent.capabilities or {}).get("attachments") or {}
    return AgentForSend(
        ref=_ref(agent),
        version=agent.version,
        runtime_type=agent.runtime_type,
        runtime_arn=agent.runtime_arn,
        runtime_qualifier=agent.runtime_qualifier,
        attachments_enabled=bool(attachments.get("enabled")),
        settings=dict(agent.settings or {}),
    )


async def refs_by_ids(
    session: AsyncSession, agent_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, AgentRef]:
    if not agent_ids:
        return {}
    rows = await session.scalars(select(Agent).where(Agent.id.in_(set(agent_ids))))
    return {a.id: _ref(a) for a in rows}
