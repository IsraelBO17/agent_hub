"""Alembic environment. Synchronous: `create_engine("postgresql+psycopg://…")` uses psycopg's sync
driver on the same URL the app uses asynchronously. Migrations use the DIRECT URL (never through a
transaction-mode pooler) (standard §11.1)."""

import importlib
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.db import Base
from app.core.settings import get_settings

# Every module that defines tables, so autogenerate sees them. Add each new feature's models here.
MODEL_MODULES = [
    "app.core.jobs.models",
    "app.db.models",  # every Agent Hub table until each feature moves its tables into its package
    "app.features.auth.models",
]
for module in MODEL_MODULES:
    importlib.import_module(module)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().migrations_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_settings().migrations_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        # compare_server_default: `alembic check` also catches a changed server_default.
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_server_default=True
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
