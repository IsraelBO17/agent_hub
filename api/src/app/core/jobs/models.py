"""The jobs table, owned by core/jobs. Only core/jobs writes it; features enqueue through `enqueue`."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

JOB_STATUSES = ("queued", "running", "succeeded", "failed", "dead")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    type: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]]
    status: Mapped[str] = mapped_column(Text, server_default="queued")
    attempts: Mapped[int] = mapped_column(server_default="0")
    max_attempts: Mapped[int] = mapped_column(server_default="5")
    run_at: Mapped[datetime] = mapped_column(server_default=func.now())
    locked_until: Mapped[datetime | None]
    last_error: Mapped[dict[str, Any] | None]
    request_id: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'dead')", name="status"
        ),
        Index("ix_jobs_due", "run_at", postgresql_where=text("status IN ('queued', 'failed')")),
        Index("ix_jobs_running_lease", "locked_until", postgresql_where=text("status = 'running'")),
        Index(
            "uq_jobs_type_idempotency_key",
            "type",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )
