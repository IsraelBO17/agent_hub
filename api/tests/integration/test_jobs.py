"""The job table, worker and sweeps (standard §13), with real commits and test-only handlers."""

from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
from pydantic import BaseModel
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.context import request_id_var
from app.core.jobs import enqueue, job
from app.core.jobs.models import Job
from app.core.jobs.queue import claim
from app.core.jobs.registry import HANDLERS
from app.core.jobs.runner import purge_finished_jobs, run_due_jobs
from app.core.settings import get_settings

Sessions = async_sessionmaker[AsyncSession]


@pytest.fixture(autouse=True)
async def _clean(sessions: Sessions) -> AsyncIterator[None]:
    async with sessions() as s, s.begin():
        await s.execute(text("TRUNCATE jobs"))
    yield
    async with sessions() as s, s.begin():
        await s.execute(text("TRUNCATE jobs"))


class Boom(BaseModel):
    n: int


@job("test.boom", Boom)
async def _boom(session: AsyncSession, payload: Boom) -> None:
    raise RuntimeError("boom")


class Record(BaseModel):
    n: int


RAN: list[int] = []


@job("test.record", Record)
async def _record(session: AsyncSession, payload: Record) -> None:
    RAN.append(payload.n)


async def test_enqueue_then_run_succeeds_under_the_request_id(sessions: Sessions) -> None:
    RAN.clear()
    token = request_id_var.set("req_from_the_api")
    try:
        async with sessions() as s, s.begin():
            await enqueue(s, "test.record", {"n": 7})
    finally:
        request_id_var.reset(token)
    assert await run_due_jobs(sessions, get_settings()) == 1
    assert RAN == [7]
    async with sessions() as s:
        done = await s.scalar(select(Job))
        assert (
            done is not None
            and done.status == "succeeded"
            and done.request_id == "req_from_the_api"
        )


async def test_rollback_means_no_job(sessions: Sessions) -> None:
    """The outbox: a job enqueued in a transaction that rolls back never exists."""
    async with sessions() as s:
        await s.begin()
        await enqueue(s, "test.record", {"n": 1})
        await s.rollback()
    assert await run_due_jobs(sessions, get_settings()) == 0


async def test_failure_retries_then_dead_letters(sessions: Sessions) -> None:
    async with sessions() as s, s.begin():
        await enqueue(s, "test.boom", {"n": 1}, max_attempts=2)
    await run_due_jobs(sessions, get_settings())
    async with sessions() as s:
        failed = await s.scalar(select(Job))
        assert failed is not None and failed.status == "failed" and failed.attempts == 1
        assert failed.last_error is not None and failed.last_error["code"] == "job_failed"
    async with sessions() as s, s.begin():  # skip the backoff
        await s.execute(update(Job).values(run_at=text("now()")))
    await run_due_jobs(sessions, get_settings())
    async with sessions() as s:
        assert (await s.scalar(select(Job.status))) == "dead"


async def test_unknown_job_type_fails_visibly(sessions: Sessions) -> None:
    async with sessions() as s, s.begin():
        await enqueue(s, "nobody.handles.this", {}, max_attempts=1)
    await run_due_jobs(sessions, get_settings())
    async with sessions() as s:
        assert (await s.scalar(select(Job.status))) == "dead"


async def test_idempotency_key_dedupes_enqueue(sessions: Sessions) -> None:
    async with sessions() as s, s.begin():
        await enqueue(s, "test.boom", {"n": 1}, idempotency_key="k")
        await enqueue(s, "test.boom", {"n": 1}, idempotency_key="k")
    async with sessions() as s:
        assert len((await s.scalars(select(Job))).all()) == 1


async def test_skip_locked_and_expired_lease(sessions: Sessions) -> None:
    async with sessions() as s, s.begin():
        await enqueue(s, "test.boom", {"n": 1})
    async with sessions() as a, sessions() as b, a.begin(), b.begin():
        first = await claim(a, limit=10, lease=timedelta(seconds=30))
        second = await claim(b, limit=10, lease=timedelta(seconds=30))
        assert len(first) == 1 and second == []
    async with sessions() as s, s.begin():  # the worker died; its lease expires
        await s.execute(update(Job).values(locked_until=text("now() - interval '1 second'")))
    async with sessions() as s, s.begin():
        again = await claim(s, limit=10, lease=timedelta(seconds=30))
        assert len(again) == 1 and again[0].attempts == 2


async def test_purge_sweep_removes_only_old_succeeded_jobs(sessions: Sessions) -> None:
    async with sessions() as s, s.begin():
        await enqueue(s, "test.boom", {"n": 1})
        await enqueue(s, "test.boom", {"n": 2})
        await s.execute(
            update(Job)
            .where(Job.payload["n"].as_integer() == 1)
            .values(status="succeeded", updated_at=text("now() - interval '30 days'"))
        )
    async with sessions() as s, s.begin():
        assert await purge_finished_jobs(s) == 1
    async with sessions() as s, s.begin():  # idempotent
        assert await purge_finished_jobs(s) == 0


def test_handlers_registered() -> None:
    assert {"test.record", "test.boom"} <= set(HANDLERS)
