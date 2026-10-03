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
Owns `agents`, the registry. Agents are data: the catalog comes from `GET /v1/agents`, and adding an agent is an operator command, never an API or UI change (J1). `myStats` comes from the chat feature, which owns `sessions`, through a hook `main.py` wires in (`agents.public.provide_session_stats`): chat depends on agents, so agents can't import chat.

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

### Feature: chat (issue #8; F03, F04, F05, D5, D10, D11, D18, D21, P1–P3)
Owns `sessions`, `messages` and `tool_calls`. Uses the agents feature through its door (the agent to call, the `AgentRef` on sessions) and gives it, through a hook wired in `main.py`, the session counts behind `myStats`, so agents never imports chat. Flow, statuses and timers: [`../docs/SEND_MESSAGE.md`](../docs/SEND_MESSAGE.md).

Shared rules:
- **A reply is a run.** The run id is the assistant message id. The send's transaction saves the user message and an empty `streaming` assistant message (`started_at`, `heartbeat_at` = now), then commits; only then is the agent called (rule 1). The run is an asyncio task of its own, not the request's: the SSE response only mirrors it, so a disconnect stops the mirroring, not the run (D11, rule 5). A reply stream is not a job (standard §13): its `messages` row is its record.
- **The agent call:** `InvokeAgentRuntime` over HTTPS with SigV4 (`bedrock-agentcore`, the task role's credentials), runtime session id = our session id, qualifier = the agent's `runtimeQualifier` or `DEFAULT`, body = `AgentInvocation` (history per D18: earlier turns, oldest first, at most 20 turns or 32,000 characters; text kept, thinking dropped, a tool as `[tool <name>: <summary>]`). Connect timeout 10 s; the stream may be silent for minutes (thinking, tools), so the read timeout is the run cap. Only `agentcore` runtimes are called; an `http` agent is `503 agent_unavailable` until an adapter exists (D10).
- **Translation (D10)**, written against `tests/fixtures/agentcore/`: text and reasoning deltas become `text` and `thinking` blocks (a thinking block's `startedAt` is when its model call started, because Strands sends the summary in one burst after the silence); a tool-use content block becomes a `tool` block with status `running` and its parsed input when the block ends, and its `toolResult` completes it (`succeeded`, `failed`, or `cancelled` for `{"error": "cancelled"}`); `result` ends the run with its token usage; an `error` frame fails it. Signatures, metadata and unknown frames are ignored. Block ids are `b1`, `b2`, … in order.
- **Saving (P1):** blocks are saved when a block completes and at least every 2 s while text streams; every save and a 15 s tick write `heartbeat_at`. A tool call is a `tool_calls` row (input and output each truncated to 16 KB) inserted when it starts and updated when it ends; the stored block holds only `{id, type: tool, toolCallId}` and is hydrated from the row on every read (P6).
- **The stream:** `run.started` (with `session` when the call created it, `userMessage` and `assistantMessage`), then `block.started` / `block.delta` / `block.completed`, then exactly one of `run.completed`, `run.failed` (also for `interrupted`). Ids are `<messageId>:<n>`. A `: ping` comment goes out after 15 s without an event.
- **Endings:** `result` → `complete` (any stop reason but `cancelled`); `result` with `cancelled` (the agent's own time limit; Stop is #9) → `interrupted`, `run_time_limit`; `error` frame or a body that ends without `result` → `failed`, `agent_error`; AgentCore throttling (429) → `failed`, `rate_limited` with `retryAfter`; AgentCore unreachable or 5xx → `failed`, `agent_unavailable`; other AgentCore refusals → `failed`, `agent_error`; the run cap (15 min) → `interrupted`, `run_time_limit`; still running when a shutdown's drain window ends → `interrupted`, `run_interrupted`; a bug of ours → `failed`, `internal_error`. Open blocks are closed and running tools become `cancelled` on any ending but `complete`. Errors are stored and streamed as the problem object, with the send's `requestId`.
- **Limits:** at most 3 `streaming` replies per user (`429 too_many_runs`, `retryAfter` 10), counted under a per-user advisory lock in the send's transaction; one open reply per session (the unique index `uq_messages_open_reply_per_session`).

#### capability: `create_session_and_send` → `ChatService.start()` (POST /v1/agents/{slug}/sessions)
- **intent:** the first message of a new session, with its reply streamed (F03: the session exists only once sent).
- **actor / authz:** a valid access token.
- **inputs:** `slug`; `SendMessageRequest` (`clientMessageId`, `text`, `fileIds`, `answer`).
- **rejections** (nothing is saved):
  - `401`; slug not matching the pattern or a body that fails the schema → `422 invalid_request`
  - no text after trimming, and no files or answer → `422 empty_message`; text over 32,000 characters → `422 message_too_long`
  - unknown agent → `404 agent_not_found`; retired → `409 agent_retired`; `status = offline`, or a runtime type with no adapter → `503 agent_unavailable`
  - `fileIds` given: the agent takes no files → `422 attachments_not_supported`, otherwise `409 file_not_ready` (uploads arrive with the files feature)
  - `answer` given → `409 question_not_open` (questions arrive with their feature)
  - the API is draining for a deploy → `503 shutting_down` (`retryAfter` 5)
  - three replies already streaming for this user → `429 too_many_runs`
  - `clientMessageId` already used: same agent and same content → `200 application/json` `SendReplay` (no new run); otherwise → `409 idempotency_conflict`
- **effect:** insert the session (`title` = the text with whitespace collapsed, cut at a word boundary to about 60 characters, `title_source = auto`, D21), the user message (`seq` 1, `complete`, text block) and the assistant message (`seq` 2, `streaming`, `reply_to_id`, `agent_version` = the agent's version); commit; start the run and stream it. `last_message_at` is set at the send and when the reply ends.
- **transaction:** one commit before the agent is called; the run's checkpoints are their own small commits.
- **cross-feature:** agents door: `get_for_send(slug)`, `refs_by_ids`.
- **side effects:** the `InvokeAgentRuntime` call, outside any transaction.
- **idempotency:** by `clientMessageId` per user, as above; a race between two identical sends is decided by the unique `(user_id, client_message_id)`, and the loser replays.
- **audit:** the rows themselves (`created_at`, `started_at`, `completed_at`, `usage`).
- **invariants:** `seq` is unique per session; at most one open reply per session.

#### capability: `send_message` → `ChatService.send()` (POST /v1/sessions/{sessionId}/messages)
- **intent:** the next message in a session, with its reply streamed.
- **rejections:** as `create_session_and_send`, plus: no such session for this user, or deleted → `404 session_not_found`; a reply in the session is still open → `409 run_in_progress`. The replay applies when the `clientMessageId` was used in this session with the same content.
- **effect:** user message and assistant message at the next two `seq`s; history is the session's earlier messages. A reply `awaiting_approval` would be completed by the send (D19); that arrives with approvals, and until then any open reply is `409 run_in_progress`.
- **transaction, cross-feature, side effects, idempotency, audit, invariants:** as above.

#### capability: `get_message` → `ChatService.get_message()` (GET /v1/messages/{messageId})
- **intent:** poll a reply after a lost connection (P3), every 2 s while `streaming`.
- **rejections:** `401`; a malformed id → `422 invalid_request`; not this user's, or its session deleted → `404 message_not_found`.
- **effect:** the message as saved by its latest checkpoint, tool blocks hydrated. Read only; idempotent.

#### capability: `list_messages` → `ChatService.list_messages()` (GET /v1/sessions/{sessionId}/messages)
- **intent:** reload a transcript, newest page first (F05).
- **inputs:** `before` (a `seq`, optional), `limit` (1–100, default 50).
- **rejections:** `401`; invalid parameters → `422 invalid_request`; no such session for this user, or deleted → `404 session_not_found`.
- **effect:** the newest `limit` messages with `seq < before`, returned oldest first; `nextBefore` is the smallest `seq` in the page when older messages exist, else `null`. Tool blocks hydrated. Read only; idempotent.

#### capability: `stop_reply` → `ChatService.stop()` (POST /v1/messages/{messageId}/stop) (issue #9; F04, P4)
- **intent:** stop a reply that is being written, keeping what it has written so far.
- **actor / authz:** a valid access token; the message's owner.
- **rejections:** `401`; a malformed id → `422 invalid_request`; not this user's message, or its session deleted → `404 message_not_found`.
- **effect:** if the message is `streaming`, set `cancel_requested_at = now()` (kept if already set) and return `202 {messageId, status: streaming}`. Any other message (a reply that already ended, a user message) is left alone: `202` with its current status. The flag is the signal, so it works whichever task receives the request (rule 7, two tasks during a deploy); the task that runs the reply is also told directly when it is the same one.
- **the run, on seeing the flag** (at most 2 s later: it reads the flag on every save, and every 2 s otherwise): it sends `AgentCancel` (`{"cancel": {"messageId"}}`) on the same runtime session, keeps reading the reply for up to 5 s so the agent's last frames (a tool's `cancelled` result, `result` with `stopReason: cancelled`) are saved, then closes open blocks (running tools become `cancelled`) and saves `stopped`, with no error and the usage if the agent sent it. The stream ends with `run.stopped`. If the reply finished (`end_turn`) before the cancel took effect, it is `complete`. A failed cancel call is logged and the reply is still saved `stopped` (the agent may run on until its own limit).
- **transaction:** one small commit for the flag; the run's endings as before.
- **side effects:** the `AgentCancel` call, from the run, outside any transaction.
- **idempotency:** yes: repeating it keeps the first `cancel_requested_at` and returns `202`.
- **audit:** `cancel_requested_at`, `completed_at`.

Related endings: a reply that hits the run cap or is cut by a shutdown also sends `AgentCancel` (best effort, 3 s), so the agent doesn't run on unread. The sweep saves a dead run that had a stop requested as `stopped` instead of `interrupted`.

#### sweep: `chat.interrupt_stale_replies` (every minute, and at startup)
- `streaming` replies whose `heartbeat_at` is older than 60 s become `interrupted` with `run_interrupted` (the task running them died); their running tools become `cancelled`. A reply still running on the old task during a deploy keeps its heartbeat fresh and is left alone. Bounded to 100 rows per run, oldest first; idempotent.

#### Shutdown (P2)
On SIGTERM new sends get `503 shutting_down`. Runs in progress continue; one still running `SHUTDOWN_GRACE_SECONDS` (110) after the signal is saved as `interrupted` (`run_interrupted`) and its stream ends with `run.failed`. The lifespan waits for runs to save before the process exits.

**Decided with the owner (2026-10-03):** chat owns its tables and feeds `myStats` through a hook wired in `main.py`; a few real calls to Research Analyst are allowed while building. **Picked defaults:** `result` with `max_tokens` or `limit_turns` is `complete`; the agent's own time limit (`cancelled` without a Stop) is `interrupted`, `run_time_limit`; a tool's `summary` is its result's `summary` field, else its error, else the start of its output. The web half follows the web shell (#4).

## 5–8. Non-functional needs, integrations, background work, deployment
See the profile and ARCHITECTURE: one user in v1 (D9), AgentCore runtimes by exact ARN (D27), Neon Postgres (D3), ECS Fargate behind an ALB (D2), the worker inside the API task (P7).

## 9. Open questions
Tracked in ARCHITECTURE §4 and §5.
