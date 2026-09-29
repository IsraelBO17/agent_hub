# Agent Hub

One web app that is a single chat interface for many AI agents (Strands agents on Amazon Bedrock AgentCore Runtime, LangGraph later). Agents are data: adding one never needs a UI change.

**Status:** planning and foundations. Done so far: decisions, diagrams, database schema, and the API contract. Next: Terraform (step 7), then the first end-to-end slice (step 8). See [`docs/BUILD_PLAN.md`](docs/BUILD_PLAN.md).

## Layout

One repository, one folder per deployable part (ARCHITECTURE D24). Each folder uses its own language's tools; there is no monorepo tooling on top.

```
agent_hub/
├── api/            FastAPI service (Python 3.12, uv). ECS Fargate behind an ALB.
│   ├── openapi.yaml    The API contract. The API implements it; web/ generates its types from it.
│   ├── app/            Application code (today: db/models.py)
│   ├── migrations/     Alembic migrations
│   └── tests/
├── web/            Vite + React + TypeScript SPA (npm). Amplify Hosting.        (created in step 8)
├── infra/          Terraform (D14).                                           (created in step 7)
│   ├── bootstrap/      State bucket, applied once by hand
│   ├── modules/        network, ecr, service, alb, s3, secrets, amplify
│   └── envs/dev/       The only environment until v1 (D17)
├── agents/         Agent descriptors, one YAML per agent; the registry CLI     (created in step 8)
│                   inserts them. Agent code lives in each agent's own repo.
├── design/         Pencil design file, generated index, index tool
├── docs/           Plan, decisions, flows, data model, diagrams
└── Makefile        Shortcuts for the commands below
```

Adding an agent touches only `agents/` (and the `agents` table), never `web/` or `api/`.

## Where to read

| Need | Look at |
|---|---|
| Build steps, status, open questions | [`docs/BUILD_PLAN.md`](docs/BUILD_PLAN.md) |
| Why a technical choice was made | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Endpoints, errors, stream events, blocks | [`api/openapi.yaml`](api/openapi.yaml) |
| Send and stream flow, statuses, timers | [`docs/SEND_MESSAGE.md`](docs/SEND_MESSAGE.md) |
| Tables and enforced rules | [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) |
| Scope and acceptance criteria | [`docs/PRODUCT_PLAN.md`](docs/PRODUCT_PLAN.md) |
| Screens and components | [`design/README.md`](design/README.md), [`design/INDEX.md`](design/INDEX.md) |

## Commands

Needs Docker, [uv](https://docs.astral.sh/uv/) and Node (for `npx`). Run `make` to list them.

```bash
make db-up
```

```bash
make api-test
```

```bash
make contract-lint
```
