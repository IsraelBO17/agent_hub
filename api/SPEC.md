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

## 5–8. Non-functional needs, integrations, background work, deployment
See the profile and ARCHITECTURE: one user in v1 (D9), AgentCore runtimes by exact ARN (D27), Neon Postgres (D3), ECS Fargate behind an ALB (D2), the worker inside the API task (P7).

## 9. Open questions
Tracked in ARCHITECTURE §4 and §5.
