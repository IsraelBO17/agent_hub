# Agent Hub API

The one API behind Agent Hub's web app: auth, the agent registry, sessions and messages, the agent stream, approvals and files (D1). Built to the **API Development Standard** ([`docs/STANDARD.md`](docs/STANDARD.md)) from the `api-standard` template. Project profile: [`../docs/API_PROFILE.md`](../docs/API_PROFILE.md). Spec: [`SPEC.md`](SPEC.md). Contract: [`openapi.yaml`](openapi.yaml). The repository-wide rules in [`../CLAUDE.md`](../CLAUDE.md) apply too.

## Read first
1. `SPEC.md`: what the service does and every operation's rules (capability blocks). The spec comes before code; if a change isn't in it, update it first.
2. `openapi.yaml`: the wire contract. It comes before code too; the contract tests hold the app to it.
3. `docs/RECIPES.md`: how to do each common task. Follow the recipe; don't improvise a different structure.
4. `docs/STANDARD.md`: the rules and defaults behind the recipes. The project profile adds this project's values.

## Commands
| Command | What it does |
|---|---|
| `make db-up` / `make db-reset` | Start the local Postgres (needed by `make check`) / empty it |
| `make check` | Lint, format, types, migrations in sync, unit + integration + contract tests, audit. **Must pass before you say anything is done.** |
| `make fmt` | Fix lint and formatting |
| `make migration m="…"` | New numbered migration from the models; review it by hand |
| `make run` / `make worker` | Run the API on :8000 / the job worker |
| `make token` | A local access token for calling the API with curl |
| `uv run hub …` | Operator commands against `DATABASE_URL`: `agents add <descriptor.yaml>`, `agents list`, `users invite <email>` (`make agent-add`, `make agents`, `make invite`) |
| `make docs` | Swagger UI over the contract at http://localhost:8000/docs, with a local test user's token (local only) |
| `make image` | Build the arm64 image tagged with the git SHA |

Skills: `/add-resource`, `/add-migration`, `/add-auth`, `/add-job`, `/add-stream`, `/add-integration`, `/deploy`, `/pre-merge` (each runs a recipe).

## Layout
`main.py` (`create_app()`, the only wiring) → `features/<name>/` (`router.py` → `service.py` → `repository.py`, plus `models.py`, `schemas.py`, `exceptions.py`, `public.py`, `jobs.py`) on top of `core/` (settings, db, errors, auth, middleware, logging, jobs). `serve.py` and `worker.py` are the process entrypoints. Agent Hub's tables are still in `db/models.py`; each feature moves its own tables into `features/<name>/models.py` when it is built. The template's `notes` example (in the `api-standard` repository) shows every pattern.

## Defaults (don't ask; use these unless the spec or profile says otherwise)
FastAPI, Pydantic v2 (camelCase wire, snake_case Python), SQLAlchemy 2 async + psycopg 3, Alembic, Postgres. RFC 9457 problems with a stable `code`; validation `422 invalid_request` (the profile's choice). `/v1` in the URL. Cursor pagination (`limit` ≤ 100). UUIDs, `timestamptz`, CHECK constraints for enumerations. Every query filters by owner; another owner's row is 404. Background work is a job enqueued in the same transaction. Local settings come from `.env.example` (a new required setting goes there). Streams are SSE. Tests against real Postgres. Terraform; arm64 images tagged with the git SHA. Ask the owner only what's genuinely specific to this service, in one batch, with a recommendation.

## Never
- Write code before its capability block in `SPEC.md` and its operation in `openapi.yaml` exist, or change behaviour without updating both.
- Commit, roll back or open a session anywhere but a service (`BaseService.transaction()`); repositories, `public.py` and job handlers flush.
- Call another system (HTTP, email, payment, queue) inside a transaction: enqueue a job.
- Import another feature's internals: only its `public.py`. `core/` never imports a feature.
- Rename or remove a shipped error `code`, or build an error body in a router.
- Return an ORM row, or take input on anything but `ApiInput` (it accepts only contract names and rejects NUL).
- Use `BaseHTTPMiddleware`, or refuse a stream from inside its generator (do it in a dependency).
- Point tests at anything but the local database, or mock another feature.
- Put secrets, account ids or tag values in code, tests, `.env.example` or commits.
- Apply infrastructure or deploy without showing the owner the plan and getting a yes.

## Done means
`make check` passes; the change was run (the endpoint called, the job executed); `SPEC.md`, `openapi.yaml` and the code agree; the standard's definition of done (§20) holds.
