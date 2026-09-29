# Build plan

The ordered steps for building Agent Hub, their status, and how we work. Start any new session here, then read [`ARCHITECTURE.md`](ARCHITECTURE.md) (decisions) and the docs linked from each finished step.

## How we work

- **One step at a time.** At the end of each step, show the result and wait for the owner's approval before starting the next.
- **Ask when a decision is the owner's; don't guess.** Otherwise pick the simple option, say what was picked, and continue. Record picked defaults in the step's doc and in the `ARCHITECTURE.md` change log.
- **Don't re-open a decision in `ARCHITECTURE.md`** without saying why. That file is the single source of truth for decisions; update it whenever something changes.
- **Small, reviewable changes.** Run and test what you build, and say what couldn't be verified.
- **Diagrams:** Mermaid source in `docs/diagrams/` plus a rendered PNG (see [`diagrams/README.md`](diagrams/README.md)).
- **Never commit secrets.** Never run `terraform apply`, or anything that costs money or changes AWS, without showing the plan and getting a yes.
- **Git:** commit each finished step to `main` with a clear message. Don't push unless asked.
- **Design changes** happen in a separate design session: write a self-contained prompt for it rather than editing `design/fleet_dev.pen` here.

## Steps

| # | Step | Status | Output |
|---|---|---|---|
| 1 | **Inspect the repo, lock the decisions.** Report what exists, write the decision log, challenge weak points, ask the owner's questions in one batch. | ✅ Done | [`ARCHITECTURE.md`](ARCHITECTURE.md) (D1–D18, P1–P8) |
| 2 | **Architecture diagram**, kept in sync with the decisions. | ✅ Done | [`diagrams/architecture.mmd`](diagrams/architecture.mmd) + PNG |
| 3 | **Sequence diagram: "user sends a message".** Sign-in and session check, saving the user message, calling the AgentCore runtime, translating and streaming events, keep-alives, saving the assistant message; failure paths: Stop, browser disconnect, agent error, expired session, agent offline. | ✅ Done | [`SEND_MESSAGE.md`](SEND_MESSAGE.md), [`diagrams/send-message.mmd`](diagrams/send-message.mmd), [`diagrams/send-message-failures.mmd`](diagrams/send-message-failures.mmd) + PNGs |
| 4 | **ER diagram and Postgres schema.** `users`, `refresh_tokens`, `agents`, `sessions`, `messages` (ordered typed blocks in one JSON column), `artifacts`, `artifact_versions`, `files`, `tool_calls`, `approval_requests`, `feedback`, `share_links`. `user_id` on every user-owned table, indexes for history listing and reload, Alembic migrations. Check against the screens for missing data. | ✅ Done | [`DATA_MODEL.md`](DATA_MODEL.md), [`diagrams/er.mmd`](diagrams/er.mmd) + PNG, `api/app/db/models.py`, `api/migrations/`, `api/tests/` |
| 5 | **OpenAPI spec.** OpenAPI 3.1 covering auth, agents, sessions, messages, streaming (the SSE event schema defined precisely, including all block types), uploads and artifacts (signed URLs), feedback and errors. Then connect the front end to it through a single API client layer. | ⏭ Next | (There is no front-end code yet; the plan is to write the typed client module on its own and wire it in when the Vite app is created. Awaiting the owner's go-ahead.) |
| 6 | **Repo layout.** Propose a simple monorepo (`web/`, `api/`, `infra/`, `docs/`) fitted to what's already here, without breaking the existing front end. | ⬜ | |
| 7 | **Terraform foundation (dev first).** State bucket bootstrap, network, ECR, ECS cluster and service, ALB with the explicit idle timeout, S3 bucket, Secrets Manager entries, IAM roles, Amplify app. Show `terraform plan` output before any apply. Re-check ECS Express Mode docs first (D2). | ⬜ | |
| 8 | **First end-to-end slice with ONE real agent.** Google sign-in, load the agent from the `agents` table, send a message, stream the reply from the real AgentCore runtime through the ALB, save the history, reload it in the real UI. Deployed to dev. Must prove SSE works through the ALB with keep-alives, and must record what the AgentCore runtime actually emits so the translator (D10) is written against real output. Also verify: Stop actually stops the run on AgentCore; Neon pooler vs. driver prepared statements. | ⬜ | |
| 9 | **Remaining features, one small slice at a time:** agent catalog and sessions CRUD from the database, Stop generation, tool-call steps, artifacts and uploads, questions and approvals (spike the approval pause/resume first, P8), feedback, share links, invite flow for more users, optional AgentCore Memory, CI/CD, logging and monitoring. Later: mobile screens. | ⬜ | |

## Open questions (owner to answer)

Kept current in [`ARCHITECTURE.md` §4](ARCHITECTURE.md#4-open-questions-answers-pending). As of 2026-09-29 these are still open:

- **Q2 Domain:** which parent domain; is it in Route 53; certificates from ACM? (Needed by step 7.)
- **Q3 Networking:** public subnets with public IPs, inbound from the ALB only, no NAT gateway? (Step 7.)
- **Q8 Budget:** is $50/month AWS (excluding model tokens) still the ceiling?
- **Q9 First agent:** is there an agent already deployed on AgentCore to use in step 8?
- **Q10 AWS account:** which account or CLI profile; may read-only commands and `terraform plan` run against it? (Step 7.)

## Where things are

| Need | Look at |
|---|---|
| Why a technical choice was made | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Product scope, acceptance criteria, screen list | [`PRODUCT_PLAN.md`](PRODUCT_PLAN.md) |
| The send / stream flow, statuses, timers, error codes | [`SEND_MESSAGE.md`](SEND_MESSAGE.md) |
| Tables, enforced rules, indexes | [`DATA_MODEL.md`](DATA_MODEL.md) |
| Diagrams | [`diagrams/`](diagrams/) |
| Chart rendering rules | [`CHART_SPEC.md`](CHART_SPEC.md) |
| Screens and components | `design/INDEX.md`, `design/fleet_dev.pen` |
| Schema code and how to run it | [`api/README.md`](../api/README.md) |

Update the status column and the open questions whenever a step finishes.
