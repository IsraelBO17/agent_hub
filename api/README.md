# Agent Hub API

FastAPI service (not written yet). Today this folder holds the **database schema and migrations** (build plan step 4) and the **API contract**, [`openapi.yaml`](openapi.yaml) (step 5). Repo layout: root [`README.md`](../README.md).

- Models: `app/db/models.py` (source of truth for the schema). Notes: `docs/DATA_MODEL.md`.
- Migrations: `migrations/` (Alembic). They connect with `DATABASE_URL_DIRECT`, Neon's **direct** (unpooled) connection string, not the pooled one (ARCHITECTURE D3).

## Run locally

Needs [uv](https://docs.astral.sh/uv/) and Docker.

```bash
docker run -d --rm --name agenthub-pg -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=agent_hub -p 55432:5432 postgres:17-alpine
```

```bash
export DATABASE_URL_DIRECT=postgresql://postgres:dev@localhost:55432/agent_hub
```

```bash
uv run alembic upgrade head
```

```bash
uv run pytest
```

The tests drop and recreate the schema, so point them only at a disposable database.

## Changing the schema

1. Edit `app/db/models.py`.
2. `uv run alembic revision --autogenerate -m "what changed"`, then read and fix the generated file (autogenerate misses some things, such as renames).
3. `uv run alembic upgrade head`, `uv run alembic check` (should report no changes) and `uv run pytest`.
4. Update `docs/DATA_MODEL.md` and `docs/diagrams/er.mmd` (re-render the PNG).
