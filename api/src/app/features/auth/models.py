"""Tables owned by the auth feature: users and their refresh tokens (D8, D9).

Only this feature writes them. Other tables point at `users.id` (every user-owned row has `user_id`);
other features learn who is signed in from the access token (`CurrentUser`), not from these tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, Index, LargeBinary, Text, func, text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.db.models import created_at, one_of, pk, updated_at, user_fk

USER_STATUSES = ("invited", "active", "disabled")


class User(Base):
    """A person who can sign in. Keyed by Google `sub` (D9)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = pk()
    google_sub: Mapped[str | None] = mapped_column(
        Text, unique=True
    )  # null until an invite is accepted
    email: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="invited")
    preferences: Mapped[dict[str, Any]] = mapped_column(
        server_default=text("'{}'::jsonb")
    )  # defaultAgentSlug, reopenLastSession
    invited_at: Mapped[datetime | None]
    last_login_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    __table_args__ = (
        one_of("status", USER_STATUSES),
        CheckConstraint("status = 'invited' OR google_sub IS NOT NULL", name="active_has_sub"),
        Index("uq_users_email_lower", func.lower(text("email")), unique=True),
    )


class RefreshToken(Base):
    """Rotating refresh tokens, stored as SHA-256 hashes (D8)."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = pk()
    user_id: Mapped[uuid.UUID] = user_fk()
    family_id: Mapped[
        uuid.UUID
    ]  # all rotations of one sign-in share a family; reuse revokes the family
    token_hash: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    expires_at: Mapped[datetime]
    rotated_at: Mapped[datetime | None]  # set when exchanged for a new token
    revoked_at: Mapped[datetime | None]
    user_agent: Mapped[str | None] = mapped_column(Text)
    ip: Mapped[str | None] = mapped_column(INET)
    created_at: Mapped[datetime] = created_at()

    __table_args__ = (
        Index(None, "user_id"),
        Index(None, "family_id"),
    )
