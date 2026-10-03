"""Authentication (standard §12): verify the service's own access token and yield a Principal.

The algorithm is pinned here, never read from the token or a setting. Which identity provider
proves who the user is, and how refresh tokens rotate, is added by the /add-auth recipe.
"""

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Header

from app.core.context import user_id_var
from app.core.errors import Forbidden, TokenExpired, Unauthenticated
from app.core.settings import Settings, get_settings

log = logging.getLogger(__name__)
_ALGORITHM = "HS256"
_REQUIRED = ["sub", "exp", "iat", "iss", "aud"]


@dataclass(frozen=True)
class Principal:
    user_id: uuid.UUID
    roles: frozenset[str]


def issue_access_token(settings: Settings, user_id: uuid.UUID, roles: tuple[str, ...] = ()) -> str:
    now = int(time.time())
    claims = {
        "sub": str(user_id),
        "roles": list(roles),
        "iat": now,
        "exp": now + settings.access_token_ttl_seconds,
        "iss": settings.token_issuer,
        "aud": settings.token_audience,
    }
    return jwt.encode(claims, settings.session_signing_key.get_secret_value(), _ALGORITHM)


def verify_access_token(settings: Settings, token: str) -> Principal:
    try:
        claims = jwt.decode(
            token,
            settings.session_signing_key.get_secret_value(),
            algorithms=[_ALGORITHM],
            audience=settings.token_audience,
            issuer=settings.token_issuer,
            options={"require": _REQUIRED},
        )
        return Principal(uuid.UUID(claims["sub"]), frozenset(claims.get("roles", [])))
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpired() from exc
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        log.info(
            "token_rejected", extra={"reason": type(exc).__name__}
        )  # reason logged, not returned
        raise Unauthenticated() from exc


async def get_principal(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise Unauthenticated()
    principal = verify_access_token(settings, token.strip())
    user_id_var.set(str(principal.user_id))  # request-scoped: each request runs in its own context
    return principal


CurrentUser = Annotated[Principal, Depends(get_principal)]


def require_role(role: str) -> object:
    """A coarse gate for a router or endpoint. Rules about a specific resource live in its service."""

    async def _check(principal: CurrentUser) -> Principal:
        if role not in principal.roles:
            raise Forbidden()
        return principal

    return Depends(_check)
