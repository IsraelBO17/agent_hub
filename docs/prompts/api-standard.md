I want a personal **API (backend) standard**, the same way I have one for agents, and then I want Agent Hub's API built to it. Two phases, in order. Stop for my approval at every step marked ⏸.

# Purpose: why this standard exists
The standard is how I build **any** backend project, Agent Hub or something entirely different, **quickly and consistently with AI coding agents like Claude Code**. When someone asks me for a backend system, I start a repo from the template, and a coding agent builds it by following the standard, with me approving decisions. So the standard's main reader is a coding agent. It MUST give the agent:
- **Rules it can't miss:** a `CLAUDE.md` in the template (so every generated repo carries its conventions, commands and "never do" list), pointing to `docs/STANDARD.md`.
- **Recipes, not just rules:** step-by-step playbooks in `docs/RECIPES.md` for the common tasks (start a new API from a spec, add a resource end to end (contract → model → migration → repository → service → route → tests), add auth, add a background job or stream, add an integration, deploy), each ending with how to verify it.
- **Defaults for every decision,** so the agent asks only what's genuinely specific to the project.
- **An intake spec** (`SPEC.md` template, like the agent standard's): what to capture with me before any code, and the order of work from spec to deployed.
- **A golden path:** one fully working example feature in the template that shows every pattern once, for the agent to copy.
- **One self-check command** (`make check`: lint, types, tests, contract checks) the agent runs before saying it's done.
- **Claude Code skills** for the recipes (e.g. `/new-api`, `/add-resource`, `/add-migration`, `/add-auth`), in the template's `.claude/skills/`, so they're one command away in every generated repo.
Keep `STANDARD.md` short and unambiguous (rules and defaults), put the how-to in the recipes, and write both so a coding agent can follow them literally.

# Context you must know
- I already have an **Agent Development Standard**: `../agent-standard` (a GitHub template repo, `IsraelBO17/agent-standard`). Read `../agent-standard/docs/STANDARD.md` and `README.md` first. The API standard must follow the **same shape**: a project-neutral `docs/STANDARD.md` with MUST/SHOULD/MAY, numbered sections, a default stack with documented exceptions, a lifecycle and Definition of Done, profiles kept in each project's repo, appendices with templates and reference code; plus a **template repository** whose skeleton actually runs (lint clean, tests green, CI) and a README block explaining how to start a new repo from it. Keep the two standards consistent where they overlap: errors, config and secrets, observability, IaC, tags, versioning.
- The project it will first be used for: **Agent Hub** (this repo, `agent_hub`). One FastAPI service on ECS Fargate behind an ALB, Neon Postgres, SSE streaming, Google sign-in plus its own session, AWS us-east-1, Terraform. Decisions: `docs/ARCHITECTURE.md` (D1–D27, P1–P8). Contract: `api/openapi.yaml`. Existing code: `api/` (SQLAlchemy 2 models, Alembic migrations, schema tests, `uv`). Build order and issues: `docs/DELIVERY_PLAN.md`, GitHub issue IsraelBO17/agent_hub#5.

# REFERENCE REPOS (my existing APIs, to learn from)
<!-- Fill in: path or GitHub URL, and what it's a good (or bad) example of. -->
- …
- …
If this list is empty or unclear, ask me before anything else.

# Phase 1: Determine the API standard

**Keep the standard project-neutral.** Agent Hub is the *first project* the standard will be used on and a useful test case, not the source of its rules. The standard and its template MUST NOT contain Agent Hub specifics: no AWS account or profile, domain, resource names, tag keys or values, issue numbers, or decision numbers. Where the standard needs such a value, it says "set by the project profile" (as `agent-standard` §18 does), and the Agent Hub values go only into the profile in step 7. Generic practices that Agent Hub also uses (IaC, required tags, a naming convention, a secrets manager) belong in the standard as rules without the values.
1. **Study the references.** Read each reference repo and extract how it handles: project layout and layering; configuration and secrets; API design (contract-first or code-first, versioning, naming, pagination, errors, idempotency, request IDs); auth and authorization; data access, transactions and migrations; background work and streaming; logging, tracing and metrics; testing (unit, integration against a real database, contract tests against OpenAPI); security (OWASP API Top 10, input validation, CORS, rate limits, dependency scanning); performance; Docker, deployment and IaC; CI; release and versioning; documentation. Report a short table per topic: what each repo does, what's worth keeping, what to drop, and where they conflict. Also say where Agent Hub's decisions (`docs/ARCHITECTURE.md`) already settle a topic. ⏸
2. **Ask me the open decisions in one batch,** each with 2–3 options and your recommendation. At least: the default stack (I expect Python 3.12, uv, FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, Postgres; confirm or challenge it from the references), layering (e.g. routes → services → repositories), contract-first versus code-first OpenAPI, the async driver, the logging and tracing stack, and the test layout. ⏸
3. **Write `docs/STANDARD.md`** in a new sibling repo `../api-standard` (v1.0, owner Boluwatife Israel). Principles, default stack, lifecycle and gates, layout, the topics above as numbered sections, Definition of Done, profiles section, appendices (templates and reference code). Every code example checked against current library docs. ⏸
4. **Build the template skeleton** in `../api-standard`: runnable service (health endpoint, settings, RFC 9457 errors, request-ID middleware, DB session handling, one example resource end to end with a migration), tests (unit plus integration against Postgres in Docker), Dockerfile (arm64, non-root), CI workflow, `infra/` notes, a README "start a new API" checklist, and the agent-facing pieces from Purpose (`CLAUDE.md`, `docs/RECIPES.md`, the `SPEC.md` intake template, `.claude/skills/`, `make check`). Lint clean, tests green. ⏸
5. **Prove it's reusable:** in a scratch folder, start a small unrelated API (for example a bookmarks or inventory service: two resources, auth, one migration) from the template and build it by following only `CLAUDE.md`, the recipes and the skills, as a fresh coding agent would. Report every question you had to ask, every guess, and every place the standard was silent or Agent Hub-shaped, then fix the standard and template. Throw the sample away. ⏸
6. **Publish it:** create `IsraelBO17/api-standard` as a **private template repository** (`gh repo create … --private`, then `gh repo edit --template`), commit and push. ⏸
7. **Agent Hub profile:** write `agent_hub/docs/API_PROFILE.md` (the project-specific rules on top of the standard: contract `api/openapi.yaml`, AWS names and tags D26/D27, Neon specifics D3, SSE rules from `docs/SEND_MESSAGE.md`, and so on). Point `CLAUDE.md` and `docs/ARCHITECTURE.md` at it. ⏸

# Phase 2: Build Agent Hub's API layer with the standard (issue #5)
Work on a branch `api-shell` in `agent_hub`; finish with a pull request.
Build it **the way any future project would be built**: from the template, following `CLAUDE.md`, the recipes and the skills. Where they fall short, fix the standard (in its repo, with a version bump) rather than working around it here.
1. **Map the gap:** compare `agent_hub/api/` with the standard's layout and say what moves and what stays. The models, migrations and schema tests must keep working. ⏸
2. **Build issue #5's scope to the standard** (read `gh issue view 5 --repo IsraelBO17/agent_hub`):
   - FastAPI app with settings from environment (ECS injects `DATABASE_URL`, `DATABASE_URL_DIRECT`, `SESSION_SIGNING_KEY` from Secrets Manager; plus `APP_ORIGIN`, `FILES_BUCKET`, `GOOGLE_CLIENT_ID`, `AWS_REGION`, `PORT`), CORS for `APP_ORIGIN` only, `X-Request-Id`, and the contract's `Problem`/`ErrorCode` errors.
   - `GET /v1/health` with no database call.
   - An async pool on Neon's **pooled** string, with the D3 question answered by a real test: does the driver work through Neon's transaction-mode pooler (prepared statements)? Write the answer into D3.
   - Dockerfile (arm64). SIGTERM: a graceful shutdown hook (P2).
   - Tests; `make db-up`, `make api-test` and `make contract-lint` stay green.
   ⏸
3. **Deploy:** push the image to ECR `fleet-dev-api-ecr-us-east-1` (tagged with the git SHA). Set `enable_api = true`, `api_desired_count = 1`, `api_image_tag`, and `agent_runtime_arns = ["arn:aws:bedrock-agentcore:us-east-1:992382810653:runtime/fleet_dev_research_analyst_runtime_us_east_1-J5QFpm41XD"]`, kept in a committed file (ARNs aren't secret), not the gitignored tfvars. Show me the Terraform plan and apply only on my yes. ⏸
4. **Close out:** `https://api.fleet.qucoon.com/v1/health` returns 200 through the ALB; tick issue #5's items; comment with results; open the PR.

Out of scope for #5: auth (#6), agents and the CLI (#7), send and stream (#8), Stop (#9). Don't design against them. For example, Stop will set `messages.cancel_requested_at`, then the task running the reply sends `AgentCancel` on the same runtime session.

# Rules

## General (both phases)
- Check current docs (FastAPI, Pydantic, SQLAlchemy, the driver, uv, AWS provider) before relying on an API. When a reference repo and current best practice disagree, say so and recommend.
- Never commit secrets. Never create billable cloud resources without showing me the plan and getting a yes.
- The new standard repo (`../api-standard`) may use `main`. Don't commit to agent_hub's `main`: use the branch named in Phase 2.
- Nothing below this line belongs in the standard or its template.

## Agent Hub only (Phase 1 step 7, the profile, and Phase 2)
- AWS profile `ml_account` (account 992382810653, us-east-1), **shared with other projects** (D27). Names `fleet-dev-<component>-<type>-us-east-1`; tag values live in the gitignored `infra/envs/dev/terraform.tfvars` and are never committed (agent_hub is public).
- **Dependency:** `enable_api = true` needs the ALB certificate for `api.fleet.qucoon.com`, which validates only once the `fleet` NS record exists in the qucoon.com zone. Check `dig +short NS fleet.qucoon.com`. If it's empty, finish everything else, show me the plan, and stop before applying.
- Agent Hub's Terraform is in `infra/` (`make infra-validate`, `make infra-plan`); apply only after I've seen the plan. Use the Makefile targets (`make db-up`, `make api-test`, `make contract-lint`).
