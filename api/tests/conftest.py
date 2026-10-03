"""Shared fixtures. Integration and contract tests need a real Postgres (`make db-up`); unit tests
need nothing. The local database is wiped and migrated once per run: never point it elsewhere."""

import os

# Required settings come from .env.example (core/settings.py). Tests always run as local.
os.environ["APP_ENV"] = "local"

import uuid
from collections.abc import AsyncIterator, Callable

import httpx
import pytest
from alembic import command
from alembic.config import Config
from asgi_lifespan import LifespanManager
from fastapi import APIRouter, FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth import CurrentUser, issue_access_token
from app.core.db import get_db, get_session
from app.core.schemas import ApiInput
from app.core.settings import get_settings
from app.main import create_app

AuthHeaders = Callable[[uuid.UUID | None], dict[str, str]]


def _reset_database() -> None:
    url = get_settings().migrations_url
    if "localhost" not in url and "127.0.0.1" not in url:
        raise RuntimeError("tests wipe the database: point DATABASE_URL at a local one")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    engine.dispose()
    command.upgrade(Config("alembic.ini"), "head")


class _Echo(ApiInput):
    text: str
    max_words: int | None = None  # "maxWords" on the wire


_probe = APIRouter(prefix="/v1/_test")


@_probe.post("/echo")
async def _echo(body: _Echo, user: CurrentUser) -> dict[str, str]:
    """Test-only: an authenticated endpoint with a body, for core HTTP tests (auth, limits,
    validation) that must not depend on any feature. Not part of the contract."""
    return {"text": body.text, "userId": str(user.user_id)}


@pytest.fixture(scope="session")
def fastapi_app() -> FastAPI:
    _reset_database()
    app = create_app()
    app.include_router(_probe)
    return app


@pytest.fixture(scope="session")
async def app(fastapi_app: FastAPI) -> AsyncIterator[object]:
    """The app with its lifespan running (httpx's ASGITransport doesn't run it)."""
    async with LifespanManager(fastapi_app) as manager:
        yield manager.app


@pytest.fixture
def sessions(app: object) -> async_sessionmaker[AsyncSession]:
    """Real sessions that commit. Tests using them clean up what they create."""
    return get_db().sessions


@pytest.fixture
async def session(app: object) -> AsyncIterator[AsyncSession]:
    """One session inside an outer transaction that is rolled back after the test. Services'
    commits become savepoints, so nothing a test writes survives it.

    Two traps: (1) setup writes made directly on this session are undone if the code under test
    rolls back, so `await session.commit()` after setup (it commits only a savepoint); (2) every
    row gets the same `created_at` (now() is the transaction's start), so tests of ordering set
    `created_at` explicitly."""
    async with get_db().engine.connect() as conn:
        outer = await conn.begin()
        s = AsyncSession(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        try:
            yield s
        finally:
            await s.close()
            await outer.rollback()


@pytest.fixture
async def client(
    app: object, fastapi_app: FastAPI, session: AsyncSession
) -> AsyncIterator[httpx.AsyncClient]:
    """An HTTP client on the in-process app whose requests all use the rolled-back session."""

    async def _session() -> AsyncIterator[AsyncSession]:
        yield session

    fastapi_app.dependency_overrides[get_session] = _session
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def auth() -> AuthHeaders:
    """Headers for a signed-in user: auth() for a new user, auth(user_id) for a given one."""

    def headers(user_id: uuid.UUID | None = None) -> dict[str, str]:
        token = issue_access_token(get_settings(), user_id or uuid.uuid4())
        return {"Authorization": f"Bearer {token}"}

    return headers
