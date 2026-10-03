"""The Google ID-token verifier (D8): every check, against a stubbed key set."""

import time
from typing import Any

import jwt
import pytest

from app.features.auth.exceptions import IdentityProviderUnavailable, InvalidGoogleToken
from tests.support.google import FakeGoogle


async def test_valid_token_gives_the_identity() -> None:
    google = FakeGoogle()
    identity = await google.verifier().verify(google.id_token(sub="s1", email="a@b.dev"))
    assert (identity.sub, identity.email, identity.name) == ("s1", "a@b.dev", "Ada Owner")


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": int(time.time()) - 10},
        {"aud": "someone-else.apps.googleusercontent.com"},
        {"iss": "https://evil.example"},
        {"email_verified": False},
    ],
    ids=["expired", "wrong-audience", "wrong-issuer", "unverified-email"],
)
async def test_rejected(overrides: dict[str, Any]) -> None:
    google = FakeGoogle()
    with pytest.raises(InvalidGoogleToken):
        await google.verifier().verify(google.id_token(**overrides))


async def test_signed_by_another_key_is_rejected() -> None:
    google, impostor = FakeGoogle(), FakeGoogle()
    with pytest.raises(InvalidGoogleToken):
        await google.verifier().verify(impostor.id_token())  # same kid, different key


async def test_alg_none_and_garbage_are_rejected() -> None:
    google = FakeGoogle()
    unsigned = jwt.encode({"sub": "x"}, key="", algorithm="none", headers={"kid": google.kid})
    for token in (unsigned, "not-a-jwt"):
        with pytest.raises(InvalidGoogleToken):
            await google.verifier().verify(token)


async def test_keys_are_cached_and_unknown_kid_refetches_at_most_once_a_minute() -> None:
    google = FakeGoogle()
    verifier = google.verifier()
    await verifier.verify(google.id_token())
    await verifier.verify(google.id_token())
    assert google.fetches == 1
    with pytest.raises(InvalidGoogleToken):
        await verifier.verify(google.id_token(kid="rotated-away"))
    with pytest.raises(InvalidGoogleToken):
        await verifier.verify(google.id_token(kid="rotated-away"))
    assert google.fetches == 1  # within the minute: no refetch storm from bad tokens


async def test_google_down_is_503_not_401() -> None:
    google = FakeGoogle(down=True)
    with pytest.raises(IdentityProviderUnavailable):
        await google.verifier().verify(google.id_token())
