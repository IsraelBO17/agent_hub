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
| 4b | **Alignment review.** Check screens, data model, stream and flows against each other before the API contract; fix blockers, record the owner's decisions. | ✅ Done | ARCHITECTURE D19–D23, migration `0002`, [`diagrams/approval-and-upload.mmd`](diagrams/approval-and-upload.mmd), design fixes in `fleet_dev.pen`. The review doc was removed once the spec covered it (git history: `docs/ALIGNMENT_REVIEW.md` at `63b0ca7`); its open items are under "Follow-ups" below. |
| 5 | **OpenAPI spec.** OpenAPI 3.1 covering auth, agents, sessions, messages, streaming (the SSE event schema defined precisely, including all block types), uploads and artifacts (signed URLs), feedback and errors. Then connect the front end to it through a single API client layer. | ✅ Spec done; client layer waits for the front end | [`api/openapi.yaml`](../api/openapi.yaml) (lint: `npx @redocly/cli lint api/openapi.yaml`; TypeScript types: `npx openapi-typescript api/openapi.yaml`). The typed client module is written when the Vite app is created. |
| 6 | **Repo layout.** Propose a simple monorepo (`web/`, `api/`, `infra/`, `docs/`) fitted to what's already here, without breaking the existing front end. | ✅ Done | ARCHITECTURE D24; layout in the root [`README.md`](../README.md); root `Makefile`. `web/`, `infra/` and `agents/` are created by the steps that fill them. |
| 7 | **Terraform foundation (dev first).** State bucket bootstrap, network, ECR, ECS cluster and service, ALB with the explicit idle timeout, S3 bucket, Secrets Manager entries, IAM roles, Amplify app. Show `terraform plan` output before any apply. Re-check ECS Express Mode docs first (D2). | 🔄 Code written and validated; plans and applies pending | [`infra/`](../infra/README.md): bootstrap (state bucket, Route 53 zone), `envs/dev`, 7 modules. `make infra-validate`, `make infra-plan`. |
| 8 | **First end-to-end slice with ONE real agent.** Google sign-in, load the agent from the `agents` table, send a message, stream the reply from the real AgentCore runtime through the ALB, save the history, reload it in the real UI. Deployed to dev. Must prove SSE works through the ALB with keep-alives, and must record what the AgentCore runtime actually emits so the translator (D10) is written against real output. Also verify: Stop actually stops the run on AgentCore; Neon pooler vs. driver prepared statements. | ⬜ = milestone **M1** (30 Sep – 16 Oct) | [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md) §3; GitHub issues #2–#10 |
| 9 | **Remaining features, one small slice at a time:** agent catalog and sessions CRUD from the database, Stop generation, tool-call steps, artifacts and uploads, questions and approvals (spike the approval pause/resume first, P8), feedback, share links, invite flow for more users, optional AgentCore Memory, CI/CD, logging and monitoring. Later: mobile screens. | ⬜ = milestones **M2–M4** (to v1 on 18 Dec) | [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md) §3; issues written at each milestone's start |

## Follow-ups (from the alignment review, for their feature slices)

| Item | When | What |
|---|---|---|
| Share options | F18 (P1) | Add `share_links.options jsonb` (`includeToolCalls`) and a unique partial index for one active link per session; `api/openapi.yaml` already assumes both. |
| Regenerate siblings | F20 second half (P1) | Add `messages.superseded_at`; Regenerate only the latest reply so `seq` stays linear; history (D18) sends only the shown sibling. Then add the regenerate operation to the spec. |
| Feedback trace id | F20 (P1) | The popover says "Sent with this session's trace ID": store `messages.trace_id` if AgentCore exposes one, or drop the line. |
| Export all | F24 (P1) | Needs a background job; output is a `files` row (`purpose = export`). Session export is Markdown only (F27, in the spec). |
| Multi-user | Invite flow (step 9) | Add `users.role` (who may invite users and register agents); per-user "Always allow" tool rules come with the P2 permission prompt. |
| HTML preview origin | Artifacts slice | D7: sandboxed iframe without `allow-same-origin` is the default; decide whether a separate origin is still needed. |

## Open questions (owner to answer)

Kept current in [`ARCHITECTURE.md` §4](ARCHITECTURE.md#4-open-questions-answers-pending). As of 2026-09-29 these are still open:

- **Q8 Budget:** is $50/month AWS (excluding model tokens) still the ceiling?
- **Cost allocation tags:** ask the organization's management account (005151336112) to activate `Project`, `Owner`, `Environment` and `aws-apn-id` as cost allocation tags, so fleet's budget and Cost Explorer can see fleet's spend (D27).

## Where things are

| Need | Look at |
|---|---|
| Why a technical choice was made | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Milestones, dates, what's next, tracking | [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md), GitHub milestones and the pinned Weekly status issue |
| Product scope, acceptance criteria, screen list | [`PRODUCT_PLAN.md`](PRODUCT_PLAN.md) |
| The send / stream flow, statuses, timers, error codes | [`SEND_MESSAGE.md`](SEND_MESSAGE.md) |
| Tables, enforced rules, indexes | [`DATA_MODEL.md`](DATA_MODEL.md) |
| Diagrams | [`diagrams/`](diagrams/) |
| Chart rendering rules | [`CHART_SPEC.md`](CHART_SPEC.md) |
| Screens and components | `design/INDEX.md`, `design/fleet_dev.pen` |
| Schema code and how to run it | [`api/README.md`](../api/README.md) |

Update the status column and the open questions whenever a step finishes.
