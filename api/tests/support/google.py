"""A stand-in for Google: an RSA key, its key set served by httpx.MockTransport, and ID tokens
signed with it. No test ever calls Google."""

import base64
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from app.features.auth.google import GoogleVerifier

CLIENT_ID = "test-client.apps.googleusercontent.com"
ISSUER = "https://accounts.google.com"
KID = "test-key-1"


def _b64(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


@dataclass
class FakeGoogle:
    key: rsa.RSAPrivateKey = field(
        default_factory=lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048)
    )
    kid: str = KID
    down: bool = False
    fetches: int = 0

    def jwks(self) -> dict[str, Any]:
        pub = self.key.public_key().public_numbers()
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "alg": "RS256",
                    "use": "sig",
                    "kid": self.kid,
                    "n": _b64(pub.n),
                    "e": _b64(pub.e),
                }
            ]
        }

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.fetches += 1
        if self.down:
            return httpx.Response(503)
        return httpx.Response(200, json=self.jwks(), headers={"cache-control": "max-age=3600"})

    def verifier(self) -> GoogleVerifier:
        client = httpx.AsyncClient(transport=httpx.MockTransport(self.handler))
        return GoogleVerifier(
            client,
            certs_url="https://www.googleapis.com/oauth2/v3/certs",
            client_id=CLIENT_ID,
            issuers=[ISSUER, "accounts.google.com"],
            cache_seconds=3600,
        )

    def id_token(
        self,
        *,
        sub: str = "google-sub-1",
        email: str = "owner@example.com",
        kid: str | None = None,
        **overrides: Any,
    ) -> str:
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": ISSUER,
            "aud": CLIENT_ID,
            "sub": sub,
            "email": email,
            "email_verified": True,
            "name": "Ada Owner",
            "picture": "https://lh3.googleusercontent.com/a/x",
            "iat": now,
            "exp": now + 600,
            **overrides,
        }
        return jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": kid or self.kid})
