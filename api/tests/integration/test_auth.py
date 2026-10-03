"""Auth end to end (SPEC.md, feature: auth): each rejection and effect of the capability blocks."""

import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import issue_access_token
from app.core.settings import get_settings
from app.features.auth.models import RefreshToken, User
from app.features.auth.router import get_google_verifier
from tests.support.google import FakeGoogle

ORIGIN = {"Origin": "http://localhost:5173"}  # APP_ORIGIN in .env.example


@pytest.fixture
def google(fastapi_app: FastAPI, client: httpx.AsyncClient) -> Iterator[FakeGoogle]:
    fake = FakeGoogle()
    verifier = fake.verifier()
    fastapi_app.dependency_overrides[get_google_verifier] = lambda: verifier
    yield fake  # the client fixture clears every override afterwards


@pytest.fixture
async def invited(session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="Owner@Example.com", status="invited")
    session.add(user)
    await session.commit()  # a savepoint in the test's transaction
    yield user


def refresh_cookie(response: httpx.Response) -> str:
    header = response.headers["set-cookie"]
    return header.split(";", 1)[0].removeprefix("ah_refresh=")


def with_cookie(token: str) -> dict[str, str]:
    return {**ORIGIN, "Cookie": f"ah_refresh={token}"}


async def sign_in(client: httpx.AsyncClient, google: FakeGoogle, **claims: str) -> httpx.Response:
    return await client.post(
        "/v1/auth/google", json={"idToken": google.id_token(**claims)}, headers=ORIGIN
    )


# ---- sign in


async def test_invited_user_signs_in_and_is_activated(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User, session: AsyncSession
) -> None:
    r = await sign_in(client, google, email="owner@example.com", sub="sub-owner")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"accessToken", "expiresAt", "user"}
    assert body["user"]["email"] == "Owner@Example.com"
    assert body["user"]["preferences"] == {"defaultAgentSlug": None, "reopenLastSession": False}
    await session.refresh(invited)
    assert (invited.status, invited.google_sub, invited.name) == (
        "active",
        "sub-owner",
        "Ada Owner",
    )


async def test_refresh_cookie_attributes(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User
) -> None:
    cookie = (await sign_in(client, google)).headers["set-cookie"].lower()
    for part in ("httponly", "secure", "samesite=strict", "path=/v1/auth", "max-age=2592000"):
        assert part in cookie
    assert "domain=" not in cookie  # host-only (D8, D25)


async def test_later_sign_ins_find_the_user_by_google_sub(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User
) -> None:
    await sign_in(client, google, sub="sub-owner")
    r = await sign_in(client, google, sub="sub-owner", email="renamed@example.com")
    assert r.status_code == 200 and r.json()["user"]["id"] == str(invited.id)


async def test_uninvited_account_is_403_with_its_email(
    client: httpx.AsyncClient, google: FakeGoogle
) -> None:
    r = await sign_in(client, google, email="stranger@example.com")
    assert r.status_code == 403
    assert r.json()["code"] == "not_invited" and r.json()["email"] == "stranger@example.com"


async def test_disabled_account_is_403(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User, session: AsyncSession
) -> None:
    await sign_in(client, google, sub="sub-owner")
    await session.execute(update(User).where(User.id == invited.id).values(status="disabled"))
    await session.commit()
    r = await sign_in(client, google, sub="sub-owner")
    assert r.status_code == 403 and r.json()["code"] == "account_disabled"


async def test_bad_google_token_is_401(client: httpx.AsyncClient, google: FakeGoogle) -> None:
    r = await client.post("/v1/auth/google", json={"idToken": "garbage"}, headers=ORIGIN)
    assert r.status_code == 401 and r.json()["code"] == "invalid_google_token"


async def test_google_down_is_503(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User
) -> None:
    google.down = True
    r = await sign_in(client, google)
    assert r.status_code == 503 and r.json()["code"] == "identity_provider_unavailable"
    assert r.headers["retry-after"] == "5"


@pytest.mark.parametrize(
    "headers", [{}, {"Origin": "https://evil.example"}], ids=["missing", "foreign"]
)
@pytest.mark.parametrize("path", ["/v1/auth/google", "/v1/auth/refresh", "/v1/auth/logout"])
async def test_origin_is_required_on_every_auth_endpoint(
    client: httpx.AsyncClient, google: FakeGoogle, path: str, headers: dict[str, str]
) -> None:
    r = await client.post(path, json={"idToken": "x"}, headers=headers)
    assert r.status_code == 403 and r.json()["code"] == "origin_not_allowed"


# ---- refresh


async def test_refresh_rotates_the_cookie(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User
) -> None:
    first = refresh_cookie(await sign_in(client, google))
    r = await client.post("/v1/auth/refresh", headers=with_cookie(first))
    assert r.status_code == 200 and set(r.json()) == {"accessToken", "expiresAt"}
    second = refresh_cookie(r)
    assert second != first
    r = await client.post("/v1/auth/refresh", headers=with_cookie(second))
    assert r.status_code == 200


async def test_reusing_a_rotated_token_signs_the_family_out(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User, session: AsyncSession
) -> None:
    first = refresh_cookie(await sign_in(client, google))
    second = refresh_cookie(await client.post("/v1/auth/refresh", headers=with_cookie(first)))
    r = await client.post("/v1/auth/refresh", headers=with_cookie(first))  # reuse
    assert r.status_code == 401 and r.json()["code"] == "session_expired"
    r = await client.post("/v1/auth/refresh", headers=with_cookie(second))  # the family is gone
    assert r.status_code == 401 and r.json()["code"] == "session_expired"
    revoked = (await session.scalars(select(RefreshToken.revoked_at))).all()
    assert revoked and all(revoked)  # the revocation committed despite the error


async def test_refresh_without_or_with_unknown_cookie_is_401(client: httpx.AsyncClient) -> None:
    for headers in (ORIGIN, with_cookie("not-a-token")):
        r = await client.post("/v1/auth/refresh", headers=headers)
        assert r.status_code == 401 and r.json()["code"] == "session_expired"


async def test_expired_refresh_token_is_401(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User, session: AsyncSession
) -> None:
    token = refresh_cookie(await sign_in(client, google))
    await session.execute(
        update(RefreshToken).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    )
    await session.commit()
    r = await client.post("/v1/auth/refresh", headers=with_cookie(token))
    assert r.status_code == 401 and r.json()["code"] == "session_expired"


async def test_refresh_for_a_disabled_user_is_403_and_signs_out(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User, session: AsyncSession
) -> None:
    token = refresh_cookie(await sign_in(client, google))
    await session.execute(update(User).where(User.id == invited.id).values(status="disabled"))
    await session.commit()
    r = await client.post("/v1/auth/refresh", headers=with_cookie(token))
    assert r.status_code == 403 and r.json()["code"] == "account_disabled"
    assert all((await session.scalars(select(RefreshToken.revoked_at))).all())


# ---- sign out


async def test_logout_revokes_and_clears_the_cookie(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User
) -> None:
    token = refresh_cookie(await sign_in(client, google))
    r = await client.post("/v1/auth/logout", headers=with_cookie(token))
    assert r.status_code == 204
    cleared = r.headers["set-cookie"].lower()
    assert "ah_refresh=" in cleared and "max-age=0" in cleared and "path=/v1/auth" in cleared
    r = await client.post("/v1/auth/refresh", headers=with_cookie(token))
    assert r.status_code == 401


async def test_logout_without_a_cookie_is_still_204(client: httpx.AsyncClient) -> None:
    assert (await client.post("/v1/auth/logout", headers=ORIGIN)).status_code == 204
    assert (await client.post("/v1/auth/logout", headers=with_cookie("unknown"))).status_code == 204


# ---- /v1/me


async def test_me_returns_the_signed_in_user(
    client: httpx.AsyncClient, google: FakeGoogle, invited: User
) -> None:
    access = (await sign_in(client, google)).json()["accessToken"]
    r = await client.get("/v1/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200 and r.json()["id"] == str(invited.id)


async def test_me_with_an_expired_token_is_token_expired(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "access_token_ttl_seconds", -1)
    token = issue_access_token(get_settings(), uuid.uuid4())
    r = await client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert (
        r.status_code == 401
        and r.json()["code"] == "token_expired"
        and r.json()["retryable"] is True
    )


async def test_me_for_an_unknown_user_is_token_invalid(client: httpx.AsyncClient) -> None:
    token = issue_access_token(get_settings(), uuid.uuid4())
    r = await client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401 and r.json()["code"] == "token_invalid"
