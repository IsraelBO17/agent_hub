"""D3: does psycopg 3 work through Neon's pooler (PgBouncer, transaction mode)?

Skipped unless POOLER_TEST_URL is set to a **pooled** Neon connection string (host ending in
`-pooler`). It never writes: every statement is a read. Run it on purpose:

    POOLER_TEST_URL='postgresql://…-pooler…/neondb?sslmode=require' uv run pytest \
        tests/integration/test_neon_pooler.py -v

What it shows:
- with server-side prepared statements forced on (`prepare_threshold=0`), many concurrent sessions
  repeating parameterised queries succeed, so PgBouncer's protocol-level prepared statements work;
- with them off (`prepare_threshold=None`, the profile's default) the same load succeeds;
- `SET LOCAL statement_timeout` from the engine's `begin` event is applied through the pooler: a
  query longer than the timeout is cancelled.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from typing import Any

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.db import make_engine
from app.core.settings import Settings, get_settings

URL = os.environ.get("POOLER_TEST_URL", "")
pytestmark = pytest.mark.skipif(not URL, reason="POOLER_TEST_URL not set (a pooled Neon URL)")

SESSIONS = 24  # well above the app's pool, so client connections share PgBouncer's servers
ROUNDS = 12  # above psycopg's default prepare threshold (5)
QUERIES = [
    "SELECT CAST(:n AS int) + 1",
    "SELECT md5(CAST(:s AS text))",
    "SELECT count(*) FROM generate_series(1, CAST(:n AS int))",
    "SELECT current_setting('statement_timeout')",
]


def _engine(*, prepared: bool, timeout_ms: int | None = None) -> AsyncEngine:
    # One client connection per concurrent session: PgBouncer then multiplexes them onto fewer
    # server connections, which is where unsupported prepared statements would break.
    update: dict[str, Any] = {
        "database_url": URL,
        "db_prepared_statements": prepared,
        "db_pool_size": SESSIONS,
        "db_max_overflow": 0,
    }
    if timeout_ms is not None:
        update["db_statement_timeout_ms"] = timeout_ms
    settings = Settings.model_validate({**get_settings().model_dump(by_alias=True), **update})
    eng = make_engine(settings)
    if prepared:
        # Prepare every statement on first use, so the test can't pass by never preparing.
        @event.listens_for(eng.sync_engine, "connect")
        def _always_prepare(dbapi_conn: Any, _: Any) -> None:
            dbapi_conn.driver_connection.prepare_threshold = 0

    return eng


@pytest.fixture(params=[True, False], ids=["prepared-on", "prepared-off"])
async def engine(request: pytest.FixtureRequest) -> AsyncIterator[AsyncEngine]:
    eng = _engine(prepared=request.param)
    yield eng
    await eng.dispose()


async def _client(eng: AsyncEngine, n: int) -> None:
    # Stagger the first connection: two dozen TLS handshakes at the same instant can time out on a
    # slow link, which says nothing about prepared statements. The sessions still overlap.
    await asyncio.sleep(n * 0.25)
    for round_ in range(ROUNDS):
        async with eng.connect() as conn:  # one transaction per round, as a request would
            for sql in QUERIES:
                await conn.execute(text(sql), {"n": n + round_, "s": f"{n}-{round_}"})


async def test_concurrent_parameterised_queries(engine: AsyncEngine) -> None:
    await asyncio.gather(*(_client(engine, n) for n in range(SESSIONS)))


async def test_statement_timeout_applies_through_the_pooler() -> None:
    eng = _engine(prepared=False, timeout_ms=500)
    try:
        async with eng.connect() as conn:
            assert await conn.scalar(text("SHOW statement_timeout")) == "500ms"
        with pytest.raises(DBAPIError, match="statement timeout"):
            async with eng.connect() as conn:
                await conn.execute(text("SELECT pg_sleep(2)"))
    finally:
        await eng.dispose()
