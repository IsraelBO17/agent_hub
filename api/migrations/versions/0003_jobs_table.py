"""Jobs table: the background-work ledger from the API standard (§13).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-03 00:59:36.540380
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Text(), server_default="queued", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False),
        sa.Column(
            "run_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("locked_until", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'dead')",
            name=op.f("ck_jobs_status"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
    )
    op.create_index(
        "ix_jobs_due",
        "jobs",
        ["run_at"],
        unique=False,
        postgresql_where=sa.text("status IN ('queued', 'failed')"),
    )
    op.create_index(
        "ix_jobs_running_lease",
        "jobs",
        ["locked_until"],
        unique=False,
        postgresql_where=sa.text("status = 'running'"),
    )
    op.create_index(
        "uq_jobs_type_idempotency_key",
        "jobs",
        ["type", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_jobs_type_idempotency_key",
        table_name="jobs",
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.drop_index(
        "ix_jobs_running_lease", table_name="jobs", postgresql_where=sa.text("status = 'running'")
    )
    op.drop_index(
        "ix_jobs_due", table_name="jobs", postgresql_where=sa.text("status IN ('queued', 'failed')")
    )
    op.drop_table("jobs")
