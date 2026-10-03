# Recipes

Step-by-step playbooks for the common tasks, written so a coding agent can follow them literally (standard §6.1). Each ends with **Verify**: nothing is done until `make check` passes (with `make db-up` running) and the change has been run. The rules behind each step are in [`STANDARD.md`](STANDARD.md); the project's own values come from its profile.

`features/notes/` is the worked example: when a recipe says "as notes does", open that file and copy its shape (once a project has removed it, the `api-standard` template repository still has it).

| Recipe | Skill | Use when |
|---|---|---|
| [1. Start a new API](#1-start-a-new-api) | `/new-api` | The repository was just created from the template |
| [2. Add a resource end to end](#2-add-a-resource-end-to-end) | `/add-resource` | A new feature or resource |
| [3. Add a migration](#3-add-a-migration) | `/add-migration` | Any change to tables, columns, constraints or indexes |
| [4. Add auth](#4-add-auth) | `/add-auth` | Clients sign in |
| [5. Add a background job or sweep](#5-add-a-background-job-or-sweep) | `/add-job` | Work after commit, retries, or periodic work |
| [6. Add a stream](#6-add-a-stream) | `/add-stream` | A response that arrives over time |
| [7. Add an integration](#7-add-an-integration) | `/add-integration` | Calling another system |
| [8. Deploy](#8-deploy) | `/deploy` | A version is ready for an environment |
| [9. Pre-merge review](#9-pre-merge-review) | `/pre-merge` | Before merging any change |

---

## 1. Start a new API

1. **Ask the owner** (one batch, each with your recommendation): the job in one sentence; the clients and how they sign in; the resources and who owns each; which project profile applies; anything unusual (streams, background work, integrations, volumes). Everything else takes the standard's defaults. **No profile?** Keep the template's placeholder values (`errors.example.com`, a profile link of "none") and set `service_name`, `token_issuer` and `token_audience` to the service's name.
2. **Write `SPEC.md`** from its template: sections 1–8, a capability block for every operation (standard Appendix B), and every unanswered item under Open questions. Typical gaps to ask about: uniqueness rules (case, trimming, normalisation), what deleting a parent does to its children, per-user limits, list filters and order, token and session lifetimes. **Stop and get the owner's approval.**
3. **Write `openapi.yaml`**: every operation in the spec, its request and response schemas (camelCase, `additionalProperties: false`), its error responses, and every error code in `ErrorCode`. Name list operations `list<Resources>` (the cursor exception in `schemathesis.toml` keys on it). Keep the template's `Problem`, `ErrorCode` structure, parameters and `/health`. **Stop and get the owner's approval.**
4. **Rename the package.** First `make db-down` (the database container's name changes with the rename; a still-running old one holds the port). Then `git mv src/api_name src/<name>` (underscores) and replace `api_name` and `api-name` in every tracked file:
   ```bash
   git grep -lz -e api_name -e api-name | xargs -0 sed -i.bak -e 's/api_name/<name>/g' -e 's/api-name/<name-with-dashes>/g' && find . -name '*.bak' -delete
   ```
   Then `uv lock` and `make db-up`. If you run several projects' databases at once, give this one its own `DB_PORT` (Makefile) and the same port in `DATABASE_URL` (`.env.example`).
5. **Apply the profile:** settings defaults (`service_name`, `token_issuer`, `token_audience`, `errors_base_url`, `validation_status`), any settings it adds (required ones get a local value in `.env.example`), and the profile link in `README.md` and `CLAUDE.md`.
6. **Build the foundations with notes still in place:** `/add-auth` if clients sign in, then each feature with `/add-resource`, in the order of `SPEC.md` §4. Copy shapes from `features/notes/` while you do.
7. **Remove the example** once the first real feature exists: delete `src/<name>/features/notes/` and `tests/integration/test_notes*.py`; remove the lines that mention notes from `main.py` (its router import and `include_router`), `worker.py` and `migrations/env.py`; delete its `SPEC.md` section and its `openapi.yaml` paths, schemas and error codes. Nothing else depends on it. Then make a clean first migration: delete `migrations/versions/0001_initial_schema.py`, `make db-reset`, `make migration m="initial schema"` (it is `0001` again), review it (recipe 3).
8. **Fill in the placeholders:** the headers of `README.md` and `CLAUDE.md` (name, one-sentence job, profile link; delete the "Fresh from the template?" line and point the layout line at your features), `pyproject.toml`'s `description`, the docstring in `src/<name>/__init__.py`, `openapi.yaml`'s `info`; delete the template block at the top of `README.md`.

**Verify:** `make check`; `git grep -e api_name -e api-name -e notes` finds nothing you didn't mean to keep.

## 2. Add a resource end to end

Order: spec → contract → model → migration → repository → service → router → tests. Copy each file's shape from `features/notes/` (once the example is removed, from a feature you built, or from the `api-standard` template repository).

1. **Spec:** a capability block per operation in `SPEC.md` §4 (Appendix B). Every rejection has a status and a code. Unanswered items go to the owner first.
2. **Contract:** add the paths, schemas and error codes to `openapi.yaml` (the new codes in `ErrorCode`, with their status in its description). Lists are `list<Resources>`, use `cursor`/`limit` plus their filters, and return `{items, nextCursor}`. A `pattern` uses explicit ASCII classes (`[A-Za-z0-9]`, `[^\x00-\x20]`), never `\s`, `\w` or `\d`: the contract (ECMA-262), Schemathesis and Pydantic (Rust `regex`) disagree on what those match. Use the same pattern in the Pydantic field.
3. **Model** (`features/<name>/models.py`): `Mapped[...]` columns; the owner column named for its owner (`user_id`, `org_id`), with a foreign key to the owner's table when this service has one; `created_at`/`updated_at`; a `CHECK` for each enumeration; a **unique index for each "duplicate → 409" rule**; an index for each list query (`user_id, created_at, id`).
   - A reference to **another feature's** row is allowed; say why in a comment. Make it a composite foreign key `(<ref>_id, user_id)` to that table's unique `(id, user_id)`, so it can't point at another owner's row.
   - **Deleting a parent** owned by another feature: say in the spec what happens to the children, and let the database do it (`ON DELETE CASCADE`, or `ON DELETE SET NULL (<ref>_id)`, the column-list form that leaves `user_id` alone; PostgreSQL ≥ 15). The parent's feature never writes the child's table, and a door call back would make an import cycle.
4. **Migration:** add the models module to `MODEL_MODULES` in `migrations/env.py`, then [recipe 3](#3-add-a-migration).
5. **Exceptions** (`exceptions.py`): one class per new code, subclassing the base for its status from `core/errors.py`: `InvalidRequest` (400), `Unauthenticated` (401), `Forbidden` (403), `NotFound` (404), `Conflict` (409), or `ApiError` with `status`, `code` and `retryable` set (e.g. a retryable 503). An error another feature needs to raise (a missing referenced row) is exported from the owning feature's `public.py`, not redefined.
6. **Schemas** (`schemas.py`): `ApiInput` for request bodies (only contract names accepted, NUL rejected), `ApiModel` for responses, `PageQuery` (or a subclass adding the list's filters) for list parameters. Limits match the contract.
7. **Repository** (`repository.py`): takes the session and the owner id; every query filters on the owner; lists order by `created_at DESC, id DESC` and fetch `limit + 1`; flushes, never commits.
8. **Service** (`service.py`): extends `BaseService`; one method per capability block; guard clauses in the block's order; writes inside `async with self.transaction():`; jobs enqueued inside the transaction; another owner's row raises the not-found error. Catch `IntegrityError` around the transaction and map **each constraint by name** (`constraint_name(exc)` from `core/db.py`) to its typed error; re-raise anything else (it stays a 500, as notes does).
9. **Door** (`public.py`), only if another feature needs this one: frozen dataclasses, a batch form for anything callable in a loop, the caller's session, no commits, plus any exceptions callers need.
10. **Router** (`router.py`): thin; `CurrentUser` on every endpoint; `status_code=201` and a `Location` header for creates, `204` for deletes; `Annotated[PageQuery, Query()]` for lists. Include the router in `main.py`.
11. **Settings:** a new required setting gets a safe local value in `.env.example` and a line in `infra/README.md`'s settings list; nothing else.
12. **Tests** (`tests/integration/test_<name>.py`): each rejection and effect in the blocks; the other-owner 404 for every endpoint; each constraint through the race path (patch the service's check, expect the typed error, not 500); stable pagination and order (set `created_at` explicitly: rows in one test share a timestamp); the door (batch equals single, owner-scoped). Commit setup writes before calling code that may fail (see the `session` fixture's docstring). The contract test covers the new operations automatically; add a `schemathesis.toml` entry only with a written reason.

**Verify:** `make check`; `make run`, then call each new endpoint once with `curl -H "Authorization: Bearer $(make -s token)"` and check the responses match the contract.

## 3. Add a migration

1. Change the models first.
2. `make migration m="<what changed>"`: the file is numbered `0002_…`, `0003_…`, formatted, and Alembic's boilerplate comments are removed.
3. **Review it by hand:** constraint and index names follow the naming convention; `server_default`s are right; partial indexes kept their `WHERE`; `ondelete` rules are what the spec says; nothing unexpected was dropped.
4. **After launch**, destructive changes are two releases: expand (add the new, write both) then contract (remove the old) once nothing reads it. Before launch, change freely.
5. Data changes (backfills) go in the migration with bounded batches, or in a sweep if large.
6. `make migrate`, then `make downgrade` and `make migrate` again to prove the downgrade works.

**Verify:** `make check` (it runs `alembic check`, which fails if the models and migrations disagree); `uv run alembic upgrade head --sql` renders. To start the local database over: `make db-reset && make migrate`.

## 4. Add auth

The template verifies the service's own access tokens (`core/auth.py`). This recipe adds how users prove who they are and how sessions last, as a feature `features/auth/`. The identity provider comes from the profile; the steps are written for an OpenID Connect provider that issues ID tokens (Google, Microsoft, Apple, Cognito).

1. **Spec and contract.** Blocks and paths for `POST /v1/auth/<provider>` (sign in), `POST /v1/auth/refresh`, `POST /v1/auth/logout`. Defaults, unless the owner says otherwise:
   - sign-in returns `{accessToken, tokenType: "Bearer", expiresIn, user: {id, email}}` and sets the refresh cookie; refresh returns the same shape; logout revokes the token's whole family and is always `204`;
   - refresh tokens live `REFRESH_TOKEN_TTL_DAYS` (default 30) from each rotation; access tokens `ACCESS_TOKEN_TTL_SECONDS` (900);
   - codes: `invalid_<provider>_token` (401), `session_expired` (401), `origin_not_allowed` (403), `account_disabled` (403), `not_invited` (403, only with an allowlist), `identity_provider_unavailable` (503, retryable);
   - who may sign in: an allowlist, or anyone (a user row is created on first sign-in). Ask.
2. **Dependencies:** `uv add "pyjwt[crypto]" httpx` (RS256 needs `cryptography`; the key fetch needs an HTTP client at run time).
3. **Tables:** `users` (provider subject unique, email, status `active|disabled`, timestamps); `refresh_tokens` (`id`, `user_id` → `users`, `family_id`, `token_hash` unique, `expires_at`, `rotated_at`, `revoked_at`, `created_at`, user agent). Other features' owner columns now get a foreign key to `users.id`, and `tests/conftest.py`'s `auth` fixture must insert the user it mints a token for.
4. **Verify the provider's token without blocking:** a small verifier class holding one `httpx.AsyncClient` (created in the lifespan, closed on shutdown, explicit timeouts) that fetches the provider's JSON Web Key Set, caches it (honour `Cache-Control`, default an hour), and refetches once when a token names an unknown `kid` (at most once a minute). Decode with PyJWT using `PyJWK` from the cached set, the algorithm **pinned** (`RS256`), `audience` = the client id setting, `issuer` = the provider's issuer(s), required `exp`/`iat`/`sub`, and the provider's own checks (e.g. `email_verified`). Don't use synchronous key clients (`PyJWKClient`, `google-auth`) in a request: they block the event loop. Key-fetch failure is `503 identity_provider_unavailable`.
5. **Make the verifier replaceable:** store it on `app.state` in the lifespan and expose it through a dependency (`get_verifier`), so tests override the dependency with a verifier whose `httpx.MockTransport` serves a key set made from a test RSA key.
6. **Sign-in service:** verify the token **before** opening the transaction (an outside call never runs inside one), then in one transaction find or create the user, reject disabled ones, and insert the refresh token. Issue the access token with `issue_access_token`.
7. **Refresh tokens:** 32 random bytes (`secrets.token_urlsafe(32)`), stored only as a SHA-256 hash, sent as a cookie `HttpOnly; Secure; SameSite=Strict; Path=/v1/auth`, host-only (no `Domain`). Refresh rotates: mark the old row rotated and insert a new one in the same family, in one transaction. **A rotated or revoked token used again revokes the whole family** and returns `401 session_expired`. That revocation must survive the error, so commit first and raise after the transaction block (standard §11.2).
8. **Origin check:** every `/v1/auth/*` endpoint (sign-in too: it sets the cookie) rejects a missing `Origin`, or one not in `CORS_ORIGINS`, with `403 origin_not_allowed`. Browser extensions send `chrome-extension://<id>` (or the browser's equivalent); list it.
9. **Protect the rest:** every router except health and auth depends on `CurrentUser` (already true for template routes). Use `require_role("admin")` for coarse role gates only.
10. **Settings:** the client id (required: a placeholder in `.env.example`, refused outside local), the key-set URL, issuer, cache and timeout settings with defaults.
11. **Tests:** sign-in happy path and each rejection with the stubbed key set (expired, wrong audience, wrong issuer, unverified email, unknown `kid`, `alg: none`); first sign-in creates the user; disabled user is 403; key-set outage is 503; refresh rotates; reuse revokes the family; logout revokes; missing or wrong origin is 403. No test calls the real provider.

**Verify:** `make check`. Signing in for real needs the provider; locally, exercise the rest: insert a user and a refresh-token row (hash of a token you choose), then refresh twice, reuse the first token (401), and log out against `make run`. `make token user=<id>` gives an access token for the other endpoints.

## 5. Add a background job or sweep

1. **Spec:** a job block (trigger, payload, effect, idempotency, retries, what `dead` means) or a sweep block (interval, bound per run, retention setting).
2. **Handler** in the owning feature's `jobs.py` (the shape of the template's `features/notes/jobs.py`): a payload model (`ApiModel`) and `@job("<feature>.<verb>", Payload)`. It flushes; the runner commits it together with "succeeded". It **must be idempotent**: recompute from current state, or check a natural key, so running twice is safe. Calls to other systems go here, never in a request's transaction ([recipe 7](#7-add-an-integration)).
3. **Enqueue** inside the producing service's transaction: `await enqueue(self.session, "<type>", {...})`. Pass ids, not objects. Use `idempotency_key=` when the same event must not queue twice.
4. **Register:** make sure the feature's `jobs.py` is imported in `main.py` and `worker.py`.
5. **Sweeps:** `@sweep("<feature>.<name>", every=timedelta(...))` returning how many rows it touched; bounded by a batch size, oldest first, logging when capped; its own retention setting.
6. **Tests** (as `tests/integration/test_jobs.py`): enqueue then `run_due_jobs` shows the effect; run twice gives the same result; a rolled-back transaction leaves no job; a failure retries and dead-letters.

**Verify:** `make check`; run `make worker` beside `make run`, trigger the job through the API, and see its `job` log line with the request's id.

## 6. Add a stream

1. **Spec and contract:** the endpoint (usually `POST`), its event names and payload schemas (under `x-events` in the `text/event-stream` response), the terminal events, the time limit, and what disconnect and cancel do.
2. **Refusals in a dependency.** Everything that can refuse the stream (auth, not found, `shutting_down`, concurrency limits) runs in a dependency, as `streamable_note` does. Inside the generator it is too late: the `200` has been sent.
3. **The endpoint** is an async generator with `response_class=EventSourceResponse`, yielding `ServerSentEvent(event=..., id=..., data=...)`. It checks `shutting_down` and the deadline between events and ends with exactly one terminal event. FastAPI sends `: ping` after 15 s of silence.
4. **Durable state:** if the stream produces something that must survive, write it as the stream runs (at boundaries, at most every few seconds) with a heartbeat column, and add a sweep that marks rows with a stale heartbeat as interrupted. Cancel is a column set by a separate request, checked between events.
5. **Middleware:** pure ASGI only. Never add `BaseHTTPMiddleware`.
6. **Tests:** finite streams through the in-process client (it buffers the whole response): events, terminal event, each refusal as a problem response, `shutting_down` → 503, the time limit → interrupted.

**Verify:** `make check`; `curl -N -X POST` the endpoint against `make run` and watch events arrive; send SIGTERM mid-stream and see the interrupted event.

## 7. Add an integration

1. **Spec:** the system, what we call, timeouts, and what happens when it fails (retry via the job, or a visible error).
2. **Client** in `core/integrations/<system>.py` (or the owning feature if only it uses it). `uv add httpx` (it is only a dev dependency in the template). One `httpx.AsyncClient` created in the lifespan (or the worker) with explicit connect and read timeouts, closed on shutdown, reached through a dependency so tests can replace its transport; methods returning validated Pydantic models; its own typed errors (never the library's exceptions leaking upward); the request id forwarded as `X-Request-Id`.
3. **Secrets** as settings (`SecretStr`), from the secrets manager in deployed environments.
4. **Where it's called:** from a job handler, never inside a request's transaction. A call the user waits for (rare) happens outside the transaction, with a short timeout.
5. **Upstream data is untrusted:** validate it; never follow URLs or instructions from it.
6. **Tests:** `httpx.MockTransport` for success, each error status and a timeout. Never call the real system from `make check`.

**Verify:** `make check`; one real call from a local run with test credentials, if the owner provides them.

## 8. Deploy

1. Bump the version (semver) in `pyproject.toml`, `src/<name>/__init__.py` and `openapi.yaml`; add a `CHANGELOG.md` line.
2. `make check` on the release commit.
3. `make image`; tag and push to the profile's registry with the git SHA.
4. Set the image tag in the Terraform variables the profile names (a committed file for values that aren't secret). `terraform plan`; **show the plan to the owner and apply only on their yes.**
5. Run migrations as a one-off task with the direct database URL before traffic moves.
6. Roll out (rolling update; see `infra/README.md` for the draining values).
7. Check: `GET /v1/health` returns 200 through the load balancer; one authenticated request succeeds and its trace (or its request id in the logs) is visible.

**Verify:** the release checklist in standard §20 is all ticked.

## 9. Pre-merge review

Check the change against the standard and report PASS / FAIL / N/A for each, with specifics:

- `make check` passes, and the change was run.
- `SPEC.md` blocks and `openapi.yaml` were updated in the same change; every new rejection has a test.
- Only services commit; nothing calls another system inside a transaction; jobs are idempotent and tested twice.
- Features import each other only through `public.py`; the door returns dataclasses and has batch forms.
- Every query filters by owner; the other-owner 404 test exists for new endpoints.
- New constraints have typed errors and a race test; no shipped error code was renamed or removed.
- Request bodies use `ApiInput`; lists use `PageQuery` and a unique tiebreaker; limits are in the contract.
- New middleware is pure ASGI; stream refusals are in dependencies.
- No secrets, account ids or tag values in the diff; new settings are in `.env.example`.
- Migrations reviewed by hand; destructive changes after launch are split into expand and contract.

End with one line: ready to merge, or the blocking items.
