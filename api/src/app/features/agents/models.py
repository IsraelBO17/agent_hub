"""The agent registry (D6): global configuration, not user-owned.

Only this feature writes `agents`, through the operator's `hub agents add` (no HTTP write in v1).
Sessions point at `agents.id` with ON DELETE RESTRICT, so an agent with sessions is retired, never
deleted.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.db.models import created_at, one_of, pk, updated_at

AGENT_COLORS = ("red", "blue", "green", "purple", "amber", "grey")
AGENT_STAGES = ("beta", "stable")
AGENT_STATUSES = ("online", "degraded", "offline")
RUNTIME_TYPES = ("agentcore", "http")
AGENT_VISIBILITY = ("listed", "hidden")


class Agent(Base):
    """The agent registry (D6). Global configuration, not user-owned."""

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = pk()
    slug: Mapped[str] = mapped_column(Text, unique=True)  # used in URLs: /agents/:slug
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    tagline: Mapped[str | None] = mapped_column(Text)  # short description for the mobile catalog
    greeting: Mapped[str | None] = mapped_column(
        Text
    )  # new-session heading, e.g. "What are we building today?"
    icon: Mapped[str] = mapped_column(Text)  # lucide icon name
    color: Mapped[str] = mapped_column(Text)
    stage: Mapped[str] = mapped_column(Text, server_default="stable")
    status: Mapped[str] = mapped_column(Text, server_default="online")
    status_checked_at: Mapped[datetime | None]
    status_changed_at: Mapped[datetime | None]  # "Offline since …", "last seen …"
    visibility: Mapped[str] = mapped_column(Text, server_default="listed")
    runtime_type: Mapped[str] = mapped_column(Text)
    runtime_arn: Mapped[str | None] = mapped_column(Text)  # AgentCore runtime ARN
    runtime_qualifier: Mapped[str | None] = mapped_column(
        Text
    )  # AgentCore endpoint name, e.g. DEFAULT
    runtime_endpoint: Mapped[str | None] = mapped_column(Text)  # URL for runtime_type = http
    framework: Mapped[str | None] = mapped_column(Text)  # display only: strands, langgraph
    version: Mapped[str | None] = mapped_column(
        Text
    )  # deployed version, shown as "Agent updated to vN"
    deployed_at: Mapped[datetime | None]
    details: Mapped[dict[str, Any]] = mapped_column(
        server_default=text("'{}'::jsonb")
    )  # display only: model, region, framework version
    disclaimer: Mapped[str | None] = mapped_column(Text)
    capabilities: Mapped[dict[str, Any]] = mapped_column(server_default=text("'{}'::jsonb"))
    tools: Mapped[list[Any]] = mapped_column(server_default=text("'[]'::jsonb"))
    starters: Mapped[list[Any]] = mapped_column(server_default=text("'[]'::jsonb"))
    settings: Mapped[dict[str, Any]] = mapped_column(
        server_default=text("'{}'::jsonb")
    )  # history budget, run cap, memory
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    retired_at: Mapped[datetime | None]  # removed from the catalog; its sessions stay readable
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    __table_args__ = (
        one_of("color", AGENT_COLORS),
        one_of("stage", AGENT_STAGES),
        one_of("status", AGENT_STATUSES),
        one_of("visibility", AGENT_VISIBILITY),
        one_of("runtime_type", RUNTIME_TYPES),
        CheckConstraint(
            "(runtime_type = 'agentcore' AND runtime_arn IS NOT NULL)"
            " OR (runtime_type = 'http' AND runtime_endpoint IS NOT NULL)",
            name="runtime_target",
        ),
    )
