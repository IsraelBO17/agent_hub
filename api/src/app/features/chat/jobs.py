"""Chat's sweep (standard §13): replies whose task died (P1, SEND_MESSAGE rule 13)."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import problem_body
from app.core.jobs.registry import sweep
from app.features.chat.exceptions import RunInterrupted
from app.features.chat.repository import ChatRepository

log = logging.getLogger("app.chat")

STALE_AFTER = timedelta(seconds=60)
BATCH = 100


@sweep("chat.interrupt_stale_replies", every=timedelta(minutes=1))
async def interrupt_stale_replies(session: AsyncSession) -> int:
    """`streaming` replies with no heartbeat for 60 s become `interrupted`; their running tools
    `cancelled`. A run alive on another task (a deploy) keeps its heartbeat fresh, so it's left
    alone. Bounded, oldest first; idempotent (a second pass finds nothing)."""
    repo = ChatRepository(session)
    now = datetime.now(UTC)
    stale = await repo.stale_replies(now - STALE_AFTER, BATCH)
    error = problem_body(RunInterrupted("The reply stopped because the service restarted."))
    for message in stale:
        await repo.cancel_running_tools(message.id, now)
        await repo.update_message(message.id, status="interrupted", error=error, completed_at=now)
    if len(stale) == BATCH:
        log.warning("sweep_capped", extra={"sweep": "chat.interrupt_stale_replies", "batch": BATCH})
    return len(stale)
