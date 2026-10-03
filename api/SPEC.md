# Agent Hub API: spec

| | |
|---|---|
| Owner | Israel B. |
| Status | Approved through the planning documents below |
| Profile | [`../docs/API_PROFILE.md`](../docs/API_PROFILE.md) |

Agent Hub's API was specified before this template existed, so the spec lives in the planning documents rather than in this file. This file indexes them and holds the capability blocks for operations as they are built (standard §5, Appendix B).

## 1–3. Job, clients, resources
- Job, users, screens and scope: [`../docs/PRODUCT_PLAN.md`](../docs/PRODUCT_PLAN.md).
- Decisions (auth, data, streaming, deploy): [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) D1–D27, P1–P8.
- Tables and the rules the database enforces: [`../docs/DATA_MODEL.md`](../docs/DATA_MODEL.md).
- The send/stream flow, statuses, timers and error codes: [`../docs/SEND_MESSAGE.md`](../docs/SEND_MESSAGE.md).
- Every operation, schema, error code and event: [`openapi.yaml`](openapi.yaml).

## 4. Features and their rules
Capability blocks are added here by the issue that builds each feature (#6 auth, #7 agents, #8 send and stream, #9 Stop). Issue #5 (the shell) adds no operation that writes: only `GET /v1/health`, which is liveness only and never touches the database.

### Feature: auth (issue #6; F13, D8, D9, D25)
Owns `users` and `refresh_tokens`. Every other feature reads the signed-in user through `CurrentUser` (the access token), never through these tables.

Shared rules:
- **Origin check:** every `/v1/auth/*` endpoint rejects a missing `Origin`, or one not in the allowed origins, with `403 origin_not_allowed`. The cookie is `SameSite=Strict`; this is the second guard (D8).
- **Access token:** a JWT signed with `SESSION_SIGNING_KEY` (HS256, pinned), `sub` = user id, about 15 minutes. Expired → `401 token_expired` (the client refreshes and repeats); any other fault → `401 token_invalid`.
- **Refresh token:** 32 random bytes, stored only as a SHA-256 hash. Cookie `ah_refresh=<token>; HttpOnly; Secure; SameSite=Strict; Path=/v1/auth; Max-Age=2592000`, host-only on `api-fleet.qucoon.com`. Every sign-in starts a **family**; each refresh rotates within it.

#### capability: `sign_in_with_google` → `AuthService.sign_in()` (POST /v1/auth/google)
- **intent:** turn a Google ID token into an Agent Hub session.
- **actor / authz:** anyone; only invited or active users get a session (D9).
- **inputs:** `idToken` (string); the `Origin` header; user agent and client IP for the token row.
- **rejections:**
  - `Origin` missing or not allowed → `403 origin_not_allowed`
  - body invalid → `422 invalid_request`
  - ID token fails verification: bad signature, `aud` ≠ `GOOGLE_CLIENT_ID`, `iss` not Google, expired, or `email_verified` not true → `401 invalid_google_token`
  - Google's key set can't be fetched → `503 identity_provider_unavailable` (retryable)
  - no user with this Google `sub`, and no `invited` user with this email → `403 not_invited`, with `email` in the problem
  - user `disabled` → `403 account_disabled`
- **effect:**
  - Find the user by Google `sub`. Failing that, find the `invited` user by email (case-insensitive) and activate it: set `google_sub`, `status = active`.
  - Refresh `name`, `avatar_url` and `last_login_at` from the token.
  - Insert a refresh token in a new family.
  - Return `{accessToken, expiresAt, user: Me}` and set the cookie.
- **cross-feature:** none.
- **transaction:** Google's token is verified **before** the transaction (an outside call never runs inside one); the user update and the token insert are one commit.
- **side effects:** none (no job).
- **idempotency:** each sign-in is a new session; a retried request just makes a second family.
- **audit:** `last_login_at`, plus the token row's user agent and IP.
- **invariants:** an `active` user always has a `google_sub` (database CHECK); a Google `sub` maps to at most one user.

#### capability: `refresh_session` → `AuthService.refresh()` (POST /v1/auth/refresh)
- **intent:** keep a signed-in browser signed in without Google.
- **actor / authz:** whoever holds the refresh cookie.
- **inputs:** the `ah_refresh` cookie; `Origin`.
- **rejections:**
  - `Origin` missing or not allowed → `403 origin_not_allowed`
  - no cookie, unknown token, expired, or revoked → `401 session_expired`
  - token already **rotated** (reuse) → revoke the whole family (committed), then `401 session_expired`
  - user `disabled` → revoke the family, then `403 account_disabled`
- **effect:** mark the token rotated and insert its successor in the same family, with a fresh 30 days; return `{accessToken, expiresAt}` and set the new cookie.
- **transaction:** rotation is one commit. A revocation that must survive the error commits first, and the error is raised after the transaction (standard §11.2).
- **cross-feature:** none. **side effects:** none.
- **idempotency:** not idempotent by design. A second use of the same token is reuse, which signs the family out: that's the theft signal (D8).
- **audit:** the rotated and revoked timestamps on the rows.
- **invariants:** at most one live (not rotated, not revoked) token per family.

#### capability: `sign_out` → `AuthService.sign_out()` (POST /v1/auth/logout)
- **intent:** sign out on this device.
- **inputs:** the `ah_refresh` cookie, if any; `Origin`.
- **rejections:** `Origin` missing or not allowed → `403 origin_not_allowed`. Nothing else: a missing, unknown or expired cookie still returns `204`.
- **effect:** revoke the cookie's family if the token is known; clear the cookie (`Max-Age=0`); return `204`.
- **cross-feature:** none. **transaction:** one commit. **side effects:** none.
- **idempotency:** yes; repeating it returns `204`.
- **audit:** `revoked_at`. **invariants:** as refresh.

#### capability: `get_me` → `AuthService.me()` (GET /v1/me)
- **intent:** who is signed in, for the shell and Settings.
- **actor / authz:** a valid access token.
- **rejections:** `401 token_expired` or `token_invalid`; a token whose user no longer exists or is disabled → `401 token_invalid`.
- **effect:** returns `Me`. `preferences` default to `{defaultAgentSlug: null, reopenLastSession: false}` when unset.
- **transaction:** read only. **cross-feature, side effects, idempotency, audit:** none / yes. **invariants:** none.

(`PATCH /v1/me` is P1 and not part of this issue.)

#### operation: `invite_user` → `hub users invite <email>` (operator only, no HTTP)
- **intent:** let a person sign in; v1 has one user, the owner (D9).
- **effect:** insert `users(email, status = invited, invited_at = now())`. An email that already exists is reported and left unchanged.
- **run:** `make -C api invite email=<address>` against the database in `DATABASE_URL_DIRECT`; for dev, Neon's direct URL from Secrets Manager.

**Decided with the owner (2026-10-03):** the owner is invited by email and activated on first sign-in; an unreachable Google key set is `503 identity_provider_unavailable` (added to the contract); this pass builds the API half, and the web screens follow the web shell (#4).

### Feature: agents (issue #7; F01, F02, D6, D23)
Owns `agents`, the registry. Agents are data: the catalog comes from `GET /v1/agents`, and adding an agent is an operator command, never an API or UI change (J1). Reads the signed-in user's `sessions` for `myStats` (sessions isn't a feature yet; its table is read here and never written).

Shared rules:
- **The descriptor** (`agents/<slug>.yaml`, one per agent) holds the contract's `Agent` fields in camelCase, plus `visibility` (`listed` | `hidden`), `sortOrder`, `runtimeArn` or `runtimeEndpoint`, and `runtimeQualifier`. Unknown keys are rejected. `runtimeType: agentcore` needs a Bedrock AgentCore runtime ARN; `http` needs an `https://` endpoint. A tool with `requiresApproval: true` needs `capabilities.approvals: true`. Attachment limits stay within D23 (20 MB, 10 files, the seven types).
- **Not from the descriptor:** health `status` (`online` on insert; set by hand in v1, D23) and `retiredAt`. Re-registering never changes them.
- **The runtime ARN is never returned.** `details.runtimeLabel` defaults to `arn:…:runtime/<runtime id>` (no account id), or the endpoint's host for `http`.

#### capability: `list_agents` → `AgentService.list_agents()` (GET /v1/agents)
- **intent:** the catalog.
- **actor / authz:** a valid access token. **inputs:** none.
- **rejections:** `401 token_expired` or `token_invalid`.
- **effect:** agents with `retired_at IS NULL` and `visibility = listed` (also `hidden` everywhere except `APP_ENV=prod`), ordered by `sort_order`, then `name`. Each has `myStats` for the caller: the number of their sessions with the agent that aren't deleted (archived ones count) and the latest `last_message_at` among them (`null` if none). Not paginated.
- **transaction:** read only. **cross-feature:** reads `sessions` by `user_id`. **side effects, audit:** none. **idempotency:** yes.

#### capability: `get_agent` → `AgentService.get_agent()` (GET /v1/agents/{slug})
- **intent:** one agent, for the agent's page and its sessions, including retired and hidden ones so old sessions stay readable.
- **rejections:** `401`; a slug not matching `^[a-z0-9]+(-[a-z0-9]+)*$` → `422 invalid_request`; no agent with this slug → `404 agent_not_found`.
- **effect:** the agent and the caller's `myStats`, as above.
- **transaction:** read only. **cross-feature:** as above. **side effects, audit:** none. **idempotency:** yes.

#### operation: `register_agent` → `hub agents add <descriptor.yaml>` (operator only, no HTTP)
- **intent:** ship an agent by adding its descriptor (J1, D6).
- **rejections** (exit code 1, nothing written): unreadable file, invalid YAML, or an invalid descriptor (each field error printed); the slug inserted by someone else at the same moment → `conflict` (run it again).
- **effect:** no agent with the slug → insert it (`deployed_at = now()` when it has a `version`). Otherwise update every descriptor column that differs; a changed `version` also sets `deployed_at = now()` (the "Agent updated" divider). Prints `added`, `updated` (with the version change) or `unchanged`, and, for AgentCore, a reminder that the API can call the runtime only once its ARN is in `agent_runtime_arns` (D27).
- **transaction:** one commit; the row is locked (`FOR UPDATE`) while it is compared. **side effects:** none. **idempotency:** yes; the same descriptor again is `unchanged`.
- **audit:** `updated_at`, `deployed_at`; the descriptor's history is git.
- **run:** `make agent-add file=agents/<slug>.yaml` from the repository root, or `uv run hub agents add ../agents/<slug>.yaml` in `api/`, against `DATABASE_URL`; for dev, Neon's URL from Secrets Manager.

#### operation: `list_registry` → `hub agents list` (operator only)
- **effect:** every agent, retired and hidden included: slug, name, stage, status, visibility, version, retired date. Read only.

**Picked defaults (2026-10-03):** hidden agents are listed everywhere but production (the contract said "dev builds"); `myStats` counts archived sessions; the API half is built now and the catalog screen follows the web shell (#4), as with auth.

## 5–8. Non-functional needs, integrations, background work, deployment
See the profile and ARCHITECTURE: one user in v1 (D9), AgentCore runtimes by exact ARN (D27), Neon Postgres (D3), ECS Fargate behind an ALB (D2), the worker inside the API task (P7).

## 9. Open questions
Tracked in ARCHITECTURE §4 and §5.
