"""Enqueue, claim and settle jobs."""

import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import request_id_var
from app.core.jobs.models import Job


async def enqueue(
    session: AsyncSession,
    type_: str,
    payload: dict[str, Any],
    *,
    idempotency_key: str | None = None,
    delay: timedelta = timedelta(),
    max_attempts: int = 5,
) -> None:
    """Add a job inside the caller's transaction (the outbox): it exists if and only if that work
    commits. With an idempotency key, a second enqueue of the same (type, key) is a no-op."""
    stmt = insert(Job).values(
        type=type_,
        payload=payload,
        idempotency_key=idempotency_key,
        request_id=request_id_var.get(),
        run_at=func.now() + delay,
        max_attempts=max_attempts,
    )
    if idempotency_key is not None:
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["type", "idempotency_key"],
            index_where=Job.idempotency_key.is_not(None),
        )
    await session.execute(stmt)


async def claim(session: AsyncSession, *, limit: int, lease: timedelta) -> list[Job]:
    """Claim due jobs. SKIP LOCKED lets several workers claim without blocking each other; an
    expired lease (a crashed worker) makes a running job claimable again."""
    due = (
        select(Job.id)
        .where(
            or_(
                Job.status.in_(("queued", "failed")),
                (Job.status == "running") & (Job.locked_until < func.now()),
            ),
            Job.run_at <= func.now(),
        )
        .order_by(Job.run_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    rows = await session.scalars(
        update(Job)
        .where(Job.id.in_(due))
        .values(status="running", attempts=Job.attempts + 1, locked_until=func.now() + lease)
        .returning(Job)
    )
    return list(rows)


async def mark_succeeded(session: AsyncSession, job_id: uuid.UUID) -> None:
    await session.execute(
        update(Job).where(Job.id == job_id).values(status="succeeded", locked_until=None)
    )


async def mark_failed(
    session: AsyncSession, job: Job, error: dict[str, Any], *, backoff: timedelta
) -> str:
    """Retry later with backoff, or dead-letter after max_attempts. Returns the new status."""
    status = "dead" if job.attempts >= job.max_attempts else "failed"
    await session.execute(
        update(Job)
        .where(Job.id == job.id)
        .values(status=status, last_error=error, locked_until=None, run_at=func.now() + backoff)
    )
    return status


async def purge_finished(session: AsyncSession, *, older_than: timedelta, limit: int) -> int:
    """Delete succeeded jobs older than the retention window, oldest first, at most `limit`."""
    old = (
        select(Job.id)
        .where(Job.status == "succeeded", Job.updated_at < func.now() - older_than)
        .order_by(Job.updated_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(delete(Job).where(Job.id.in_(old)).returning(Job.id))
    return len(result.all())
