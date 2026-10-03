"""Wire models for /v1/agents. They match openapi.yaml's Agent; camelCase on the wire."""

import uuid
from datetime import datetime

from app.core.schemas import ApiModel
from app.features.agents.descriptor import AgentCapabilities, AgentDetails, AgentTool, Starter


class MyStats(ApiModel):
    session_count: int
    last_active_at: datetime | None


class AgentOut(ApiModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str
    tagline: str | None
    greeting: str | None
    icon: str
    color: str
    stage: str
    status: str
    status_changed_at: datetime | None
    framework: str | None
    runtime_type: str
    version: str | None
    deployed_at: datetime | None
    details: AgentDetails
    disclaimer: str | None
    capabilities: AgentCapabilities
    tools: list[AgentTool]
    starters: list[Starter]
    retired_at: datetime | None
    my_stats: MyStats


class AgentList(ApiModel):
    items: list[AgentOut]
