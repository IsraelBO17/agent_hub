"""Runs claimed jobs and due sweeps. Used by worker.py and, for small services, by the API process."""

import asyncio
import contextlib
import logging
import time
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.context import request_id_var
from app.core.jobs.models import Job
from app.core.jobs.queue import claim, mark_failed, mark_succeeded, purge_finished
from app.core.jobs.registry import HANDLERS, SWEEPS, sweep
from app.core.settings import Settings

log = logging.getLogger("app.jobs")


def backoff_for(attempts: int) -> timedelta:
    return timedelta(seconds=min(3600, 10 * attempts**2))


async def run_job(sessions: async_sessionmaker[AsyncSession], job: Job) -> str:
    """Run one claimed job: the handler's writes and 'succeeded' commit together; on failure they
    roll back and the job is retried or dead-lettered in a separate transaction."""
    token = request_id_var.set(job.request_id or "-")
    started = time.perf_counter()
    try:
        spec = HANDLERS.get(job.type)
        try:
            if spec is None:
                raise LookupError(f"no handler registered for {job.type!r}")
            payload = spec.payload_model.model_validate(job.payload)
            async with sessions() as session, session.begin():
                await spec.handler(session, payload)
                await mark_succeeded(session, job.id)
            status = "succeeded"
        except Exception as exc:
            error = {
                "type": "about:blank",
                "title": "Job failed",
                "status": 500,
                "code": "job_failed",
                "detail": f"{type(exc).__name__}: {exc}"[:1000],
                "requestId": job.request_id or "-",
                "retryable": True,
            }
            async with sessions() as session, session.begin():
                status = await mark_failed(session, job, error, backoff=backoff_for(job.attempts))
            log.log(
                logging.ERROR if status == "dead" else logging.WARNING,
                "job_failed",
                extra={"job_type": job.type, "job_id": str(job.id)},
                exc_info=exc,
            )
        log.info(
            "job",
            extra={
                "job_type": job.type,
                "job_id": str(job.id),
                "status": status,
                "attempts": job.attempts,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return status
    finally:
        request_id_var.reset(token)


async def run_due_jobs(sessions: async_sessionmaker[AsyncSession], settings: Settings) -> int:
    """Claim a batch and run it. Returns how many jobs ran."""
    async with sessions() as session, session.begin():
        jobs = await claim(
            session,
            limit=settings.worker_batch_size,
            lease=timedelta(seconds=settings.job_lease_seconds),
        )
    for job in jobs:
        await run_job(sessions, job)
    return len(jobs)


class SweepClock:
    """Runs each registered sweep at its interval. In-memory per process: with several workers a
    sweep may run more than once per interval, which is why sweeps must be idempotent."""

    def __init__(self) -> None:
        self._next: dict[str, float] = {}

    async def run_due(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        now = time.monotonic()
        for spec in SWEEPS.values():
            if self._next.get(spec.name, 0.0) > now:
                continue
            self._next[spec.name] = now + spec.every.total_seconds()
            try:
                async with sessions() as session, session.begin():
                    count = await spec.fn(session)
                log.info("sweep", extra={"sweep": spec.name, "count": count})
            except Exception:
                log.exception("sweep_failed", extra={"sweep": spec.name})


async def work_loop(
    sessions: async_sessionmaker[AsyncSession], settings: Settings, stop: asyncio.Event
) -> None:
    """Poll for jobs and sweeps until `stop` is set; finishes the batch in hand before returning."""
    clock = SweepClock()
    while not stop.is_set():
        try:
            await clock.run_due(sessions)
            ran = await run_due_jobs(sessions, settings)
        except Exception:
            log.exception("worker_loop_error")
            ran = 0
        if ran == 0:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=settings.worker_poll_seconds)


# The job table's own retention: core/jobs owns `jobs`, so its sweep lives here.
PURGE_BATCH = 1000
_retention = timedelta(days=14)


def configure_retention(days: int) -> None:
    global _retention
    _retention = timedelta(days=days)


@sweep("jobs.purge_finished", every=timedelta(hours=1))
async def purge_finished_jobs(session: AsyncSession) -> int:
    count = await purge_finished(session, older_than=_retention, limit=PURGE_BATCH)
    if count == PURGE_BATCH:
        log.info("sweep_capped", extra={"sweep": "jobs.purge_finished", "limit": PURGE_BATCH})
    return count
