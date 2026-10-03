"""Verifies Google ID tokens without blocking the event loop (D8; recipe 4).

One `httpx.AsyncClient` (created in the lifespan) fetches Google's signing keys; they are cached for
Google's `Cache-Control: max-age`, and refetched at most once a minute when a token names a key we
don't have (Google rotates keys). The algorithm is pinned to RS256.
"""

import asyncio
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from jwt import PyJWK, PyJWKSet

from app.features.auth.exceptions import IdentityProviderUnavailable, InvalidGoogleToken

_ALGORITHM = "RS256"
_REFETCH_AFTER_SECONDS = 60
_MAX_AGE = re.compile(r"max-age=(\d+)")


@dataclass(frozen=True)
class GoogleIdentity:
    sub: str
    email: str
    name: str | None
    picture: str | None


class GoogleVerifier:
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        certs_url: str,
        client_id: str,
        issuers: list[str],
        cache_seconds: int,
    ) -> None:
        self._client = client
        self._certs_url = certs_url
        self._client_id = client_id
        self._issuers = issuers
        self._cache_seconds = cache_seconds
        self._keys: dict[str, PyJWK] = {}
        self._expires = 0.0
        self._fetched = 0.0
        self._lock = asyncio.Lock()

    async def verify(self, id_token: str) -> GoogleIdentity:
        try:
            header = jwt.get_unverified_header(id_token)
        except jwt.PyJWTError as exc:
            raise InvalidGoogleToken() from exc
        kid = header.get("kid")
        if header.get("alg") != _ALGORITHM or not isinstance(kid, str):
            raise InvalidGoogleToken()
        key = await self._key(kid)
        try:
            claims: dict[str, Any] = jwt.decode(
                id_token,
                key,
                algorithms=[_ALGORITHM],
                audience=self._client_id,
                issuer=self._issuers,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidGoogleToken() from exc
        email = claims.get("email")
        if not isinstance(email, str) or claims.get("email_verified") not in (True, "true"):
            raise InvalidGoogleToken("Google says this email isn't verified.")
        return GoogleIdentity(
            sub=str(claims["sub"]),
            email=email,
            name=claims.get("name"),
            picture=claims.get("picture"),
        )

    async def _key(self, kid: str) -> PyJWK:
        now = time.monotonic()
        if kid in self._keys and now < self._expires:
            return self._keys[kid]
        async with self._lock:
            now = time.monotonic()
            stale = now >= self._expires
            unknown = kid not in self._keys and now - self._fetched >= _REFETCH_AFTER_SECONDS
            if stale or unknown:
                await self._fetch()
        if kid not in self._keys:
            raise InvalidGoogleToken()
        return self._keys[kid]

    async def _fetch(self) -> None:
        try:
            response = await self._client.get(self._certs_url)
            response.raise_for_status()
            key_set = PyJWKSet.from_dict(response.json())
        except (httpx.HTTPError, ValueError, jwt.PyJWTError) as exc:
            raise IdentityProviderUnavailable(retry_after=5) from exc
        match = _MAX_AGE.search(response.headers.get("cache-control", ""))
        max_age = int(match.group(1)) if match else self._cache_seconds
        now = time.monotonic()
        self._keys = {k.key_id: k for k in key_set.keys if k.key_id}
        self._fetched = now
        self._expires = now + max_age
