# API Development Standard

| | |
|---|---|
| Owner | Boluwatife Israel |
| Version | 1.2 (2026-10-03): expired access tokens are `401 token_expired` (retryable), distinct from `token_invalid`; the framework's own 400 uses the profile's validation status; pending methods on a built path. 1.1 (2026-10-03): a contract can be ahead of the code (pending operations are reported, not failures); full server URLs in the contract; `postgres://` database URLs accepted; `alembic check` compares server defaults. 1.0 (2026-09-30): first version |
| Applies to | Every HTTP backend (API service) I build, for any project |
| Default stack | **Python 3.12, uv, FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, PostgreSQL** (§3). Anything else is a documented exception. |
| Structure | §1–20 are the standard. §21 explains **profiles**: one per project, kept in that project's repository. Appendices hold templates and reference code. |
| Home | [`api-standard`](https://github.com/IsraelBO17/api-standard), a template repository: every API repository starts from it |
| Sibling | [Agent Development Standard](https://github.com/IsraelBO17/agent-standard) (2.2). Where both cover a topic (errors, config and secrets, observability, IaC, tags, versioning) they agree. |

**MUST** is required to ship. **SHOULD** is expected; skipping it needs a written reason in the repository's README. **MAY** is optional.

---

## 1. What this covers

An **API service** here is one deployable HTTP backend: it owns a PostgreSQL database, exposes a versioned JSON API described by an OpenAPI contract, and may stream responses and run background jobs. It is built mostly by a coding agent (Claude Code) with the owner approving decisions (§6.1).

Build the simplest thing that works:

| If the project needs… | Build |
|---|---|
| a few endpoints over one database | One service, one feature per resource (§7) |
| work that must survive restarts, retry, or run later | The job table (§13) |
| a response that arrives over time | A stream (§14) |
| a screen that filters or sorts across many features | A composed read (opt-in module, Appendix E) |
| isolation between customers inside one database | Row-level security (opt-in module, Appendix E) |
| a second service | Only when it deploys, scales or fails on a different schedule. Otherwise add a feature. |

## 2. Principles

1. **Default stack, documented exceptions** (§3), so every service is built, tested and run the same way.
2. **Built for coding agents.** Every repository tells a coding agent how to work in it (`CLAUDE.md`, recipes, skills) and how to check its own work (`make check`) (§6.1).
3. **Spec, then contract, then code.** What an operation does is written in `SPEC.md`; what goes over the wire is written in `openapi.yaml`; code implements both (§5, §8).
4. **One writer per table.** A feature is the only code that writes its tables. Everything else asks it (§7).
5. **One commit per unit of work.** The service opens and commits the transaction; everything below it only flushes (§11).
6. **Nothing irreversible inside a transaction.** Emails, payments, queue sends and calls to other systems happen after commit, from a job (§13).
7. **Errors are a contract.** One problem format, stable codes, never renamed (§9).
8. **Fail at startup, not at 3 a.m.** Settings are typed and validated at boot; unsafe values refuse to start (§10).
9. **Untrusted by default.** Every request, header, file and upstream response is validated; every query is scoped to its owner (§12, §15).
10. **Observable and owned.** Every request and job can be traced by one id, and every resource is named and tagged to its project (§17, §19).

## 3. Default stack

| Concern | Default | Notes |
|---|---|---|
| Language and packaging | Python 3.12, `uv` (`uv.lock` committed) | |
| Web framework | **FastAPI** (0.142+) on Uvicorn, started by the service's own `serve` module (§14) | Pure-ASGI middleware only (§14) |
| Validation and wire models | **Pydantic v2** (2.13+) | camelCase on the wire, snake_case in Python (§8) |
| Settings | **pydantic-settings** | Typed, validated at boot (§10) |
| Database | **PostgreSQL** | Version set by the profile |
| Data access | **SQLAlchemy 2.1** (`sqlalchemy[asyncio]`, async ORM) with **psycopg 3** (`psycopg[binary]`, URL `postgresql+psycopg://`) | The same URL gives a sync engine for Alembic and an async one for the app |
| Migrations | **Alembic** (sync `env.py`, direct URL) | Single head; `alembic check` in `make check` |
| Background work | A **Postgres job table** and a worker (§13) | No broker by default |
| Streaming | Server-Sent Events with FastAPI's `fastapi.sse.EventSourceResponse` (§14) | |
| Auth | Bearer access token (JWT, pinned algorithm) issued by the service; identity provider set by the profile (§12) | |
| Logging | Standard-library `logging`, JSON in deployed environments (§17) | |
| Tracing | OpenTelemetry (FastAPI, SQLAlchemy, httpx) (§17) | Exporter and distro set by the profile (e.g. ADOT, collector-less) |
| Tests | pytest, pytest-asyncio (1.x), httpx `AsyncClient` + `asgi-lifespan`; **Schemathesis** 4 for contract tests (§18) | Integration tests against real Postgres |
| Lint, format, types | ruff (lint and format, including the `FAST`, `ASYNC` and `S` rules), **mypy** strict with the Pydantic plugin | No SQLAlchemy mypy plugin (removed in 2.1; not needed) |
| Dependency scanning | `pip-audit` on `uv export`, and Dependabot (`uv`, `docker`, `github-actions`) (§15) | `uv audit` is still experimental |
| Container | Multi-stage: `ghcr.io/astral-sh/uv` builder, `python:3.12-slim-trixie` runtime, both pinned by digest, **arm64**, non-root (§19) | |
| Infrastructure | **Terraform** (§19) | Names and tags from the profile |
| CI | GitHub Actions running `make check` (§20) | |

**Exceptions.** Another framework, database or driver is allowed when the README says why. The rest of the standard still applies.

## 4. Lifecycle and gates

| Stage | What happens | Exit gate |
|---|---|---|
| **0. Spec** | Intake with the owner: `SPEC.md` (Appendix A) | Resources, actors, rules, non-functional needs and open questions written; owner approved |
| **1. Contract** | `openapi.yaml`: every endpoint, schema, error code and event | Valid OpenAPI 3.1 (`tests/unit/test_contract_file.py`, in `make check`); owner approved |
| **2. Build** | Features built in dependency order, each with its capability blocks (Appendix B) and tests | `make check` green; contract tests pass for every implemented operation |
| **3. Deployed (dev)** | Image built, pushed and deployed by Terraform | `/v1/health` returns 200 through the load balancer; a traced request visible; plan shown to the owner before apply |
| **4. Live** | Real use | A week without an open blocker; alarms in place |
| **5. Retired** | Traffic stopped | Data exported or deleted per the spec; infrastructure destroyed |

## 5. The spec

Every repository MUST start with `SPEC.md` (Appendix A), written with the owner **before any code**. It captures what only the owner knows: the job of the service, its users and clients, resources and who owns them, the rules for each operation, non-functional needs (latency, volume, retention, availability), integrations, and data classification. Anything the owner hasn't answered stays in **Open questions**; it is never silently defaulted.

Each operation that writes, or that another feature, a job or the clock can invoke, gets a **capability block** (Appendix B) in the feature's `SPEC.md` section before its code: actor, inputs, rejections (each becomes a guard clause and a test), effect, transaction, side effects, idempotency, audit, invariants. When a rule changes, the block changes first, in the same commit as the code and tests.

## 6. Repository

- One repository per service, created from the **api-standard** template, named by the profile (for example `<project>-api`). When the API lives inside a product monorepo, the template's contents go in that repository's API folder.

```
<service>/
├── SPEC.md                 §5
├── CLAUDE.md               For coding agents: read order, commands, defaults, "never" list (§6.1)
├── Makefile                `make check` (the done gate), `make fmt`, `make db-up`, `make run`, `make migrate`
├── openapi.yaml            The contract (§8). Source of truth for the wire.
├── schemathesis.toml       Contract-test exceptions, each with a reason (§18)
├── docs/                   STANDARD.md (snapshot), RECIPES.md, PROFILE link
├── .claude/skills/         Claude Code skills that run the recipes (§6.1)
├── README.md               What it does, how to run, test and deploy; owner; exceptions to this standard
├── CHANGELOG.md            One line per released version
├── pyproject.toml, uv.lock
├── alembic.ini, migrations/
├── src/<package>/
│   ├── main.py             create_app(): middleware, error handlers, routers, lifespan. The only wiring.
│   ├── serve.py            Starts Uvicorn and flags shutdown for draining streams (§14)
│   ├── worker.py           Runs the job worker and sweeps (§13)
│   ├── core/               Technical capability, no business rules (§7)
│   │   ├── settings.py     §10
│   │   ├── db.py           Engine, sessions, Base, SessionDep (§11)
│   │   ├── errors.py       Problem responses and the base exceptions (§9)
│   │   ├── logging.py      JSON logs with request and trace ids (§17)
│   │   ├── auth.py         Access-token verification, CurrentUser, require_role (§12)
│   │   ├── context.py      Request-scoped values (request id, user id)
│   │   ├── lifecycle.py    The `shutting_down` event (§14)
│   │   ├── middleware.py   Request id, access log, security headers, body limit (§15)
│   │   ├── schemas.py      ApiModel, ApiInput, PageQuery, Page, cursors (§8)
│   │   ├── service.py      BaseService: the transaction boundary and after-commit hooks (§11)
│   │   ├── health.py       GET /v1/health
│   │   └── jobs/           models, queue (enqueue, claim, settle), registry (@job, @sweep), runner (§13)
│   └── features/<name>/    One package per feature (§7)
├── tests/
│   ├── unit/               No database, no network, no environment
│   ├── integration/        Against real Postgres (§18)
│   └── contract/           The app against openapi.yaml (§18)
├── Dockerfile              §19
├── .github/                CI and Dependabot (§20)
└── infra/                  Notes or Terraform for this service (§19)
```

MUST: the files above that apply, including the coding-agent files. SHOULD: CI on every pull request.

### 6.1 Working with coding agents

Services are built mostly by coding agents with the owner approving decisions. Every repository therefore carries:

| File | Purpose |
|---|---|
| `CLAUDE.md` | Read at the start of every session: what the service is, read order (`SPEC.md` → `openapi.yaml` → `docs/RECIPES.md` → `docs/STANDARD.md` → profile), commands, layout in one line, defaults to use without asking, a "never" list, and what "done" means |
| `docs/RECIPES.md` | Step-by-step playbooks: start a new API, add a resource end to end, add a migration, add auth, add a job, add a stream, add an integration, deploy. Each ends with **Verify** |
| `.claude/skills/` | Claude Code skills that run the recipes: `/new-api`, `/add-resource`, `/add-migration`, `/add-auth`, `/add-job`, `/add-stream`, `/add-integration`, `/deploy`, `/pre-merge` |
| `Makefile` | `make check`: lint, format check, types, migrations in sync, unit, integration and contract tests. The gate a coding agent runs before saying anything is done |

Rules:
- **Spec before contract before code.** A coding agent writes `SPEC.md`, then the contract, and stops for the owner's approval after each.
- **Recipes over improvisation.** When a recipe is missing or wrong, fix the recipe in the template (with a version bump) rather than working around it.
- **Defaults over questions.** Ask only what the spec, profile and this standard don't settle; ask in one batch, with a recommendation.
- **Self-check before done.** `make check` passes, and the change was run, not just written.
- **Keep them in sync.** A change to this standard updates the recipes, skills and `CLAUDE.md` in the same release.

## 7. Layering and features

`src/<package>/` has two layers and one wiring point:

- **`core/`**: technical capability (settings, database, errors, logging, middleware, jobs). No business rules. Never imports a feature.
- **`features/<name>/`**: one package per resource or business area. Each has the same files, so any feature reads the same:

| File | Holds | Rule |
|---|---|---|
| `router.py` | HTTP endpoints | Thin: parse, call the service, shape the response. No business rules, no session handling, no error bodies built by hand |
| `schemas.py` | Wire request and response models | Match `openapi.yaml`; private to the feature |
| `service.py` | Business rules and **the transaction** | One method per capability block; guard clauses from its rejections |
| `repository.py` | Queries for this feature's tables | Only this feature's tables; flushes, never commits |
| `models.py` | SQLAlchemy tables this feature owns | Only this feature writes them |
| `exceptions.py` | Typed errors with stable codes | One class per error code (§9) |
| `public.py` | The feature's **door**: functions (and exceptions) other features may use | Takes the caller's session; returns frozen dataclasses, never ORM rows; flushes, never commits |
| `jobs.py` | Handlers for jobs this feature owns (optional) | Registered with the job registry (§13) |

- `main.py` is the only module that imports a feature's `router`.
- **Import rules** (checked by `tests/unit/test_architecture.py`): `core` imports no feature; a feature imports another feature **only** through its `public.py`; the feature import graph has no cycles.
- **Write ownership:** only a feature's own repository writes its tables. A change to another feature's data goes through that feature's `public.py` (a complete business operation such as `close_account`, never a setter such as `set_status`) or a job that feature handles.
- **Deleting a parent another feature references** never makes the parent's feature write the child's table, and a door call back would create an import cycle. The spec says what happens to the children, and the database does it: `ON DELETE CASCADE`, or `ON DELETE SET NULL (<ref>_id)` (the column-list form, PostgreSQL ≥ 15, so a composite owner key keeps its `user_id`). Work that must happen in code is a job the child's feature handles.
- **Reads across features** go through `public.py`. Every door read that a caller could run in a loop MUST have a batch form (`get_cards_by_ids`) beside the single one.
- **Uniform means uniform:** a feature with no rules still has a `service.py` that forwards to the repository. Don't invent logic to fill it.
- Tables MAY be prefixed with their feature (`billing_invoices`) when a service has several features writing related tables; the profile decides.

When a service outgrows this (many features, cross-feature screens, several teams), adopt the **large-app module** (Appendix E): the `reads/` layer for composed queries and the full architecture ratchet.

## 8. API design

**Contract-first.** `openapi.yaml` (OpenAPI 3.1) is written by hand, reviewed, and is the source of truth. Code implements it; Schemathesis checks the running app against it (§18). FastAPI's generated schema is not published: the service serves the contract file at `/openapi.yaml` or not at all (profile). The first `servers` entry gives the path prefix: `url: /v1` with paths like `/notes`, or a full URL such as `https://api.example.com` with paths that start with `/v1`.

| Topic | Rule |
|---|---|
| Paths | `/v1/<plural-noun>`, `/v1/<plural-noun>/{id}`, kebab-case segments. Actions that aren't CRUD are `POST /v1/<noun>/{id}/<verb>` |
| Versioning | Major version in the URL. Additive changes (new fields, endpoints, optional parameters, error codes) don't bump it; removing or changing the meaning of anything does, as `/v2` alongside `/v1` |
| Casing | JSON is **camelCase** on the wire; Python and SQL are snake_case. Pydantic's alias generator does the mapping (Appendix C). Query parameters are camelCase too |
| Ids and times | UUIDs; RFC 3339 UTC timestamps with `Z` |
| Bodies | A single resource is returned bare (no envelope). Lists are `{ "items": [...], "nextCursor": "…" \| null }` |
| Inputs | Request bodies and query parameters are Pydantic models on `ApiInput` (queries as `Annotated[PageQuery, Query()]`): only the contract's camelCase names are accepted, not the snake_case Python names; unknown names and strings containing NUL (PostgreSQL text can't store it) are `400 invalid_request` |
| Patterns | A `pattern` uses explicit ASCII classes (`[A-Za-z0-9]`, `[^\x00-\x20]`), never `\s`, `\w` or `\d`: OpenAPI (ECMA-262), Schemathesis and Pydantic (Rust `regex`) disagree on them. The Pydantic field uses the same pattern |
| Pagination | List operations are named `list<Resources>`. Cursor-based: `?cursor=&limit=` (default 50, max 100). The cursor is opaque (base64 of the sort key and a unique tiebreaker). Every list has a total order ending in a unique column. Offset pagination only for small, bounded admin lists |
| Status codes | 200 read or update, 201 create (with `Location`), 202 accepted for a job, 204 delete. Errors per §9 |
| Partial updates | `PATCH` with only the fields to change: an absent field is unchanged. `null` is invalid (400) unless the field is nullable in the contract, and then it means clear |
| Idempotency | Every create that a client may retry MUST be idempotent: by a client-supplied natural key with a unique constraint (default), or by an `Idempotency-Key` header (opt-in module). The claim commits or rolls back with the work, never in a cache. The same key with different content is `409 idempotency_conflict` |
| Request ids | Every response carries `X-Request-Id`: the inbound one if present and well-formed, otherwise a new one. It is logged on every line and returned in every error (§9, §17) |
| Deletion | Deleted resources return 404 and never appear in lists |
| Limits | Every list, text field, file and array has a documented maximum |

## 9. Errors

Every error response is **RFC 9457** `application/problem+json`:

```json
{
  "type": "https://<errors base URL>/<code>",
  "title": "Session not found",
  "status": 404,
  "detail": "No session with that id.",
  "code": "session_not_found",
  "requestId": "req_8f2a…",
  "retryable": false
}
```

- `code` is **required**, snake_case, stable. Clients branch on `code`, never on `title` or `detail`. A shipped code is **never renamed or removed**: add the new one, keep sending the old until clients have moved.
- `requestId` and `retryable` are required. `retryAfter` (seconds) is set, and the `Retry-After` header too, when known (429, 503).
- **Validation** errors (including a body that doesn't parse) are **`400 invalid_request`** with `errors: [{ "path": "/json/pointer", "message": "…" }]`, one per bad field. A profile MAY choose 422 instead; the code and shape stay the same.
- Every code is listed in the contract's `ErrorCode` enum with its status, and defined once in code as an exception class (`exceptions.py`) with `status` and `code`. A feature that must raise another feature's error (a referenced row not found) imports it from that feature's `public.py`.
- **Every database constraint has a typed exception** and a service-side check: unique → 409, check → 400, foreign key → 404 on the referenced thing. The check gives the good message; the constraint makes the rule true under concurrency. The service maps an `IntegrityError` **by constraint name** (`constraint_name(exc)`) and re-raises any it doesn't expect, which then surfaces as a 500.
- Unhandled exceptions return `500 internal_error` with no stack trace or driver message; the traceback is logged with the request id.
- A `405` carries an `Allow` header listing **every** method the path supports (RFC 9110). Starlette lists only the first matching route's, so the error handler computes it from all routes.
- Streams and stored failures (a job's last error, a message's error) use the same Problem object.
- Routers never build error bodies; services raise, and one handler in `core/errors.py` renders.

## 10. Configuration and secrets

- **12-factor:** one image for every environment; only environment variables differ.
- `core/settings.py` is one `Settings` class (pydantic-settings) loaded once. Required values have no default, so a missing one **stops the service at boot**. Secrets are `SecretStr`.
- A setting whose wrong value is dangerous is validated, not documented: outside local development the service refuses to start with a placeholder or short secret, a wildcard CORS origin, or (in prod) the contract exposed; values outside their allowed set (e.g. a validation status other than 400 or 422) are refused everywhere.
- Database URLs may use `postgres://` or `postgresql://` (as hosts hand them out); settings convert them to `postgresql+psycopg://`.
- Secrets live in the cloud secrets manager and are injected as environment variables by the platform at start (profile). Never in the repository, images, logs, or the database.
- Settings read `.env.example` (committed: a safe local value for every required setting), then `.env` (gitignored overrides), then the real environment. The image contains neither file, so in a deployed environment a missing value still stops the boot. A new required setting needs only its line in `.env.example` (and the deployment's list in `infra/README.md`).
- Every limit (timeouts, pool sizes, page caps, body size, retention) is a setting with a default in code.

## 11. Data

### 11.1 Models and migrations
- SQLAlchemy 2 typed models (`Mapped[...]`, `mapped_column`), one `Base` with a **naming convention** for constraints, UUID primary keys generated by the database, `timestamptz` everywhere, `created_at`/`updated_at` on every table.
- Enumerations are text columns with a `CHECK` constraint (cheaper to change than Postgres enums).
- Every owned table carries its owner column, named for the owner (`user_id`, `org_id`), indexed, and **every query filters on it**. It references the owner's table when the service has one. A row that points at another owned row uses a composite foreign key `(<ref>_id, user_id)` to that table's unique `(id, user_id)`, so it can never point at another owner's row.
- An index exists for every query a repository runs; list queries are backed by an index matching their `WHERE` and `ORDER BY`.
- **Alembic**, one linear head, revision ids ≤ 32 characters, reviewed by hand after autogenerate. `alembic check` (models match migrations, including server defaults) runs in `make check`. Each migration SHOULD touch one feature.
- Migrations run with the **direct** database URL, never through a transaction-mode connection pooler; the app uses the pooled URL when there is one.
- Before launch, no backfill shims; after launch, a destructive change is two releases (expand, then contract).

### 11.2 Sessions and transactions
- One `AsyncSession` per request (`SessionDep`), `expire_on_commit=False`.
- **The service owns the transaction**: `async with self.transaction():` around the unit of work, one commit. Repositories and `public.py` functions MAY `flush()`; they MUST NOT `commit()`, `rollback()` or create a session.
- **Nothing irreversible inside the transaction.** No HTTP calls, emails or queue sends between `begin` and `commit`: a third party's timeout becomes your lock time, and a rollback can't un-send. Write the intent (a job row) inside; the job does the work after commit (§13).
- Never catch a database error and continue: the session is unusable after it. Check business rules before writing.
- **When a failure must leave a record** (a revoked session after token reuse, a failed attempt), write the record inside the transaction, let it commit, and raise after the `async with` block: an exception inside it rolls everything back.
- Keep transactions short. Acquire row locks in a consistent order.
- Every transaction sets `SET LOCAL statement_timeout` (setting) from the engine's `begin` event: transaction-scoped, so it works through a transaction-mode pooler, which rejects the `options` startup parameter. Long operations run as jobs with their own timeout.

### 11.3 Connections
- A small app-level pool (`pool_size`, `max_overflow`, `pool_timeout`, `pool_pre_ping`) sized to the database's connection limit divided by the number of tasks.
- Behind a **transaction-mode pooler** (PgBouncer and managed equivalents): no session state (`SET` without `LOCAL`, session advisory locks, `LISTEN`, `WITH HOLD` cursors, SQL `PREPARE`), no startup `options`. Prepared statements: psycopg's protocol-level ones work through PgBouncer ≥ 1.22 with `max_prepared_statements > 0` and libpq ≥ 17 (bundled by `psycopg[binary]`); the default is to turn them off (`prepare_threshold=None`) until a test through the real pooler shows they work. The profile records the result.
- Connection strings require TLS (`sslmode=require` or stricter).
- The engine is disposed in the lifespan shutdown.

## 12. Authentication and authorization

- **Authentication** is one dependency in `core/auth.py` (`CurrentUser`): it verifies the service's access token and yields a `Principal` (user id, roles), and puts the user id in the request context for logging. Every endpoint except health and the auth endpoints depends on it. How users sign in and how sessions last is added by the `/add-auth` recipe.
- Access tokens are short-lived JWTs signed by the service. The algorithm is **pinned in code**, never read from the token or a setting. Required claims (`sub`, `exp`, `iat`, `iss`, `aud`) are enforced by the decoder.
- Browser sessions: a short-lived access token held in memory, and a **rotating refresh token** stored hashed in the database, sent in an `HttpOnly; Secure; SameSite=Strict` cookie scoped to the auth path. Reuse of a rotated refresh token revokes the whole family.
- External identity providers (Google, Cognito, an SSO) only prove identity once; the service then issues its own session. Which provider is set by the profile.
- **Authorization** lives in the service that owns the resource: every query filters by the principal's owner id, so another owner's row is **404, not 403** (OWASP API1). Coarse role gates (`require_role`) MAY sit on routers; anything that depends on what the resource is belongs in the service and its capability block.
- Authentication failures are `401` with one generic message; the reason is logged, not returned. The one distinction kept is an **expired** access token: `401 token_expired` (`retryable: true`), so a client refreshes and repeats instead of sending the user to sign in. A known user who lacks permission is `403`.
- Auth endpoints that use cookies check `Origin` against the allowed origins.

## 13. Background work

Anything that must survive a restart, retry, or happen after commit is a **job**.

- Jobs are rows in a `jobs` table owned by `core/jobs/`: `type`, `payload` (JSON), `status` (`queued`, `running`, `succeeded`, `failed`, `dead`), `attempts`, `max_attempts`, `run_at`, `locked_until`, `last_error` (Problem), `request_id`, `idempotency_key`, timestamps.
- **Enqueue inside the producing transaction** (`await jobs.enqueue(session, "billing.send_receipt", {...})`), so the job exists if and only if the work that caused it committed. This is the outbox: no separate publish step can be lost.
- A **worker** claims due jobs with `SELECT … FOR UPDATE SKIP LOCKED`, sets a lease (`locked_until`), runs the handler in its own transaction, then marks it succeeded, or failed with backoff, or `dead` after `max_attempts`. An expired lease makes the job claimable again.
- The worker is a second role of the **same image** (`python -m <package>.worker`); a small service MAY run it inside the API process (setting). It stops claiming on SIGTERM and finishes the job it holds.
- **Handlers live in the feature that owns the work** (`features/<name>/jobs.py`), are registered by type name, and write only their feature's tables (others via `public.py`). Handlers MUST be idempotent: every job may run twice.
- Payloads carry ids, not objects, and are validated by a Pydantic model on the way in.
- Each job runs under the `request_id` of the request that enqueued it, so one id finds the request and everything it caused.
- **Periodic work** (retention, due-scans, stale-run sweeps) are **sweeps**: functions registered with an interval, run by the worker, bounded per run (and logging when capped), idempotent, each with its own retention setting.
- Dead jobs are visible (a query or an admin endpoint) and alarmed on.
- A broker (SQS or similar) is an opt-in module for volumes Postgres can't carry; the rules above still hold.

**Not a job: a response stream.** Work whose output is being streamed to a client (§14) runs in the request's task. Its own row (status, heartbeat, cancel flag) is its durable record, and a sweep marks it interrupted if its heartbeat stops.

## 14. Streaming

- Streams are **Server-Sent Events** (`text/event-stream`) returned from the endpoint that starts the work, with FastAPI's `fastapi.sse.EventSourceResponse` (`response_class=`) and an async generator yielding `ServerSentEvent`s. Clients read them with `fetch` (so they can send a body and `Authorization`), not `EventSource`.
- Each event has an `id`, an `event` name from the contract, and JSON `data`. Event names and payloads are part of `openapi.yaml`.
- **Everything that can refuse a stream runs in a dependency** (auth, not found, limits, `shutting_down`). Dependencies run before the response starts, so a refusal is an ordinary problem response; inside the generator it is too late, because the `200` and headers are already sent.
- A **keep-alive comment** (`: ping`) goes out whenever the stream is idle for 15 s (FastAPI's `EventSourceResponse` does this), independent of the work, and the load balancer's idle timeout is set well above it.
- **Middleware MUST be pure ASGI.** Starlette's `BaseHTTPMiddleware` interferes with streaming responses and context variables.
- State that matters is **written to the database as the stream runs** (at boundaries and at most every few seconds), so a crash or deploy loses at most a checkpoint, and a reload can recover from the database.
- Whether a client disconnect cancels the work is decided per stream in the spec; the default is that **only an explicit cancel request cancels**. Cancellation is a flag in the database, so any task can receive it.
- Every stream has a hard time limit (setting) and ends with exactly one terminal event.
- **Graceful shutdown.** Uvicorn gives the app no signal that shutdown has started: it stops accepting connections, waits for open requests up to `timeout_graceful_shutdown`, cancels what's left, and only then runs the lifespan shutdown. So the service starts Uvicorn from its own `serve` module, whose `Server.handle_exit` also sets an app-level `shutting_down` event. On that event the service refuses new streams (`503 shutting_down`, `retryable: true`), lets open streams finish, and a stream still running when the drain window ends checkpoints itself as interrupted. `timeout_graceful_shutdown` is set below the container's stop timeout, and the load balancer's deregistration delay covers it (profile).

## 15. Security

| Risk (OWASP API Top 10, 2023) | Rule |
|---|---|
| API1 Broken object-level authorization | Every query filters by owner; another owner's row is 404 (§12). Integration tests prove it for each resource |
| API2 Broken authentication | §12: pinned algorithm, short access tokens, rotating hashed refresh tokens, generic 401 |
| API3 Broken object property-level authorization | Response and request schemas list fields explicitly (`extra="forbid"` on input); no ORM row is returned directly |
| API4 Unrestricted resource consumption | Body-size limit, page caps, field and array maxima, statement timeouts, stream time limits, per-principal limits on expensive actions (§8, §13, §14) |
| API5 Broken function-level authorization | Role gates on admin routes; admin endpoints live under their own router |
| API6 Unrestricted access to sensitive business flows | Per-principal limits in the service for costly or abusable flows (e.g. concurrent runs), from the spec |
| API7 Server-side request forgery | The service never fetches a URL a client supplies unless the host is on an allowlist |
| API8 Security misconfiguration | Settings refuse unsafe values (§10); security headers; CORS with explicit origins only; docs endpoints off outside dev |
| API9 Improper inventory management | `openapi.yaml` is the inventory; contract tests fail on undocumented routes |
| API10 Unsafe consumption of APIs | Upstream responses are validated, time-limited and never trusted as instructions |

Also:
- **CORS:** explicit origins from settings, credentials only when cookies are used, never `*` outside local development.
- **Headers:** `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Strict-Transport-Security` outside local development, `Cache-Control: no-store` on authenticated responses.
- **SQL:** bound parameters only; no string-built SQL with request values.
- **Rate limits:** per-principal limits on expensive actions are enforced in the service against Postgres. Per-IP limits belong to the load balancer or WAF. A Redis limiter is an opt-in module.
- **Logs:** never log tokens, cookies, `Authorization` headers, passwords or request bodies of auth endpoints; log ids, not objects.
- **Dependencies:** `pip-audit` in `make check`; Dependabot for Python, Docker and GitHub Actions; the base image pinned by digest and updated monthly.
- **Least privilege:** one IAM role per service, scoped to its own resources by exact ARN.

## 16. Performance

- An index for every query; `EXPLAIN` any query over a table expected to exceed 100k rows.
- No N+1: batch forms on doors, `selectinload` for relationships a response needs.
- Page caps on every list; cursors, not offsets, for anything that grows.
- Timeouts on every outbound call (connect and read) and on every database statement.
- One HTTP client per upstream per process, created in the lifespan and closed on shutdown.
- Async all the way: no blocking I/O in request handlers (`ruff`'s `ASYNC` rules catch the common cases).
- Response budgets (p95 per endpoint) are stated in the spec when they matter, and checked before launch.

## 17. Observability

- **Logs:** one JSON object per line in deployed environments (readable text locally), through the standard `logging` module. A filter adds `request_id`, `trace_id` and `user_id` to every record, including library records.
- **One wide line per request:** method, route template, status, duration, request id. Levels: 5xx `ERROR`, 4xx `WARNING`, else `INFO`.
- **One line per job:** type, status, attempts, duration, request id.
- **Tracing:** every deployed service SHOULD send OpenTelemetry traces (FastAPI, SQLAlchemy, httpx instrumented) to the profile's backend, with the service name set. Instrument each layer **once**: FastAPI (0.142+) has built-in OpenTelemetry spans using the global providers. The template creates the app with `telemetry={"auto_configure": False}` (exporters come from the distro, not FastAPI), and when a distro's auto-instrumentation runs (e.g. ADOT's `opentelemetry-instrument`), its FastAPI instrumentor is turned off with `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=fastapi`. With a distro that pins OpenTelemetry versions, don't add separate instrumentation packages. The trace id (`trace.format_trace_id(...)`) is on every log line so logs and traces join.
- **Health:** `GET /v1/health` is liveness only: it answers `{"status": "ok"}` without touching the database, so a database outage doesn't become a restart loop. A separate readiness check MAY exist.
- **Alarms** (SHOULD): 5xx rate, p95 latency, dead jobs, unhealthy targets.
- The request id is forwarded on outbound calls (`X-Request-Id`, and `traceparent` when tracing).

## 18. Testing

| Layer | What | Where | When |
|---|---|---|---|
| Unit | Pure logic: validators, mappers, cursors, error rendering, settings validation, the import rules | `tests/unit/` | Every change; no database, network or environment |
| Integration | The app over HTTP (`httpx.AsyncClient` with `ASGITransport`, lifespan run by `asgi-lifespan`) against **real Postgres**; each test in a transaction rolled back at the end | `tests/integration/` | Every change |
| Contract | Schemathesis generates requests from `openapi.yaml` for every operation and checks status codes, content types, headers and response schemas. A unit test also checks the contract is valid OpenAPI, lists every error code the code can raise, and contains every operation the app serves (from `app.openapi()`). Documented operations not built yet are **pending**: listed in the output and skipped by Schemathesis, never a failure, because the contract is written first and built in stages | `tests/contract/`, `tests/unit/` | Every change |
| Migrations | `alembic upgrade head` on an empty database, then `alembic check` | `make check` | Every change |

Rules:
- Tests use a **real Postgres** (`make db-up`), never SQLite and never a shared or deployed database.
- Every capability block's rejections, effect and idempotency lines are test cases.
- Every resource has a test proving another owner gets 404.
- Every constraint has a test proving its violation is the typed error (409/400/404), not a 500.
- A door's write function has a test that it leaves the transaction open (write, roll back, nothing persisted).
- Job handlers are tested by running them twice (idempotency) and by forcing a failure (retry and dead-letter).
- Mock only the outside world (HTTP to third parties), never another feature.
- A Schemathesis exception lives in `schemathesis.toml`, per operation, with a written reason (e.g. an opaque cursor can match its schema and still be invalid). Never relax a check to hide a real mismatch. One expected case: a documented method not built yet on a path whose other methods are built makes `Allow` (honestly) shorter than the contract; turn off `allow_header_conformance` for that path until it is built, with that reason.
- `ASGITransport` buffers a response until the app finishes, so stream tests use finite streams; keep-alive and shutdown behaviour is tested against a real Uvicorn server started by the test.
- Use `httpx.AsyncClient`, not Starlette's `TestClient` (with Starlette 1.x it warns unless `httpx2` is installed, and it runs the app on another thread).
- pytest-asyncio runs in `auto` mode with the loop scope set to `session` for fixtures and tests, so session-scoped database fixtures share one event loop.
- `make check` needs no network beyond the local database and the vulnerability database `pip-audit` queries. No test calls a real third party: integration clients are reached through dependencies that tests override.
- The template's own tests (`tests/unit/`, and `tests/integration/` except `test_notes*.py`) test `core/` without the example feature, using a test-only route in `conftest.py`.
- Setup writes on the rolled-back `session` fixture are undone if the code under test rolls back: commit them first (it commits a savepoint). Rows written in one test share `created_at`; ordering tests set it explicitly.

## 19. Containers, deployment and infrastructure

- **Image:** multi-stage. A `ghcr.io/astral-sh/uv` build stage installs dependencies from `uv.lock` (`--locked`, no dev dependencies) and the project non-editable, with bytecode compiled; the runtime stage is `python:3.12-slim-trixie` with only the `.venv`, migrations and contract copied in, run as a **non-root** user. Both pinned by digest; built for **arm64**. One image runs every role (`api`, `worker`, `migrate`).
- The API process runs Uvicorn (through the `serve` module) with proxy headers on and `forwarded_allow_ips` limited to the load balancer's network (or `*` when only the load balancer can reach the task), and a graceful-shutdown timeout matching §14.
- **Migrations** run as a one-off task (`alembic upgrade head`) before the new version takes traffic, using the direct database URL.
- **Terraform** defines everything: compute, load balancer, DNS, certificates, secrets (the containers, not the values), registry, IAM, alarms. Remote state with locking, one state per environment, reusable modules.
- **Names and tags** follow the profile's convention on every resource (provider default tags where possible). Tag values that must not be public live in untracked variable files.
- Infrastructure changes are **planned, shown to the owner, and applied only on their yes**.
- Images are tagged with the **git SHA**; rollback is deploying the previous tag.

## 20. CI, versioning and release

- CI (GitHub Actions) runs `make check` on every pull request and on `main`, with a Postgres service container. Third-party actions are pinned by commit SHA with the version in a comment; `uv sync --locked` fails if the lock file is stale.
- Dependabot opens weekly updates for Python, Docker and Actions.
- The service version (semver) is in `pyproject.toml` and `openapi.yaml` (`info.version`); `CHANGELOG.md` gets one line per release. The API's URL version (§8) changes only for breaking changes.
- Every release: `make check` green, contract changes reviewed, migrations reviewed, image built and tagged with the SHA, plan shown before apply.

### Definition of done for a change
- [ ] `SPEC.md` capability blocks and `openapi.yaml` updated first, in the same pull request
- [ ] `make check` passes (lint, format, types, migrations in sync, unit, integration, contract, audit)
- [ ] New constraints have typed errors and tests; new resources have the other-owner 404 test
- [ ] No irreversible work inside a transaction; new jobs are idempotent and tested twice
- [ ] No shipped error code renamed or removed
- [ ] The change was run (the endpoint called, the job executed), not just tested
- [ ] `CHANGELOG.md` updated for a release

### Definition of done for a release
- [ ] The above, for every change in it
- [ ] Version bumped in `pyproject.toml` and `openapi.yaml`
- [ ] Image built for arm64, tagged with the git SHA, pushed
- [ ] Migrations applied with the direct URL before traffic moves
- [ ] Terraform plan shown to the owner and approved before apply
- [ ] `/v1/health` returns 200 through the load balancer; a traced request is visible

---

## 21. Profiles

A profile adds one project's specifics on top of this standard: the contract location, the identity provider, cloud account, region, resource names and tags, database hosting and pooler, stream rules, deployment target, and any choice this standard leaves to the profile (validation status, table prefixes, docs exposure). It MUST NOT weaken sections 1–20.

Profiles live in the **project's** repository, not here. Template: [`PROFILE_TEMPLATE.md`](PROFILE_TEMPLATE.md).

Each project's README links its profile; this standard lists none.

---

## Appendix A: Spec template

The intake template is the repository's [`SPEC.md`](../SPEC.md). A coding agent fills it with the owner before any code (recipe 1).

## Appendix B: Capability block template

One per operation that writes, or that another feature, a job or the clock can invoke. It lives in `SPEC.md` under its feature.

```markdown
### capability: `<verb_resource>` → `<Feature>Service.<method>()`  (POST /v1/…)
- **intent:** one line, product terms.
- **actor / authz:** who may call it; which owner scope applies.
- **inputs:** fields and limits.
- **rejections:** one line each, `<condition> → <status> <code>`. Each becomes a guard clause and a test.
- **effect:** what is written, and what is returned.
- **cross-feature:** doors called (`<feature>.public.<fn>`), or none.
- **transaction:** what is inside the one commit; what is deliberately after it (jobs).
- **side effects:** jobs enqueued, streams started; for each, idempotent? inside or after commit?
- **idempotency:** none, natural key (which), or `Idempotency-Key`.
- **audit:** none, or what is recorded and where.
- **invariants:** what stays true after it runs.
- **open questions:** anything the owner hasn't answered. Empty means ready to build.
```

For a job handler, add **trigger**, **payload**, **retries** and **what `dead` means**. For a sweep, add **interval**, **bound per run** and **retention setting**.

## Appendix C: Reference code

The template's `src/api_name/` is the reference implementation; the snippets below are its core. Each was checked against the library's documentation on 2026-09-30.

Versions checked: FastAPI 0.142.2, Starlette 1.7.0, Pydantic 2.13.5, pydantic-settings 2.15.0, Uvicorn 0.54.0, SQLAlchemy 2.1.1, psycopg 3.3.6, Alembic 1.20.0, pytest-asyncio 1.4.0, Schemathesis 4.28.0, mypy 2.3.1, ruff 0.16.9. Each snippet ran against Postgres 17 under `mypy --strict` and the template's ruff rules.

### C1. Settings (§10)
```python
from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env.example (committed local defaults), then .env, then the environment; the image has
    # neither file. pydantic-settings forbids unknown variables by default; env files need "ignore".
    model_config = SettingsConfigDict(env_file=(".env.example", ".env"), extra="ignore")

    env: str = "local"                      # local | dev | prod
    database_url: str                       # required: no default, so a missing value stops the boot
    database_url_direct: str | None = None  # migrations (never through a transaction-mode pooler)
    session_signing_key: SecretStr
    cors_origins: list[str] = []            # JSON in the environment: '["https://app.example.com"]'
    db_statement_timeout_ms: int = 30_000
    db_pool_size: int = 5
    db_prepared_statements: bool = False    # true only after a test through the real pooler
    port: int = 8000
    forwarded_allow_ips: str = "127.0.0.1"  # the load balancer's network, or "*" if only it can reach the task
    shutdown_grace_seconds: int = 90        # below the container's stop timeout

    @model_validator(mode="after")
    def _refuse_unsafe(self) -> "Settings":
        if self.env != "local":
            if "*" in self.cors_origins:
                raise ValueError("CORS_ORIGINS must list explicit origins outside local")
            if len(self.session_signing_key.get_secret_value()) < 32:
                raise ValueError("SESSION_SIGNING_KEY must be at least 32 characters")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### C2. Wire models: camelCase out, snake_case in Python (§8)
```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    # `populate_by_name` is discouraged since Pydantic 2.11; use the validate_by_* pair.
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True,
                              validate_by_alias=True, serialize_by_alias=True,
                              from_attributes=True)


class ApiInput(ApiModel):
    # Only the contract's names: unknown fields AND the snake_case Python names are a 400 (API3).
    model_config = ConfigDict(extra="forbid", validate_by_name=False, validate_by_alias=True)

    @field_validator("*", mode="before")
    @classmethod
    def _no_nul(cls, value: Any) -> Any:   # PostgreSQL text can't store NUL: 400, not a 500
        if _contains_nul(value):           # walks strings in nested lists and dicts too
            raise ValueError("must not contain the NUL character")
        return value


class Page[T](ApiModel):
    items: list[T]
    next_cursor: str | None                     # "nextCursor" on the wire
```
FastAPI serialises response models by alias by default, so endpoints return camelCase with no extra flags.

### C3. Errors as RFC 9457 problems (§9)
```python
class ApiError(Exception):
    """Base for every error the API returns. One subclass per code, in the feature's exceptions.py."""
    status: int = 500
    code: str = "internal_error"
    title: str = "Something went wrong"
    retryable: bool = False

    def __init__(self, detail: str | None = None, *, retry_after: int | None = None,
                 **extra: Any) -> None:
        super().__init__(detail or self.title)
        self.detail, self.retry_after, self.extra = detail, retry_after, extra


def problem(status: int, code: str, title: str, *, detail: str | None = None,
            retryable: bool = False, retry_after: int | None = None,
            headers: dict[str, str] | None = None, **extra: Any) -> JSONResponse:
    body: dict[str, Any] = {"type": ERRORS_BASE + code, "title": title, "status": status,
                            "code": code, "requestId": request_id_var.get(), "retryable": retryable}
    if detail:
        body["detail"] = detail
    headers = dict(headers or {})
    if retry_after is not None:
        body["retryAfter"] = retry_after
        headers["Retry-After"] = str(retry_after)
    body.update(extra)
    return JSONResponse(body, status_code=status, headers=headers,
                        media_type="application/problem+json")


def _allowed_methods(request: Request) -> str:
    allowed = []
    for method in ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"):
        scope = {**request.scope, "method": method}
        if any(route.matches(scope)[0] == Match.FULL for route in request.app.router.routes):
            allowed.append(method)
    return ", ".join(allowed)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return problem(exc.status, exc.code, exc.title, detail=exc.detail,
                       retryable=exc.retryable, retry_after=exc.retry_after, **exc.extra)

    @app.exception_handler(RequestValidationError)
    async def _invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"path": "/" + "/".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
                  for e in exc.errors()]
        return problem(VALIDATION_STATUS, "invalid_request", "Invalid request", errors=errors)

    @app.exception_handler(StarletteHTTPException)   # also catches router 404 and 405
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        headers = dict(exc.headers or {})
        if exc.status_code == 405:
            # RFC 9110: Allow lists every method the resource supports. Starlette lists only the
            # first route that matched the path, so collect them from all routes.
            headers["Allow"] = _allowed_methods(request)
        return problem(exc.status_code, _HTTP_CODES.get(exc.status_code, "http_error"),
                       str(exc.detail), headers=headers)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_error", exc_info=exc)
        return problem(500, "internal_error", "Something went wrong")
```
A feature's error is two lines:
```python
class NoteTitleTaken(Conflict):   # Conflict: status 409
    code, title = "note_title_taken", "A note with that title already exists"
```

### C4. Request id and access log, pure ASGI (§8, §14, §17)
```python
class RequestIdMiddleware:
    """Pure ASGI: BaseHTTPMiddleware blocks context-var changes and gets in the way of streams."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        inbound = dict(scope["headers"]).get(b"x-request-id", b"").decode("latin-1")
        rid = inbound if _VALID_ID.match(inbound) else f"req_{uuid.uuid4().hex}"
        token = request_id_var.set(rid)
        started, status = time.perf_counter(), 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message).append("X-Request-Id", rid)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            route = scope.get("route")
            level = (logging.ERROR if status >= 500
                     else logging.WARNING if status >= 400 else logging.INFO)
            log.log(level, "request", extra={
                "method": scope["method"], "route": getattr(route, "path", scope["path"]),
                "status": status, "duration_ms": round((time.perf_counter() - started) * 1000, 1)})
            request_id_var.reset(token)
```
In `create_app()`, add CORS first and this middleware last, so it is outermost (the last `add_middleware` wraps the rest), and list `X-Request-Id` in CORS `expose_headers`.

### C5. Engine and session (§11)
```python
def make_engine(settings: Settings) -> AsyncEngine:
    connect_args: dict[str, Any] = {"connect_timeout": 10}
    if not settings.db_prepared_statements:
        connect_args["prepare_threshold"] = None   # psycopg: no server-side prepared statements
    engine = create_async_engine(settings.database_url, pool_size=settings.db_pool_size,
                                 max_overflow=5, pool_timeout=10, pool_pre_ping=True,
                                 pool_recycle=300, connect_args=connect_args)
    timeout = int(settings.db_statement_timeout_ms)

    @event.listens_for(engine.sync_engine, "begin")
    def _statement_timeout(conn: Connection) -> None:
        # Transaction-scoped, so it works through a transaction-mode pooler (which rejects
        # the `options` startup parameter). The event also fires on autobegin.
        conn.exec_driver_sql(f"SET LOCAL statement_timeout = {timeout}")

    return engine
```
The lifespan creates the engine and `async_sessionmaker(engine, expire_on_commit=False)`, and calls `await engine.dispose()` on shutdown. `SessionDep = Annotated[AsyncSession, Depends(get_session)]` yields one session per request. Alembic's `env.py` is the plain synchronous template: `create_engine("postgresql+psycopg://…")` on the same URL scheme is sync.

### C6. The transaction boundary and a service (§7, §11)
```python
class BaseService:
    """Only services commit; repositories and doors flush."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._after_commit: list[Callable[[], Awaitable[None]]] = []

    def after_commit(self, fn: Callable[[], Awaitable[None]]) -> None:
        """Runs only if the transaction commits. Not for irreversible work: that is a job."""
        self._after_commit.append(fn)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        try:
            yield
            await self.session.commit()
        except BaseException:
            self._after_commit.clear()
            await self.session.rollback()
            raise
        hooks, self._after_commit = self._after_commit, []
        for fn in hooks:
            try:
                await fn()
            except Exception:
                log.exception("after_commit_failed")


class NoteService(BaseService):
    async def get(self, owner_id: uuid.UUID, note_id: uuid.UUID) -> NoteOut:
        note = await NoteRepository(self.session, owner_id).get(note_id)
        if note is None:                 # another owner's note is "not found" too (OWASP API1)
            raise NoteNotFound()
        return NoteOut.model_validate(note)

    async def create(self, owner_id: uuid.UUID, data: NoteCreate) -> NoteOut:
        repo = NoteRepository(self.session, owner_id)
        try:
            async with self.transaction():
                if await repo.title_exists(data.title):      # the good message
                    raise NoteTitleTaken()
                note = await repo.add(data.title)           # flushes
                await enqueue(self.session, "notes.index", {"noteId": str(note.id)})
        except IntegrityError as exc:                        # the constraint wins a race
            raise NoteTitleTaken() from exc
        return NoteOut.model_validate(note)
```

### C7. Jobs: enqueue in the transaction, claim with SKIP LOCKED (§13)
```python
async def enqueue(session: AsyncSession, type_: str, payload: dict[str, Any], *,
                  idempotency_key: str | None = None, delay: timedelta = timedelta()) -> None:
    """Inside the caller's transaction: the job exists if and only if that work commits."""
    stmt = insert(Job).values(type=type_, payload=payload, idempotency_key=idempotency_key,
                              request_id=request_id_var.get(), run_at=func.now() + delay)
    if idempotency_key is not None:
        stmt = stmt.on_conflict_do_nothing(index_elements=["type", "idempotency_key"],
                                           index_where=Job.idempotency_key.is_not(None))
    await session.execute(stmt)


async def claim(session: AsyncSession, *, limit: int, lease: timedelta) -> list[Job]:
    """Several workers can claim at once without blocking; an expired lease is claimable again."""
    due = (select(Job.id)
           .where(or_(Job.status.in_(("queued", "failed")),
                      (Job.status == "running") & (Job.locked_until < func.now())),
                  Job.run_at <= func.now())
           .order_by(Job.run_at).limit(limit)
           .with_for_update(skip_locked=True))
    rows = await session.scalars(
        update(Job).where(Job.id.in_(due))
        .values(status="running", attempts=Job.attempts + 1, locked_until=func.now() + lease)
        .returning(Job))
    return list(rows)
```

### C8. A stream, and draining it on shutdown (§14)
```python
# serve.py: the container's command. Uvicorn tells the app nothing until open requests end,
# so this sets an app-level event the moment SIGTERM arrives.
class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        shutting_down.set()
        super().handle_exit(sig, frame)


def main() -> None:
    settings = get_settings()
    config = uvicorn.Config("app.main:create_app", factory=True,
                            host="0.0.0.0",  # noqa: S104 (inside a container)
                            port=settings.port, proxy_headers=True,
                            forwarded_allow_ips=settings.forwarded_allow_ips,
                            timeout_graceful_shutdown=settings.shutdown_grace_seconds,
                            log_config=None)
    Server(config).run()
```
From the template's `features/notes/router.py`:
```python
async def streamable_note(note_id: uuid.UUID, user: CurrentUser, svc: Service) -> NoteOut:
    """Refusals run here: dependencies run before the response starts."""
    if shutting_down.is_set():
        raise ShuttingDown(retry_after=5)          # 503, retryable
    return await svc.get(user.user_id, note_id)     # 404 for another owner's note


@router.post("/{note_id}/stream", response_class=EventSourceResponse)
async def stream_note(
    note: Annotated[NoteOut, Depends(streamable_note)],
) -> AsyncIterable[ServerSentEvent]:
    deadline = time.monotonic() + get_settings().stream_time_limit_seconds
    words = note.body.split()
    for n, word in enumerate(words, start=1):
        if shutting_down.is_set() or time.monotonic() > deadline:
            yield ServerSentEvent(event="stream.interrupted", id=str(n), data={"sent": n - 1})
            return
        yield ServerSentEvent(event="word", id=str(n), data={"index": n, "text": word})
        await asyncio.sleep(0)
    yield ServerSentEvent(event="stream.completed", id=str(len(words) + 1), data={"sent": len(words)})
```
`EventSourceResponse` JSON-encodes `data`, sends `: ping` after 15 s of silence, and sets `Cache-Control: no-cache` and `X-Accel-Buffering: no`. Verified: a SIGTERM sent to a live Uvicorn in the middle of a stream produced `run.interrupted`, and the process then exited.

### C9. Tests: a rolled-back transaction per test, and the contract (§18)
```python
@pytest.fixture(scope="session")
async def app() -> AsyncIterator[ASGIApp]:
    application = create_app()
    async with LifespanManager(application) as manager:   # ASGITransport doesn't run the lifespan
        yield manager.app


@pytest.fixture
async def client(app: ASGIApp) -> AsyncIterator[httpx.AsyncClient]:
    async with engine().connect() as conn:
        outer = await conn.begin()
        # The services' commits become savepoints; the outer transaction is rolled back.
        session = AsyncSession(bind=conn, expire_on_commit=False,
                               join_transaction_mode="create_savepoint")

        async def _session() -> AsyncIterator[AsyncSession]:
            yield session

        fastapi_app.dependency_overrides[get_session] = _session
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://test") as c:
            yield c
        fastapi_app.dependency_overrides.clear()
        await session.close()
        await outer.rollback()
```
```python
@pytest.fixture
def api_schema(app: ASGIApp) -> schemathesis.BaseSchema:
    schema = schemathesis.openapi.from_path("openapi.yaml")
    schema.app = app                           # in process; the prefix comes from servers[0].url
    return schema


schema = schemathesis.pytest.from_fixture("api_schema")


@schema.parametrize()
@settings(max_examples=25, derandomize=True, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_matches_contract(case: schemathesis.Case) -> None:
    case.call_and_validate()
```
Contract tests write data too, so they use the same rolled-back session, and no test assumes an empty table.

### C10. Container (§19)
The template's `Dockerfile` is the reference: a `ghcr.io/astral-sh/uv:<version>-python3.12-trixie-slim` builder running `uv sync --locked --no-dev --no-install-project`, then `uv sync --locked --no-dev --no-editable`, copying `.venv` into a `python:3.12-slim-trixie` runtime (both pinned by multi-arch digest; built with `docker build --platform linux/arm64`, since a constant `FROM --platform` is flagged by Docker's linter), running as a non-root user with `CMD ["python", "-m", "<package>.serve"]`.

## Appendix D: Profile template

[`PROFILE_TEMPLATE.md`](PROFILE_TEMPLATE.md).

## Appendix E: Opt-in modules

Added by a recipe when the spec needs them, never by default.

| Module | Use when | What it adds |
|---|---|---|
| Large app | Many features, cross-feature screens, several contributors | `reads/` layer for composed read-only queries (read-only session), the full architecture ratchet, feature-prefixed tables |
| Row-level security | Several customers share tables and a missed filter would leak data | An app role without `BYPASSRLS`, policies on every owned table, the owner id bound per transaction, a boot check |
| Idempotency keys | Clients can't supply a natural key for a create | An `idempotency_keys` table; the claim and the stored response commit with the work |
| Broker | Job volume or fan-out beyond what a Postgres table carries | SQS (or similar) carrying job ids; the job table stays the record |
| Redis rate limiter | Per-IP or per-key limits the load balancer can't express | A sliding-window limiter that fails open |
| Audit log | Security-relevant actions must be answerable for years | An append-only `audit_events` table written in the same transaction |
