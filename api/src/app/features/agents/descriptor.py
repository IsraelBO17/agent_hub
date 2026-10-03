"""The agent descriptor: one YAML file per agent in `agents/` (D6, F02, AGENT_PROFILE).

The descriptor's names are the contract's (camelCase), and its nested objects are stored as-is in
the `agents` JSONB columns, so what `GET /v1/agents` returns is what the descriptor said. Unknown
keys are rejected, so a typo fails at `hub agents add` instead of hiding a capability.
"""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import Field, model_validator

from app.core.schemas import ApiInput

SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"  # the contract's AgentSlug; also lucide icon names
RUNTIME_ARN = r"^arn:aws:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:runtime/[A-Za-z0-9_-]+$"
MAX_FILE_BYTES = 20 * 1024 * 1024  # D23

UploadContentType = Literal[
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "text/csv",
    "text/plain",
]


def _is_none(value: object) -> bool:
    """For optional contract properties: left out of the JSON, never sent as null."""
    return value is None


class AgentDetails(ApiInput):
    """Display-only facts for the agent detail page."""

    model: str | None = Field(default=None, exclude_if=_is_none)
    region: str | None = Field(default=None, exclude_if=_is_none)
    framework_version: str | None = Field(default=None, exclude_if=_is_none)
    runtime_label: str | None = Field(default=None, exclude_if=_is_none)


class AttachmentLimits(ApiInput):
    enabled: bool
    content_types: list[UploadContentType]
    max_file_bytes: int = Field(ge=0, le=MAX_FILE_BYTES)
    max_files: int = Field(ge=0, le=10)


class AgentCapabilities(ApiInput):
    attachments: AttachmentLimits
    artifacts: bool
    approvals: bool
    questions: bool


class AgentTool(ApiInput):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500)
    requires_approval: bool


class Starter(ApiInput):
    title: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, exclude_if=_is_none)
    prompt: str = Field(min_length=1, max_length=2000)


class AgentDescriptor(ApiInput):
    slug: str = Field(pattern=SLUG, max_length=64)
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    tagline: str | None = Field(default=None, max_length=120)
    greeting: str | None = Field(default=None, max_length=120)
    icon: str = Field(pattern=SLUG, max_length=64)  # lucide
    color: Literal["red", "blue", "green", "purple", "amber", "grey"]
    stage: Literal["beta", "stable"] = "stable"
    visibility: Literal["listed", "hidden"] = "listed"  # hidden: the Scenario Agent
    sort_order: int = 0  # catalog order, then name
    version: str | None = Field(default=None, max_length=40)
    framework: str | None = Field(default=None, max_length=40)
    runtime_type: Literal["agentcore", "http"]
    runtime_arn: str | None = Field(default=None, pattern=RUNTIME_ARN)
    runtime_qualifier: str | None = Field(default=None, max_length=100)  # AgentCore endpoint
    runtime_endpoint: str | None = Field(default=None, pattern=r"^https://[^\x00-\x20]+$")
    details: AgentDetails = AgentDetails()
    disclaimer: str | None = Field(default=None, max_length=300)
    capabilities: AgentCapabilities
    tools: list[AgentTool] = Field(default_factory=list)
    starters: list[Starter] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.runtime_type == "agentcore" and (not self.runtime_arn or self.runtime_endpoint):
            raise ValueError("runtimeType agentcore needs runtimeArn and no runtimeEndpoint")
        if self.runtime_type == "http" and (not self.runtime_endpoint or self.runtime_arn):
            raise ValueError("runtimeType http needs runtimeEndpoint and no runtimeArn")
        names = [t.name for t in self.tools]
        if len(names) != len(set(names)):
            raise ValueError("tool names must be unique")
        if any(t.requires_approval for t in self.tools) and not self.capabilities.approvals:
            raise ValueError("a tool requires approval, so capabilities.approvals must be true")
        return self


def load_descriptor(path: Path) -> AgentDescriptor:
    """Raises OSError, yaml.YAMLError or pydantic.ValidationError; the CLI reports them."""
    return AgentDescriptor.model_validate(yaml.safe_load(path.read_text()))
