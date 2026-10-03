import time
import uuid

import jwt
import pytest

from app.core.auth import issue_access_token, verify_access_token
from app.core.errors import Unauthenticated
from app.core.settings import get_settings


def test_round_trip() -> None:
    user = uuid.uuid4()
    principal = verify_access_token(
        get_settings(), issue_access_token(get_settings(), user, ("admin",))
    )
    assert principal.user_id == user and principal.roles == {"admin"}


def _token(**overrides: object) -> str:
    s = get_settings()
    now = int(time.time())
    claims: dict[str, object] = {
        "sub": str(uuid.uuid4()),
        "iat": now,
        "exp": now + 60,
        "iss": s.token_issuer,
        "aud": s.token_audience,
        **overrides,
    }
    return jwt.encode(claims, s.session_signing_key.get_secret_value(), "HS256")


@pytest.mark.parametrize(
    "token",
    [
        _token(exp=int(time.time()) - 1),
        _token(aud="someone-else"),
        _token(sub="not-a-uuid"),
        jwt.encode({"sub": str(uuid.uuid4())}, "x" * 40, "HS256"),
        jwt.encode({"sub": str(uuid.uuid4())}, key="", algorithm="none"),
    ],
    ids=["expired", "wrong-audience", "bad-sub", "wrong-key", "alg-none"],
)
def test_rejected(token: str) -> None:
    with pytest.raises(Unauthenticated):
        verify_access_token(get_settings(), token)
