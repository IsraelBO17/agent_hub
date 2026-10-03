"""Database engine, sessions and the declarative Base (standard §11).

The engine is created in the lifespan (`init_db`) and disposed on shutdown. One AsyncSession per
request (`SessionDep`). Only services commit.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Annotated, Any, ClassVar

from fastapi import Depends
from sqlalchemy import MetaData, event
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import Settings

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map: ClassVar[dict[Any, Any]] = {
        dict[str, Any]: JSONB,
        list[Any]: JSONB,
        datetime: TIMESTAMP(timezone=True),
        uuid.UUID: UUID(as_uuid=True),
    }


def make_engine(settings: Settings) -> AsyncEngine:
    connect_args: dict[str, Any] = {"connect_timeout": 10}
    if not settings.db_prepared_statements:
        # psycopg: no server-side prepared statements. Safe behind any transaction-mode pooler.
        connect_args["prepare_threshold"] = None
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=10,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=connect_args,
    )
    timeout = int(settings.db_statement_timeout_ms)

    @event.listens_for(engine.sync_engine, "begin")
    def _statement_timeout(conn: Connection) -> None:
        # Transaction-scoped, so it works through a transaction-mode pooler (which rejects the
        # `options` startup parameter). The event also fires on autobegin.
        conn.exec_driver_sql(f"SET LOCAL statement_timeout = {timeout}")

    return engine


def constraint_name(exc: IntegrityError) -> str | None:
    """The violated constraint's name, so a service can map each constraint to its own typed error
    (names are stable: they come from NAMING_CONVENTION or the model's explicit Index name)."""
    diag = getattr(exc.orig, "diag", None)
    name = getattr(diag, "constraint_name", None)
    return name if isinstance(name, str) else None


class Database:
    def __init__(self, settings: Settings) -> None:
        self.engine = make_engine(settings)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)


_db: Database | None = None


def init_db(settings: Settings) -> Database:
    global _db
    _db = Database(settings)
    return _db


def get_db() -> Database:
    if _db is None:
        raise RuntimeError("init_db() runs in the lifespan")
    return _db


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_db().sessions() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
