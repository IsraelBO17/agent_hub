# Agent Hub: architecture decisions

| | |
|---|---|
| Status | v0.2, D1–D17 and P1–P8 locked; §2 default and §4 questions still open |
| Date | 2026-09-29 |
| Owner | Israel B. (approver) |
| Scope | Back end, infrastructure, auth, data and the agent stream. Product scope stays in `PRODUCT_PLAN.md`. |

This file is the single source of truth for technical decisions. When a decision changes, edit it here and add a line to the change log (§7).

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
**ECS Express Mode.** Not the default: one independent write-up reports no control over the load balancer settings SSE needs. A quick search on 2026-09-29 found nothing in AWS docs either way. Re-check the current Express Mode docs before step 7 and record the result here.
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
**Gap to close:** how the agent gets prior turns; see Q6.

### D5. Streaming: SSE over a `fetch` POST
**Decision.** `POST /sessions/{id}/messages` returns `text/event-stream`. The client reads it with `fetch` and a stream reader, not `EventSource` (which can't send an `Authorization` header or a body). The API writes a keep-alive comment (`: ping`) every 15 s from its own task, independent of the agent. The ALB idle timeout is set explicitly (300 s proposed) rather than relying on the 60 s default.
**Why.** SSE is plain HTTP, passes the ALB, and is enough for one-way streaming; the client never needs to push mid-stream (Stop is a separate request, see P4).
**Revisit if.** SSE fails through the ALB in the step 8 proof, or we need bidirectional traffic (then WebSockets on the same ALB).

### D6. Agents are rows in an `agents` table
**Decision.** Name, slug, description, icon, colour, stage, status, runtime type, runtime ARN or endpoint, capabilities, starters, disclaimer and tool list are columns (capabilities and tools as JSON). Adding an agent is an insert, done by a small CLI or SQL seed in v1 (the Add-agent UI is P2).
**Why.** J1: shipping an agent is the only work. No code change in the API or UI.
**Revisit if.** An agent needs behaviour the descriptor can't express; extend the descriptor, never special-case an agent id.

### D7. Files in S3, metadata in Postgres
**Decision.** Uploads and artifact files live in one private S3 bucket. Postgres holds metadata and ownership. The browser uploads with a short-lived presigned PUT (or POST with size and type conditions) and downloads with a short-lived presigned GET. The API checks ownership before signing.
**Why.** Keeps large bodies off the API task; S3 handles size, durability and range requests.
**Note.** The bucket needs a CORS rule for the app origin. HTML artifacts are served from a separate origin for the sandbox (F09); that origin is decided in step 9 with artifacts.
**Revisit if.** We need virus scanning or image processing on upload (add an S3 event, not a proxy).

### D8. Auth: Google sign-in, then the API's own session
**Decision.** The browser gets a Google ID token (Google Identity Services) and posts it once to `POST /auth/google`. The API verifies signature (Google JWKS), `aud` (our client ID), `iss`, `exp` and `email_verified`, looks the user up by Google `sub`, and rejects unknown or inactive users. It then issues:
- a short-lived **access token** (JWT, ~15 min, signed with the session key from Secrets Manager), held in memory by the client and sent as `Authorization: Bearer`;
- a rotating **refresh token** (random, stored hashed in `refresh_tokens`) in a cookie: `HttpOnly; Secure; SameSite=Strict; Domain=api.<domain>; Path=/auth`.
Refresh rotates the token and detects reuse (reuse of an old token revokes the whole family). App (`app.`) and API (`api.`) share a parent domain, so the cookie is same-site; CORS allows only the app origin with credentials, and `/auth/*` also checks `Origin`.
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
**Revisit if.** Model cost from orphaned runs becomes noticeable (lower the cap, or cancel after N minutes with no client attached).

### D12. Region: us-east-1
Compute, S3, AgentCore, Secrets Manager, Amplify and Neon all in us-east-1. **Revisit if** a model or AgentCore feature we need isn't there.

### D13. Front-end hosting: AWS Amplify Hosting
**Decision.** Amplify Hosting serves the web app on `app.<domain>`, same parent domain as the API.
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

---

## 2. Unconfirmed defaults (do not build on these until confirmed; see Q3)

| Default | Why it's the default | Cost of the alternative |
|---|---|---|
| Fargate tasks in **public subnets** with public IPs; security group allows inbound only from the ALB; **no NAT gateway** | The task must reach Neon, Google, AgentCore, Secrets Manager and ECR over the internet anyway; a NAT gateway is ~$33/month per AZ before data | Private subnets + NAT or VPC endpoints: more cost, no real gain while Neon is public |

## 3. Adopted amendments (P1–P8, accepted 2026-09-29)

These refine D1–D15 and are binding for the steps that follow.

**P1. Write the assistant message at stream start, checkpoint during it.** Saving only at stream end means a task crash, OOM or deploy mid-reply loses everything, and the "partial text saved on disconnect" path is the same code in a worse place. Proposal: insert the assistant row with `status = streaming` when the agent is called; update its blocks at block boundaries and at most every ~2 s; set `complete | stopped | interrupted | failed` at the end. On startup, any row still `streaming` becomes `interrupted`. Same number of saves in the happy path plus a few cheap updates; D11's guarantees become crash-safe.

**P2. Deploys should drain, not cut.** Set the ALB target group's deregistration delay to ~300 s and the container's `stopTimeout` to the ECS maximum (120 s), and have the app stop accepting new streams on SIGTERM while finishing open ones. With rolling deploys (min healthy 100 %, max 200 %) most in-flight replies then finish. Replies longer than the drain window are still cut and saved as `interrupted`.

**P3. v1 has no stream resume; reload is the recovery.** `PRODUCT_PLAN.md` F08 mentions resuming from `Last-Event-ID`. With one task and no event buffer that isn't cheap. Proposal: events carry ids from day one (so resume can be added later), but in v1 a dropped stream means the client reloads the message from Postgres. Because the agent keeps running after a disconnect (D11), the client polls the message until its status leaves `streaming`, then renders it; Retry is offered only for `failed` or `interrupted`.

**P4. Stop is an explicit request, not just a closed connection.** The client can't distinguish its own abort from a network drop, and neither can the server. Proposal: `POST /sessions/{id}/runs/{runId}/stop` cancels the agent call and saves `stopped`; the client also aborts the fetch. A plain disconnect does not cancel (D11). With one task this needs no shared state; with more tasks later it needs a cancel flag in Postgres.

**P5. Extend the closed block set** to include `plan` and `status/error` now (P0 screens use them), and reserve `citation`, `chart`, `image`, `file`, `form` for P1 (D10).

**P6. `messages.blocks` is the transcript; side tables are indexes and state.** Step 4 lists `tool_calls`, `approval_requests` and `artifacts` beside a JSON `blocks` column. To avoid two sources of truth: the block holds what's rendered, the side table holds what must be queried or enforced (approval status and audit, artifact versions, tool timings), and the block references the row by id. Step 4 is designed this way.

**P7. One API task, no autoscaling in v1.** Keeps Stop, keep-alives and approval waits simple. Revisit when there's more than one user.

**P8. Approvals are P0 but depend on pausing a Strands run.** Long-running background tasks are out of v1, but F10 approvals still need the agent to wait for a human, possibly for minutes. The API owns approval state in Postgres and enforces it; *how* the agent pauses and resumes (Strands interrupt, re-invoke with the decision, AgentCore session idle limits) must be spiked before approvals are built. I've kept it out of step 8 (one agent, plain chat) and will spike it at the start of the approvals slice.

## 4. Open questions (answers pending)

Answered 2026-09-29: Q1 → D16 (Vite SPA), Q4 → D17 (dev only), Q5 → D11 (let the agent finish), Q7 → §3 (P1–P8 accepted). Still open:

| # | Question | Blocks | My default |
|---|---|---|---|
| Q2 | **Domain.** Which parent domain, is it in Route 53, and who issues TLS (ACM in us-east-1)? | ALB listener, Amplify custom domain, cookie domain, Google OAuth origins | Subdomains of your portfolio domain, ACM certificates, Route 53 if already there |
| Q3 | **Networking.** Accept public subnets, public IP, ALB-only inbound, no NAT? | Step 7 | Yes |
| Q6 | **Where the agent's conversation context comes from.** AgentCore keeps state only while its runtime session is alive (idle timeout); after that, the agent forgets. Options: (a) the API sends recent history in every invocation payload, from Postgres; (b) agents use AgentCore Memory; (c) rely on the runtime session and accept forgetting. | Agent contract, step 8 | (a): the API sends history; agents stay stateless and interchangeable |
| Q8 | **Budget.** Is the $50/month AWS ceiling in the plan still right, excluding model tokens? | Task size, alarms | Yes |
| Q9 | **First real agent for step 8.** Research Analyst (the plan's pick), or an agent you already have deployed on AgentCore? An existing one is faster. Is there one, and can the API's IAM role invoke it? | Step 8 | An existing deployed agent, if any |
| Q10 | **AWS account.** Is there a dedicated account (or at least credentials profile) for Agent Hub, and may I run read-only AWS CLI and `terraform plan` against it? | Step 7 | Ask again at step 7 |

## 5. Open items (known, not yet decided)

- Domain and TLS certificate (Q2).
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
