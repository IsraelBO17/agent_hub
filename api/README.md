# Agent Hub API

The FastAPI service behind Agent Hub (ARCHITECTURE D1, D2). Built to the owner's [API standard](https://github.com/IsraelBO17/api-standard) with Agent Hub's values in [`../docs/API_PROFILE.md`](../docs/API_PROFILE.md). Repo layout: root [`README.md`](../README.md).

| | |
|---|---|
| Owner | Israel B. |
| Stage | Build (M1) |
| Version | 0.5.0 |
| Stack | FastAPI · SQLAlchemy 2 async (psycopg 3) · Neon Postgres · ECS Fargate (exceptions: none) |
| Contract | [`openapi.yaml`](openapi.yaml) (D23) |
| Spec | [`SPEC.md`](SPEC.md), which indexes the planning documents |

- Code: `src/app/`: `main.py` wires `core/` (settings, errors, request ids, logging, database, auth verification, jobs) and the features. `serve.py` is the container's command.
- Schema: `src/app/db/models.py` for tables whose feature isn't built yet; built features keep theirs in `features/<name>/models.py` (`auth`, `agents`). Notes: [`../docs/DATA_MODEL.md`](../docs/DATA_MODEL.md).
- Migrations: `migrations/` (Alembic). They use `DATABASE_URL_DIRECT`, Neon's **direct** (unpooled) connection string; the app uses the pooled one (D3).

## Run and test

Needs [uv](https://docs.astral.sh/uv/) and Docker. From the repository root:

```bash
make db-up
```

```bash
make api-test
```

`make api-test` is the done gate (`make check` in this folder): lint, format, types, migrations in sync, unit, integration and contract tests, and the dependency audit. It wipes and re-creates the local database.

Run the API on port 8000 (local settings come from `.env.example`; put overrides in `.env`):

```bash
make api-migrate && make api-run
```

A local access token for curl: `make -C api token`.

**Operator commands (`hub`):** `uv run hub --help` in this folder. They use the database in `DATABASE_URL` (local by default; for dev, set it to Neon's URL from Secrets Manager without printing it).

- Register or update an agent from its descriptor (D6): `make agent-add file=agents/<slug>.yaml` from the repository root. It reports `added`, `updated` or `unchanged`; the catalog shows the agent on the next load, with no code change.
- List the registry: `make agents`.
- Let someone sign in (D9): `make -C api invite email=<address>`.

**Swagger UI (local only):** `make -C api docs` serves the contract at `http://localhost:8000/docs`, pointed at your local API, and prints an access token for an active local test user: click **Authorize** and paste it. Everything except `POST /v1/auth/google` works there (that needs a real Google ID token for our client ID). The test user is refused on any non-local database.

## Changing the schema

1. Edit the models.
2. `make -C api migration m="what changed"`, then read and fix the generated file (autogenerate misses some things, such as renames and CHECK changes).
3. `make api-check` (should report no changes) and `make api-test`.
4. Update [`../docs/DATA_MODEL.md`](../docs/DATA_MODEL.md) and `docs/diagrams/er.mmd` (re-render the PNG).

## Deploy
Recipe 8 in [`docs/RECIPES.md`](docs/RECIPES.md) with the profile's values; Terraform in [`../infra/`](../infra/README.md).
