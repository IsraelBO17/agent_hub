"""The chat feature's door (standard §7). Only what another feature needs: the session counts
behind the catalog's `myStats`, handed to the agents feature by main.py (agents can't import chat:
chat already depends on agents)."""

import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.agents.public import AgentStats
from app.features.chat.repository import ChatRepository


async def session_stats(
    session: AsyncSession, user_id: uuid.UUID, agent_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, AgentStats]:
    """Batch: this user's sessions per agent (archived count, deleted don't)."""
    stats = await ChatRepository(session).agent_stats(user_id, agent_ids)
    return {a: AgentStats(session_count=c, last_active_at=t) for a, (c, t) in stats.items()}
