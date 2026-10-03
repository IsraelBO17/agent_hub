"""Wire models for auth and /v1/me. They match openapi.yaml; camelCase on the wire."""

import uuid
from datetime import datetime

from pydantic import Field

from app.core.schemas import ApiInput, ApiModel


class GoogleSignIn(ApiInput):
    id_token: str = Field(min_length=1, max_length=8192)


class Preferences(ApiModel):
    default_agent_slug: str | None = None
    reopen_last_session: bool = False


class Me(ApiModel):
    id: uuid.UUID
    email: str
    name: str | None
    avatar_url: str | None
    preferences: Preferences


class AccessToken(ApiModel):
    access_token: str
    expires_at: datetime


class SignedIn(AccessToken):
    user: Me
