"""Connection settings the standard relies on (§11.3)."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import get_settings


async def test_statement_timeout_set_per_transaction(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with sessions() as s:
        value = await s.scalar(text("SHOW statement_timeout"))
    assert value == f"{get_settings().db_statement_timeout_ms // 1000}s"


async def test_prepared_statements_off_by_default(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with sessions() as s:
        raw = await (await s.connection()).get_raw_connection()
        assert raw.driver_connection.prepare_threshold is None  # type: ignore[union-attr]
