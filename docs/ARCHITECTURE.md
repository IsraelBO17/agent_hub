# Agent Hub: architecture decisions

| | |
|---|---|
| Status | v0.4, D1–D27 and P1–P8 locked; §4 questions still open |
| Date | 2026-09-29 |
| Owner | Israel B. (approver) |
| Scope | Back end, infrastructure, auth, data and the agent stream. Product scope stays in `PRODUCT_PLAN.md`. |

This file is the single source of truth for technical decisions. Architecture diagram: [`diagrams/architecture.mmd`](diagrams/architecture.mmd) ([PNG](diagrams/architecture.png)); keep it in sync with this file. When a decision changes, edit it here and add a line to the change log (§7).

**It supersedes parts of `PRODUCT_PLAN.md`.** The plan was written before these decisions and still mentions DynamoDB, Cognito, a Next.js front end, a registry CLI writing to DynamoDB and "API Gateway or Lambda Function URL". Where the two disagree, this file wins:

| Plan says | Now |
|---|---|
| DynamoDB for sessions, approvals, registry (F01, F06, F10, risks) | Neon Postgres (D3, D4, D6) |
| Cognito, `useAuth()` over Cognito (F13, A5) | Direct Google sign-in plus the API's own session (D8) |
| API on ECS Fargate *or* a Lambda Function URL (risks, A5) | ECS Fargate behind an ALB (D2) |
| CloudFront + S3 *or* Amplify (A5) | Amplify Hosting (D13) |
| Registry CLI writes descriptors to DynamoDB (F01, §3) | Agents are rows in Postgres; a small CLI or SQL seed inserts them (D6) |

---

## 1. Decision log

Each entry: the decision, why, and what would make us revisit it.

### D1. One API layer
**Decision.** The browser never calls agents, AgentCore, Postgres or AWS APIs directly. Everything goes through one FastAPI service. The only exception is S3 object transfer through signed URLs the API issues (D7).
**Why.** One place for auth, persistence, stream translation, approval enforcement and cost caps. No AWS credentials in the browser (F13).
**Revisit if.** A second client (mobile app, CLI) needs a different shape of API; even then, add routes, not a second service.

### D2. Compute: ECS Fargate behind an Application Load Balancer
**Decision.** FastAPI runs as a container on ECS Fargate, behind an ALB, defined in Terraform. One task in v1.
**Why.** Replies can stream for minutes. Lambda has a 15-minute cap and awkward streaming from Python. App Runner is closed to new customers. A plain Fargate service gives full control of ALB settings (idle timeout, deregistration delay) that SSE depends on.
**ECS Express Mode.** Not used. Re-checked 2026-09-29 (step 7): AWS's Express Mode best-practices page says the service creates and owns its ALB and target group, and the only documented way to tune them (health-check timeouts, security groups) is afterwards in the EC2 console or CLI, outside the Express configuration. Idle timeout and deregistration delay would then drift from anything in Terraform. A plain service keeps them in code.
**Cheaper options weighed (2026-09-29, owner chose to keep the ALB).** The ALB plus its two public IPv4 addresses is ~$24 of the ~$37/month dev bill. Considered: one EC2 `t4g.micro`/`small` with Caddy for TLS (~$11–17/month; loses draining deploys and adds OS upkeep); Fargate with a public task IP and DNS (fragile: IP changes each deploy, TLS in the container, no draining); API Gateway REST response streaming (still needs a load balancer for a private Fargate backend, or a Lambda rewrite that breaks D11); Lightsail containers (no IAM roles). Kept the ALB, behind an `enable_api` switch so it is only billed from step 8.
**Revisit if.** Express Mode exposes the ALB idle timeout and deregistration delay (it would remove most of the Terraform); or always-on cost matters more than streaming control.

### D3. Database: Neon Postgres, us-east-1
**Decision.** Neon Postgres in us-east-1. The app uses Neon's pooled connection string plus a small app-level pool (SQLAlchemy async). Migrations (Alembic) use the **direct** (unpooled) string, because Neon's pooler runs PgBouncer in transaction mode, which doesn't suit DDL and session-level features.
**Why.** Relational data (sessions, messages, versions, approvals with audit) fits Postgres; Neon is serverless-priced and fast to create by hand.
**Watch.** PgBouncer transaction mode and asyncpg prepared statements: confirm the driver settings in step 8 (for example `statement_cache_size=0` if Neon's pooler rejects them). Neon's resume after idle adds latency to the first query; keep the app pool's connect timeout generous and retry once.
**Revisit if.** Cold resume hurts the first reply noticeably (turn off scale-to-zero on the dev branch or move to RDS), or we need private networking to the database.

### D4. Postgres owns conversation history
**Decision.** Postgres is the record of every session and message. AgentCore Memory is an optional add-on the *agent* may use for its own long-term memory; the UI never reads from it.
**Why.** History must survive agent redeploys, AgentCore session expiry and framework changes (LangGraph later), and must be queryable for the sidebar, search and export.
**Revisit if.** Never for history. Memory usage is per agent.
**Context for the agent:** see D18.

### D5. Streaming: SSE over a `fetch` POST
**Decision.** `POST /v1/sessions/{id}/messages` returns `text/event-stream`. The client reads it with `fetch` and a stream reader, not `EventSource` (which can't send an `Authorization` header or a body). The API writes a keep-alive comment (`: ping`) every 15 s from its own task, independent of the agent. The ALB idle timeout is set explicitly (300 s proposed) rather than relying on the 60 s default.
**Why.** SSE is plain HTTP, passes the ALB, and is enough for one-way streaming; the client never needs to push mid-stream (Stop is a separate request, see P4).
**Revisit if.** SSE fails through the ALB in the step 8 proof, or we need bidirectional traffic (then WebSockets on the same ALB).

### D6. Agents are rows in an `agents` table
**Decision.** Name, slug, description, icon, colour, stage, status, runtime type, runtime ARN or endpoint, capabilities, starters, disclaimer and tool list are columns (capabilities and tools as JSON). Adding an agent is an insert, done by a small CLI or SQL seed in v1 (the Add-agent UI is P2).
**Why.** J1: shipping an agent is the only work. No code change in the API or UI.
**Revisit if.** An agent needs behaviour the descriptor can't express; extend the descriptor, never special-case an agent id.

### D7. Files in S3, metadata in Postgres
**Decision.** Uploads and artifact files live in one private S3 bucket. Postgres holds metadata and ownership. The browser uploads with a short-lived presigned PUT (or POST with size and type conditions) and downloads with a short-lived presigned GET. The API checks ownership before signing.
**Why.** Keeps large bodies off the API task; S3 handles size, durability and range requests.
**Keys.** Every object key starts with `u/{userId}/`, so per-user lifecycle rules, exports and IAM conditions stay possible when there are more users.
**Note.** The bucket needs a CORS rule for the app origin. HTML artifacts are served from a separate origin for the sandbox (F09); that origin is decided in step 9 with artifacts.
**Revisit if.** We need virus scanning or image processing on upload (add an S3 event, not a proxy).

### D8. Auth: Google sign-in, then the API's own session
**Decision.** The browser gets a Google ID token (Google Identity Services) and posts it once to `POST /v1/auth/google`. The API verifies signature (Google JWKS), `aud` (our client ID), `iss`, `exp` and `email_verified`, looks the user up by Google `sub`, and rejects unknown or inactive users. It then issues:
- a short-lived **access token** (JWT, ~15 min, signed with the session key from Secrets Manager), held in memory by the client and sent as `Authorization: Bearer`;
- a rotating **refresh token** (random, stored hashed in `refresh_tokens`) in a cookie: `HttpOnly; Secure; SameSite=Strict; Path=/v1/auth`, host-only (no `Domain` attribute), so it goes only to `api.fleet.qucoon.com` (D25) (all routes live under `/v1`, D23).
Refresh rotates the token and detects reuse (reuse of an old token revokes the whole family). App (`app.`) and API (`api.`) share a parent domain, so the cookie is same-site; CORS allows only the app origin with credentials, and `/v1/auth/*` also checks `Origin`.
**Why.** No Cognito to operate; Google does the hard part; our own session gives revocation and short token lifetime.
**Revisit if.** We need non-Google sign-in, SSO, or passkey step-up (P2).

### D9. Single user via allowlist, multi-user-ready schema
**Decision.** Users are keyed by Google `sub` (email kept for display and invites). Only the owner's row is active, seeded by hand. Every user-owned table has `user_id` from day one, and every query filters on it.
**Why.** Adding users later means inviting them, not migrating data.
**Revisit if.** Teams or shared agents arrive (P2): add an `agent_access` table, not a schema rewrite.

### D10. One common agent stream format
**Decision.** The API translates every agent's output into the app's own message blocks and SSE events. Each runtime type has a translator (Strands on AgentCore first). An agent that can't be translated gets an adapter. The UI knows only the app format.
**Block set.** The decision named text, thinking, tool step, artifact, question and approval. The screens and `PRODUCT_PLAN.md` §5 also need **plan / progress** (P0, F05), **error / stopped status** (P0, F08) and, in P1, **citation, chart, image, file, form**. Proposal P5 adds them to the closed set; the OpenAPI spec (step 5) defines them precisely.
**Why.** New agents and new frameworks plug in with zero UI changes (F26).
**Revisit if.** Never the principle; the block set grows by platform release.
**Blocker.** The real AgentCore/Strands stream must be recorded (step 8) before the translator is written.

### D11. Save timing
**Decision.** The user message is saved before the agent is called. The assistant message is saved when the stream ends. If the user stops or the browser disconnects, the partial text is saved and the message is marked stopped or interrupted.
**Amended 2026-09-29 (accepted):**
- The assistant message row is created when the agent is called and checkpointed during the stream (P1), so "partial text is saved" holds even if the task dies.
- **A browser disconnect does not cancel the agent.** The API keeps consuming the agent stream, saves the full reply and marks it `complete`; the client picks it up on reload (P3). A hard per-run time cap (default 15 min, configurable per agent) ends runaway runs as `interrupted`.
- **Only Stop cancels** (P4). A stopped reply keeps its partial text and is marked `stopped`.
- **Amended 2026-09-29 (alignment review B3):** Stop is a flag in Postgres (`messages.cancel_requested_at`), not an in-memory signal, and dead runs are found by a stale `messages.heartbeat_at`, not by "any `streaming` row at startup". Rolling deploys run two tasks at once, so both P1 and P4 had to work across tasks now, not later.
**Revisit if.** Model cost from orphaned runs becomes noticeable (lower the cap, or cancel after N minutes with no client attached).

### D12. Region: us-east-1
Compute, S3, AgentCore, Secrets Manager, Amplify and Neon all in us-east-1. **Revisit if** a model or AgentCore feature we need isn't there.

### D13. Front-end hosting: AWS Amplify Hosting
**Decision.** Amplify Hosting serves the web app on `fleet.qucoon.com`, same parent domain as the API (D25).
**Why.** Managed builds, previews per branch, TLS, custom domain.
**Revisit if.** We choose a server-rendered framework Amplify handles poorly (not expected: the front end is a static SPA, D16), or cost/control push us to S3 + CloudFront.

### D14. Infrastructure as code: Terraform
**Decision.** Remote state in S3 with locking (S3 native lockfile, `use_lockfile = true`, so no DynamoDB table), one state per environment, reusable modules: service (ECS), load balancer, S3, secrets, Amplify, plus network and ECR. The state bucket is bootstrapped once by a tiny separate config.
**Revisit if.** Never for v1.

### D15. Secrets in AWS Secrets Manager
**Decision.** Neon connection strings (pooled and direct), Google client ID and session signing key live in Secrets Manager. ECS injects them into the container at start through the task execution role (`secrets` in the task definition). Nothing secret in the repo, images or front-end code. The Google client ID is not secret and also ships to the front end as build config.
**Revisit if.** Secret count or cost grows; SSM Parameter Store SecureString is the cheaper fallback.

### D16. Front end: Vite single-page app
**Decision.** React + TypeScript built with Vite, React Router for the routes in `PRODUCT_PLAN.md` §5, TanStack Query for server state, CSS variables generated from the Pencil tokens, Recharts behind `<ChartBlock>` (`CHART_SPEC.md`). Amplify serves it as static files with an SPA rewrite to `index.html`. All API calls go through one client module generated from, or typed against, the OpenAPI spec (step 5). Replaces "Next.js" in `PRODUCT_PLAN.md`.
**Why.** A signed-in app with no SEO needs and a separate API gains nothing from server rendering; a static build is simpler to host, cache and reason about.
**Revisit if.** Public share pages (`/s/:shareId`, P1) need link previews (Open Graph tags): then add a tiny server-rendered route for that page only, or have the API render its meta tags.

### D17. One environment (dev) until v1
**Decision.** Only `dev` is built and deployed until v1. The Terraform layout still has one state per environment and reusable modules, so `prod` is a new directory with its own variables, not a rewrite.
**Why.** Each environment costs roughly $35–45/month always on; two would exceed the $50 budget. With one user, dev is the daily driver.
**Revisit if.** v1 launches, or a deploy to dev breaks daily use once too often.

### D18. The API sends conversation history on every call
**Decision.** Agents are stateless between turns. On each invocation the API reads the session's recent history from Postgres and sends it in the payload, together with the new user message. The API also passes our session id as the AgentCore `runtimeSessionId`, so a warm runtime session can reuse whatever it still has in memory, but no agent may depend on it.
- **What is sent:** prior user and assistant turns as plain role + text (the app's blocks flattened: text kept, thinking dropped, tool steps and artifacts summarised by name and a short result), newest last, trimmed to a per-agent budget (default: last 20 turns or ~32k characters, configurable in the agent's descriptor).
- **Contract:** every agent must accept `{ "messages": [...history], "input": "...", "attachments": [...] }` (exact shape fixed in the OpenAPI/agent contract, step 5; attachments per D20). An agent that can't gets an adapter (D10).
**Why.** AgentCore keeps state only while its runtime session is alive; after the idle timeout the agent forgets. Sending history from the record we already own (D4) keeps agents interchangeable, makes reloads, retries and redeploys behave the same, and needs nothing extra from each agent.
**Later: AgentCore Memory.** An agent may add AgentCore Memory for long-term memory (facts and preferences across sessions, summaries of long sessions), and it can later replace or shorten the history the API sends for that agent. It is opt-in per agent, enabled by a descriptor flag, and Postgres stays the record of the conversation (D4). The UI never reads from it.
**Revisit if.** Payloads get large enough to hurt latency or token cost (summarise older turns, or move that agent to AgentCore Memory), or an agent framework insists on owning its own thread state (LangGraph checkpointer): then that agent's adapter maps our session to its thread.

### D19. An approval ends the run; the decision continues it
**Decision (owner, 2026-09-29).** When an agent asks for approval, the API saves the `approval_requests` row, marks the assistant message `awaiting_approval` and ends the run (the stream closes with `run.awaiting_approval`). `POST /v1/approvals/{id}/decision` records approve or deny, then re-invokes the agent with the history plus the decision and streams the continuation into the **same** assistant message (status back to `streaming`). Deny also re-invokes, so the agent can acknowledge; expiry does not (the message becomes `complete`, the card shows Expired). Sending a new message while an approval is pending cancels it (`cancelled`) and completes the paused message in the same transaction.
**Why.** Agents are stateless between calls anyway (D18). Waiting costs nothing: no open stream, no run-cap time, no session lock, and a deploy can't kill it. The database enforces one open reply per session (`streaming` or `awaiting_approval`).
**Revisit if.** The P8 spike shows a Strands agent can't resume from a re-invocation; then fall back to holding the run open (the alternative considered in step 4b).

### D20. Agents get attachments as short-lived signed URLs
**Decision (owner, 2026-09-29).** The agent payload carries `attachments: [{fileId, name, contentType, sizeBytes, url}]` for the files on the new message, where `url` is a presigned S3 GET valid for 15 minutes. Earlier attachments appear in history by name only. Agent roles get no S3 permissions.
**Why.** Works for any runtime (AgentCore or `http`, LangGraph included) with no IAM change per agent; the API keeps ownership checks (D7).
**Revisit if.** Agents need a file again after 15 minutes (add a tool-side refresh), or files outgrow a single download.

### D21. Session title = the first message, trimmed
**Decision (owner, 2026-09-29).** The API sets `sessions.title` when it creates the session: the first user message, whitespace collapsed, cut at a word boundary to about 60 characters (`title_source = auto`). Rename sets `title_source = user`. No model call and no title event.
**Why.** Instant (the sidebar shows it before the reply), free, and needs nothing from agents or new IAM.
**Revisit if.** Titles are noticeably poor; then have the API ask a small Bedrock model after the first reply and emit `session.updated`.

### D22. Cross-session activity by polling
**Decision (2026-09-29).** There is no per-user push channel in v1. `GET /v1/sessions` rows carry `isRunning` and `pendingApprovals`; the client refreshes the list every 20 s while the tab is visible and diffs it to show the sidebar working dot, the approval badge and toast (P0), and the "Task complete" toast (moved into v1 by the owner, alignment review D4). While the open agent is offline the client polls it every 30 s to unlock the composer.
**Why.** Two indexed queries every 20 s for one user cost nothing; a push channel needs shared state across tasks.
**Revisit if.** There are many users or the 20 s delay feels slow; then add a per-user SSE channel.

### D23. API conventions
**Decision (picked defaults, 2026-09-29; the contract is [`api/openapi.yaml`](../api/openapi.yaml)).** All routes under `/v1`. Errors are RFC 9457 `application/problem+json` with `code`, `requestId`, `retryable` and optional `retryAfter`; the SSE `run.failed` event and `messages.error` use the same object, and every response carries `X-Request-Id`. Cursor pagination (`cursor`, `limit` ≤ 100); messages page backwards by `seq`. Uploads: 20 MB per file, 10 per message, `pdf png jpeg webp gif csv txt`, narrowed per agent by `capabilities.attachments`. At most 3 concurrent runs per user (`429 too_many_runs`). Agents are addressed by slug. UUIDs, RFC 3339 UTC timestamps, camelCase JSON.
**Revisit if.** A second client needs different shapes.

### D24. One repository, one folder per deployable part
**Decision (2026-09-29, step 6).** `api/` (FastAPI, uv), `web/` (Vite SPA, npm), `infra/` (Terraform: `bootstrap/`, `modules/`, `envs/dev/`), `agents/` (one descriptor YAML per agent, inserted by the registry CLI), plus `design/` and `docs/`. No monorepo tooling (no workspaces, Nx or Turborepo): the three parts use three languages and share only the OpenAPI contract, which stays at `api/openapi.yaml` and is read by `web/` for its types. A root `Makefile` holds shortcuts only. Folders are created by the step that first fills them. Agent code lives in each agent's own repository, named `fleet-agent-<slug>` (confirmed by the owner 2026-09-30); this repo holds only descriptors (and the Scenario Agent, if it is built here). How agents are built: `docs/AGENT_PROFILE.md` (fleet's profile of the owner's [agent-standard](https://github.com/IsraelBO17/agent-standard)). Amplify builds `web/` as a monorepo app root.
**Why.** The simplest layout that keeps "adding an agent touches only `agents/`" checkable in a pull request, and keeps each part deployable on its own.
**Revisit if.** A second TypeScript package appears (then npm workspaces), or the contract gains another consumer (then move it to a top-level `contract/`).

### D25. Domain: `fleet.qucoon.com`, delegated to its own Route 53 zone
**Decision (owner, 2026-09-29, Q2; changed the same day from `fleet.qucoon.com`).** `qucoon.com` is hosted in Route 53 in **another AWS account**. Only `fleet.qucoon.com` is delegated to a Route 53 zone in the Agent Hub account (created by `infra/bootstrap`): whoever manages `qucoon.com` adds four `NS` records named `fleet` with the values Terraform prints.
- Web app (Amplify): `https://fleet.qucoon.com`; share links `https://fleet.qucoon.com/s/<slug>`.
- API (ALB): `https://api.fleet.qucoon.com`.
- Certificates: ACM in us-east-1, validated through DNS records in the delegated zone. Amplify manages its own certificate for the app.
- Google OAuth authorised JavaScript origin: `https://fleet.qucoon.com`; CORS allows only that origin.
- Checked 2026-09-29: `qucoon.com` is on Route 53 (`awsdns` name servers), has no CAA records (nothing blocks Amazon certificates), and `fleet` isn't in use.
**Why.** Owning the domain gives the ALB a certificate and puts app and API on one site, which the `SameSite=Strict` refresh cookie needs (D8). A delegated zone keeps Agent Hub's records in its own account and leaves the rest of `qucoon.com` untouched; $0.50/month.
**Revisit if.** The app moves to another domain: change one Terraform variable, the Google OAuth origin and the CORS origin.

### D26. Resource names and required tags
**Decision (owner, 2026-09-29, internal convention).**
- **Names:** `<project>-<environment>-<component>-<type>-<region>`, with project `fleet` and environment `dev`, e.g. `fleet-dev-main-vpc-us-east-1`, `fleet-dev-api-alb-us-east-1`, `fleet-dev-files-s3-us-east-1`. Built in one place per module from `project`, `environment` and `region`. All names fit AWS limits (ALB and target group ≤ 32 characters).
- **Tags on every resource** (provider `default_tags`, plus `propagate_tags` so ECS tasks carry them): `Owner`, `Project` (`fleet`), `Environment` (`dev`), `aws-apn-id`, and `ManagedBy = terraform`.
- **`Owner` and `aws-apn-id` values stay out of git** (the repository is public): they are required Terraform variables with no default, set in the gitignored `terraform.tfvars` of each root. Terraform refuses to plan without them.
- The Terraform state bucket is per environment (`fleet-dev-tfstate-s3-us-east-1`), which follows the convention; D14's "one state per environment" is unchanged.
**Why.** Company convention for cost reporting, ownership and partner attribution. The product is still called Agent Hub; `fleet` is the project name in AWS.
**Revisit if.** The convention changes: names and tags are defined once in each root.

### D27. Shared AWS account: attribute and scope everything to fleet
**Decision (2026-09-29, Q10).** Agent Hub runs in `ml_account` (992382810653, us-east-1), a **member account of an AWS Organization** (management account 005151336112) that other projects also use. Consequences:
- **Budget** counts only costs tagged `Project=fleet` (`TagKeyValue` filter). It needs `Project` (and ideally `Owner`, `Environment`, `aws-apn-id`) **activated as cost allocation tags in the management account**; a member account can't do it. Until activation the budget sees $0, and tagged costs count only from activation onward.
- **Least privilege across projects:** the API may invoke only fleet's AgentCore runtimes, listed by exact ARN (`agent_runtime_arns`, no wildcard). The S3, Secrets Manager and ECR permissions were already scoped to fleet's own resources.
- **Model spend** (Bedrock, billed in this account) is attributed by invoking models through an **application inference profile tagged `Project=fleet`** in each fleet agent (step 8, issue #3).
**Why.** An account-wide budget alarmed on other projects' spend ($289.68 in September before fleet existed), and a wildcard IAM grant would have let the API call other teams' agents.
**Revisit if.** Fleet gets its own account: drop the tag filter and keep the explicit runtime list.

---

## 2. Networking (confirmed by the owner, 2026-09-29, Q3)

| Decision | Why | Cost of the alternative |
|---|---|---|
| Fargate tasks in **public subnets** with public IPs; security group allows inbound only from the ALB; **no NAT gateway** | The task must reach Neon, Google, AgentCore, Secrets Manager and ECR over the internet anyway; a NAT gateway is ~$33/month per AZ before data | Private subnets + NAT or VPC endpoints: more cost, no real gain while Neon is public |

## 3. Adopted amendments (P1–P8, accepted 2026-09-29)

These refine D1–D15 and are binding for the steps that follow.

**P1. Write the assistant message at stream start, checkpoint during it.** Saving only at stream end means a task crash, OOM or deploy mid-reply loses everything, and the "partial text saved on disconnect" path is the same code in a worse place. Proposal: insert the assistant row with `status = streaming` when the agent is called; update its blocks at block boundaries and at most every ~2 s; set `complete | stopped | interrupted | failed` at the end. The running task also writes `heartbeat_at` at every checkpoint and on its 15 s keep-alive tick; a sweep (on startup and every minute) marks `streaming` rows whose heartbeat is older than 60 s as `interrupted`. *(Amended 2026-09-29: "any row still streaming on startup" would also catch replies still running on the old task during a deploy.)* Same number of saves in the happy path plus a few cheap updates; D11's guarantees become crash-safe.

**P2. Deploys should drain, not cut.** Set the ALB target group's deregistration delay to ~300 s and the container's `stopTimeout` to the ECS maximum (120 s), and have the app stop accepting new streams on SIGTERM while finishing open ones. With rolling deploys (min healthy 100 %, max 200 %) most in-flight replies then finish. Replies longer than the drain window are still cut and saved as `interrupted`.

**P3. v1 has no stream resume; reload is the recovery.** `PRODUCT_PLAN.md` F08 mentions resuming from `Last-Event-ID`. With one task and no event buffer that isn't cheap. Proposal: events carry ids from day one (so resume can be added later), but in v1 a dropped stream means the client reloads the message from Postgres. Because the agent keeps running after a disconnect (D11), the client polls the message until its status leaves `streaming`, then renders it; Retry is offered for `stopped`, `failed` and `interrupted` (amended 2026-09-29; the design and `SEND_MESSAGE.md` table already allowed Retry after Stop). There is no "agent silent for 60 s" error: a long silence shows a soft "still working" note, because the run may well finish.

**P4. Stop is an explicit request, not just a closed connection.** The client can't distinguish its own abort from a network drop, and neither can the server. Proposal: `POST /v1/messages/{id}/stop` (the run id is the assistant message id) cancels the agent call and saves `stopped`; the client also aborts the fetch. A plain disconnect does not cancel (D11). The stop request sets `messages.cancel_requested_at`; the task running the reply checks it at each checkpoint (≤ 2 s) and on the keep-alive tick, so Stop works whichever task receives it (amended 2026-09-29: rolling deploys already run two tasks).

**P5. Extend the closed block set** to include `plan` and `status/error` now (P0 screens use them), and reserve `citation`, `chart`, `image`, `file`, `form` for P1 (D10).

**P6. `messages.blocks` is the transcript; side tables are indexes and state.** Step 4 lists `tool_calls`, `approval_requests` and `artifacts` beside a JSON `blocks` column. To avoid two sources of truth: the block holds what's rendered, the side table holds what must be queried or enforced (approval status and audit, artifact versions, tool timings), and the block references the row by id. Step 4 is designed this way.

**P7. One API task, no autoscaling in v1.** Keeps Stop, keep-alives and approval waits simple. Revisit when there's more than one user.

**P8. Approvals are P0 but depend on pausing a Strands run.** Long-running background tasks are out of v1, but F10 approvals still need the agent to wait for a human, possibly for minutes. The API owns approval state in Postgres and enforces it; *how* the agent pauses and resumes (Strands interrupt, re-invoke with the decision, AgentCore session idle limits) must be spiked before approvals are built. I've kept it out of step 8 (one agent, plain chat) and will spike it at the start of the approvals slice. *The API side is now decided (D19); the spike proves the agent side: that a Strands agent can end its turn on an approval request and resume correctly when re-invoked with the decision. Strands has this built in ("interrupts": a `BeforeToolCallEvent` hook calls `event.interrupt(...)`, the run returns with `stop_reason = "interrupt"`, and it resumes when invoked with an `interruptResponse`). Because agents are stateless (D18), the spike must decide where the paused state lives between the two calls: a Strands session manager on S3 keyed by our session id, or the API resending enough context.*

## 4. Open questions (answers pending)

Answered 2026-09-29: Q9 → Research Analyst v0 (`DELIVERY_PLAN.md` §2), Q2 → D25 (`fleet.qucoon.com`), Q3 → §2 (public subnets, no NAT), Q1 → D16 (Vite SPA), Q4 → D17 (dev only), Q5 → D11 (let the agent finish), Q6 → D18 (API sends history; AgentCore Memory later), Q7 → §3 (P1–P8 accepted). Still open:

| # | Question | Blocks | My default |
|---|---|---|---|
| ~~Q2~~ | **Answered → D25.** ~~Domain.~~ Which parent domain, is it in Route 53, and who issues TLS (ACM in us-east-1)? | ALB listener, Amplify custom domain, cookie domain, Google OAuth origins | Subdomains of your portfolio domain, ACM certificates, Route 53 if already there |
| Q8 | **Budget.** Is the $50/month AWS ceiling in the plan still right, excluding model tokens? | Task size, alarms | Yes |
| ~~Q10~~ | **Answered → D27 (shared `ml_account`).** ~~AWS account.~~ Is there a dedicated account (or at least credentials profile) for Agent Hub, and may I run read-only AWS CLI and `terraform plan` against it? | Step 7 | Ask again at step 7 |

## 5. Open items (known, not yet decided)

- The four `NS` records for `fleet` in the `qucoon.com` zone (another AWS account), added by whoever manages it once Terraform creates the delegated zone (D25).
- Google OAuth client: created by hand in Google Cloud console. Needs the app origin as an authorised JavaScript origin.
- Terraform state bucket: bootstrapped first, by a separate minimal config.
- Neon: created by hand; its pooled and direct connection strings go into Secrets Manager.
- Long-running background tasks: out of v1.
- ECS Express Mode: re-check docs before step 7 (D2).

## 6. Known risks

| Risk | Mitigation |
|---|---|
| Always-on cost (Fargate task, ALB, public IPv4) | Smallest task size, one env until v1 (D17), budget alarm |
| SSE through the ALB | Prove in step 8 with a long, slow reply and keep-alives; explicit idle timeout |
| Deploys and restarts cut in-flight replies | P1 checkpoints, P2 draining, client Retry |
| Neon resume delay after idle | Retry once on connect; consider disabling scale-to-zero on the primary branch |
| Real AgentCore stream format unknown | Record real output in step 8 before writing the translator |
| Approval pause/resume on AgentCore (P8) | Spike before building approvals |
| Neon pooler vs. asyncpg prepared statements | Verify driver settings in step 8 |
| Orphaned runs keep spending tokens after the user leaves (D11) | Per-run time cap; revisit if cost shows up |

## 7. Change log

| Date | Change |
|---|---|
| 2026-09-29 | v0.1: decisions D1–D15 recorded; proposals P1–P8 and questions Q1–Q10 raised. |
| 2026-09-29 | v0.2: Vite SPA (D16), dev only until v1 (D17), disconnect lets the agent finish with a time cap (D11), P1–P8 accepted. |
| 2026-09-29 | Architecture diagram added (`docs/diagrams/`, step 2). |
| 2026-09-29 | v0.3: D18, the API sends history on every call; AgentCore Memory recorded as a later, per-agent option. |
| 2026-09-29 | Send-message sequence diagrams and `SEND_MESSAGE.md` (step 3). Picked defaults: run id = assistant message id, idempotent sends via `clientMessageId`, refresh token 30 days. |
| 2026-09-29 | Data model, Postgres schema and first Alembic migration (step 4): `DATA_MODEL.md`, `api/app/db/models.py`, `api/migrations/`. |
| 2026-09-29 | v0.4, alignment review (build step 4b): D19 approval pause, D20 attachments to agents, D21 session titles, D22 polling for cross-session activity, D23 API conventions; D7 key prefix; D8 cookie path `/v1/auth`; D11, P1, P3, P4 amended for two tasks during deploys and Retry after Stop; D18 payload gains `attachments`. Migration `0002`. |
| 2026-09-29 | OpenAPI 3.1 spec (step 5): `api/openapi.yaml`. Stream events fixed as `run.started`, `block.started/delta/updated/completed`, `artifact.delta`, and the terminal `run.completed`, `run.awaiting_approval`, `run.stopped`, `run.failed`. |
| 2026-09-29 | Repo layout (step 6): D24. Root `README.md` maps the repo; root `Makefile` for common commands. |
| 2026-09-29 | Q3 answered: public subnets, ALB-only inbound, no NAT gateway (§2 confirmed). Q10: account exists; the owner sets up access at step 7. |
| 2026-09-29 | Q2 answered: D25, `fleet.programmeos.com` (app) and `api.fleet.programmeos.com` (API), subdomain delegated from GoDaddy to Route 53; refresh cookie made host-only. |
| 2026-09-29 | Step 7: Terraform written (`infra/`); D2 Express Mode re-check recorded. Budget alarm at $50 (Q8 default) when an alert email is set. |
| 2026-09-29 | D2: cheaper alternatives to the ALB weighed; ALB kept behind `enable_api` (off until step 8). |
| 2026-09-29 | Domain changed to `fleet.qucoon.com` (D25; `qucoon.com` is on Route 53 in another account). D26: naming convention and required tags; `Owner` and `aws-apn-id` values kept out of git. |
| 2026-09-29 | D27: shared member account; budget filtered to `Project=fleet` (needs tag activation in the management account); API runtime access by exact ARN only. |
| 2026-09-30 | Agent repos confirmed as `fleet-agent-<slug>`, one per agent (D24). P8 spike refined with Strands interrupts. Agent development standard written (personal, project-neutral). |
| 2026-09-30 | The standard moved to its own template repository, `IsraelBO17/agent-standard` (private); Agent Hub keeps only its profile, `docs/AGENT_PROFILE.md`. |
| 2026-09-30 | Step 8 (issue #3): Research Analyst v0's AgentCore stream recorded (`api/tests/fixtures/agentcore/`); the agent sends plain JSON frames ending in `result`. Closing the response stream, and `StopRuntimeSession`, do not stop a run: Stop needs a cancel signal in the agent (SEND_MESSAGE "Verified"). |
