"""Job handlers and sweeps, registered by name. Handlers live in the feature that owns the work
(`features/<name>/jobs.py`) and are imported by main.py and worker.py so they register."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

Handler = Callable[[AsyncSession, Any], Awaitable[None]]
SweepFn = Callable[[AsyncSession], Awaitable[int]]


@dataclass(frozen=True)
class JobSpec:
    job_type: str
    payload_model: type[BaseModel]
    handler: Handler


@dataclass(frozen=True)
class SweepSpec:
    name: str
    every: timedelta
    fn: SweepFn


HANDLERS: dict[str, JobSpec] = {}
SWEEPS: dict[str, SweepSpec] = {}


def job[P: BaseModel](
    type_: str, payload_model: type[P]
) -> Callable[
    [Callable[[AsyncSession, P], Awaitable[None]]], Callable[[AsyncSession, P], Awaitable[None]]
]:
    """Register a handler. It runs in a transaction that also marks the job succeeded, so it must
    flush, not commit. It MUST be idempotent: every job may run more than once."""

    def register(
        fn: Callable[[AsyncSession, P], Awaitable[None]],
    ) -> Callable[[AsyncSession, P], Awaitable[None]]:
        if type_ in HANDLERS:
            raise ValueError(f"job type {type_!r} registered twice")
        HANDLERS[type_] = JobSpec(type_, payload_model, fn)
        return fn

    return register


def sweep(name: str, *, every: timedelta) -> Callable[[SweepFn], SweepFn]:
    """Register periodic work. It must be bounded per run (log when capped) and idempotent."""

    def register(fn: SweepFn) -> SweepFn:
        if name in SWEEPS:
            raise ValueError(f"sweep {name!r} registered twice")
        SWEEPS[name] = SweepSpec(name, every, fn)
        return fn

    return register
