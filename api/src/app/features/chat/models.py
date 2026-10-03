"""Tables owned by the chat feature: sessions, their messages, and the agents' tool calls.

Only this feature writes them (standard §7). `messages.blocks` is the transcript; `tool_calls` holds
what is queried or enforced, and a stored tool block only references its row (P6). Design notes:
docs/DATA_MODEL.md.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Computed,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.db.models import created_at, one_of, pk, updated_at, user_fk

TITLE_SOURCES = ("auto", "user")
MESSAGE_ROLES = ("user", "assistant")
MESSAGE_STATUSES = (
    "streaming",
    "awaiting_approval",
    "complete",
    "stopped",
    "failed",
    "interrupted",
)
OPEN_REPLY = "status IN ('streaming', 'awaiting_approval')"
TOOL_CALL_STATUSES = ("running", "awaiting_approval", "succeeded", "failed", "denied", "cancelled")


class Session(Base):
    """A conversation with one agent."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = pk()
    user_id: Mapped[uuid.UUID] = user_fk()
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"))
    title: Mapped[str | None] = mapped_column(Text)
    title_source: Mapped[str | None] = mapped_column(Text)
    last_message_at: Mapped[datetime] = mapped_column(server_default=func.now())
    pinned_at: Mapped[datetime | None]
    archived_at: Mapped[datetime | None]
    deleted_at: Mapped[datetime | None]  # soft delete for the undo window; purged afterwards
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    __table_args__ = (
        one_of("title_source", TITLE_SOURCES),
        UniqueConstraint("id", "user_id"),  # target of composite foreign keys
        # Sidebar: one agent's live sessions, newest first.
        Index(
            "ix_sessions_sidebar",
            "user_id",
            "agent_id",
            text("last_message_at DESC"),
            postgresql_where=text("deleted_at IS NULL AND archived_at IS NULL"),
        ),
        # Catalog "continue where you left off" and ⌘K: live sessions across agents.
        Index(
            "ix_sessions_recent",
            "user_id",
            text("last_message_at DESC"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_sessions_archived",
            "user_id",
            text("archived_at DESC"),
            postgresql_where=text("archived_at IS NOT NULL AND deleted_at IS NULL"),
        ),
        Index("ix_sessions_purge", "deleted_at", postgresql_where=text("deleted_at IS NOT NULL")),
        Index(None, "agent_id"),
    )


class Message(Base):
    """One turn. `blocks` is the ordered transcript content; side tables hold state (P6)."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = pk()
    session_id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID] = user_fk()
    seq: Mapped[int] = mapped_column(Integer)  # order within the session, assigned by the API
    role: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="complete")
    blocks: Mapped[list[Any]] = mapped_column(server_default=text("'[]'::jsonb"))
    client_message_id: Mapped[uuid.UUID | None]  # idempotent sends (user messages)
    reply_to_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE")
    )
    agent_version: Mapped[str | None] = mapped_column(Text)  # agent version that produced the reply
    error: Mapped[dict[str, Any] | None]  # {code, message, retryable}
    usage: Mapped[dict[str, Any] | None]  # tokens, durations
    search_text: Mapped[str | None] = mapped_column(Text)  # plain text flattened from blocks
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', coalesce(search_text, ''))", persisted=True)
    )
    started_at: Mapped[datetime | None]
    heartbeat_at: Mapped[
        datetime | None
    ]  # written by the task running the reply; a stale one means that task died
    cancel_requested_at: Mapped[
        datetime | None
    ]  # Stop; the running task checks it, whichever task received the request
    completed_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    __table_args__ = (
        one_of("role", MESSAGE_ROLES),
        one_of("status", MESSAGE_STATUSES),
        CheckConstraint("jsonb_typeof(blocks) = 'array'", name="blocks_is_array"),
        CheckConstraint("role = 'assistant' OR status = 'complete'", name="user_message_complete"),
        ForeignKeyConstraint(
            ["session_id", "user_id"], ["sessions.id", "sessions.user_id"], ondelete="CASCADE"
        ),
        UniqueConstraint("id", "user_id"),
        # Reload a session in order; also enforces a unique order.
        UniqueConstraint("session_id", "seq"),
        # Per user, not per session: the first send creates the session, so a resend must find it (F03).
        UniqueConstraint("user_id", "client_message_id"),
        # One open reply per session: running or waiting for an approval (run_in_progress, ARCHITECTURE D19).
        Index(
            "uq_messages_open_reply_per_session",
            "session_id",
            unique=True,
            postgresql_where=text(OPEN_REPLY),
        ),
        Index("ix_messages_search", "search_vector", postgresql_using="gin"),
        Index(None, "reply_to_id"),
    )


class ToolCall(Base):
    """A tool the agent ran, with timings and (truncated) input and output."""

    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = pk()
    message_id: Mapped[uuid.UUID]
    session_id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID] = user_fk()
    tool_use_id: Mapped[str] = mapped_column(Text)  # the agent's own id for the call
    name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="running")
    summary: Mapped[str | None] = mapped_column(Text)
    input: Mapped[dict[str, Any] | None]
    output: Mapped[dict[str, Any] | None]
    output_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL")
    )
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None]

    __table_args__ = (
        one_of("status", TOOL_CALL_STATUSES),
        ForeignKeyConstraint(
            ["message_id", "user_id"], ["messages.id", "messages.user_id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["session_id", "user_id"], ["sessions.id", "sessions.user_id"], ondelete="CASCADE"
        ),
        UniqueConstraint("message_id", "tool_use_id"),
        Index(None, "session_id"),
    )
