"""Wire base models: camelCase JSON, snake_case Python (standard §8), and cursor pagination."""

import base64
import json
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.core.errors import InvalidCursor

MAX_PAGE = 100
DEFAULT_PAGE = 50


class ApiModel(BaseModel):
    """Base for every response model."""

    # `populate_by_name` is discouraged since Pydantic 2.11; the validate_by_* pair replaces it.
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
        from_attributes=True,
    )


class ApiInput(ApiModel):
    """Base for request bodies and query models.

    - Unknown fields are rejected (OWASP API3), and so are the snake_case Python names: only the
      contract's camelCase names are accepted.
    - Strings may not contain NUL: PostgreSQL text can't store it, so it would otherwise be a 500.
    """

    model_config = ConfigDict(extra="forbid", validate_by_name=False, validate_by_alias=True)

    @field_validator("*", mode="before")
    @classmethod
    def _no_nul(cls, value: Any) -> Any:
        if _contains_nul(value):
            raise ValueError("must not contain the NUL character")
        return value


def _contains_nul(value: Any) -> bool:
    if isinstance(value, str):
        return "\x00" in value
    if isinstance(value, dict):
        return any(_contains_nul(k) or _contains_nul(v) for k, v in value.items())
    if isinstance(value, list | tuple):
        return any(_contains_nul(v) for v in value)
    return False


class PageQuery(ApiInput):
    """Query parameters for a list. Unknown parameters are rejected, like unknown body fields.
    Use as `params: Annotated[PageQuery, Query()]`; extend it for a list's own filters."""

    cursor: str | None = Field(default=None, max_length=200)
    limit: int = Field(default=DEFAULT_PAGE, ge=1, le=MAX_PAGE)


class Page[T](ApiModel):
    items: list[T]
    next_cursor: str | None


def encode_cursor(created_at: datetime, row_id: uuid.UUID) -> str:
    """Opaque cursor for lists ordered by (created_at DESC, id DESC)."""
    raw = json.dumps([created_at.isoformat(), str(row_id)]).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        created_at, row_id = json.loads(raw)
        return datetime.fromisoformat(created_at), uuid.UUID(row_id)
    except (ValueError, TypeError) as exc:
        raise InvalidCursor() from exc
