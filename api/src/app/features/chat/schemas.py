"""Wire models for sessions and messages. They match openapi.yaml; camelCase on the wire.

Blocks stay plain dicts in their wire shape (translator.py builds them; openapi.yaml's Block is
the schema, checked in the tests), so what a stream sent is what a reload returns.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.core.schemas import ApiInput, ApiModel

MAX_TEXT = 32_000  # message_too_long above this (checked in the service, for its own code)


class BlockRef(ApiInput):
    message_id: uuid.UUID
    block_id: str = Field(min_length=1, max_length=64)


class AnswerInput(ApiInput):
    question_ref: BlockRef
    option_ids: list[str] | None = Field(default=None, max_length=10)
    text: str | None = Field(default=None, max_length=2000)
    values: dict[str, Any] | None = None


class SendMessageRequest(ApiInput):
    client_message_id: uuid.UUID
    text: str | None = None
    file_ids: list[uuid.UUID] | None = Field(default=None, max_length=10)
    answer: AnswerInput | None = None

    @field_validator("file_ids")
    @classmethod
    def _unique(cls, value: list[uuid.UUID] | None) -> list[uuid.UUID] | None:
        if value is not None and len(set(value)) != len(value):
            raise ValueError("file ids must be unique")
        return value


class MessagePageQuery(ApiInput):
    before: int | None = Field(default=None, ge=1)
    limit: int = Field(default=50, ge=1, le=100)


class AgentRefOut(ApiModel):
    id: uuid.UUID
    slug: str
    name: str
    icon: str
    color: str
    status: str
    stage: str
    retired: bool


class SessionSummaryOut(ApiModel):
    id: uuid.UUID
    agent: AgentRefOut
    title: str
    title_source: str
    created_at: datetime
    last_message_at: datetime
    pinned_at: datetime | None
    archived_at: datetime | None
    is_running: bool
    pending_approvals: int
    message_count: int


class MessageOut(ApiModel):
    id: uuid.UUID
    session_id: uuid.UUID
    seq: int
    role: str
    status: str
    blocks: list[dict[str, Any]]
    client_message_id: uuid.UUID | None
    reply_to_id: uuid.UUID | None
    agent_version: str | None
    error: dict[str, Any] | None
    usage: dict[str, int] | None
    feedback: None = None  # feedback arrives with F20
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class StopAccepted(ApiModel):
    message_id: uuid.UUID
    status: str


class MessagePage(ApiModel):
    items: list[MessageOut]
    next_before: int | None


class SendReplay(ApiModel):
    session: SessionSummaryOut
    user_message: MessageOut
    assistant_message: MessageOut
