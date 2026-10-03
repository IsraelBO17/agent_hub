# Changelog

One line per released version (standard §20).

- 0.1.0: the API shell (issue #5): settings, errors, request ids, health, database pool, jobs, Docker; from the api-standard template (standard 1.1).
- 0.2.0: auth (issue #6, API half): Google sign-in, refresh rotation with reuse detection, logout, `/v1/me`, the invite command (standard 1.2).
- 0.3.0: agents (issue #7, API half): `GET /v1/agents`, `GET /v1/agents/{slug}` with `myStats`; the `hub` operator CLI (`hub agents add|list`, `hub users invite`); `getAgent` documents `422` for a malformed slug.
- 0.4.0: chat (issue #8, API half): `POST /v1/agents/{slug}/sessions` and `POST /v1/sessions/{id}/messages` stream the reply (SSE) from Research Analyst on AgentCore; the run outlives the request, checkpoints, heartbeats and is swept when its task dies; `GET /v1/messages/{id}`, `GET /v1/sessions/{id}/messages`; the translator is tested against the recorded AgentCore streams. Contract: `422` on the two GETs, `shutting_down` on the sends' `503`.
- 0.5.0: Stop (issue #9, API half): `POST /v1/messages/{id}/stop` sets the cancel flag; the run picks it up within about 2 s from any task, sends `AgentCancel` on the same runtime session, keeps the partial reply and ends with `run.stopped`. The run cap and shutdown also cancel the agent; the sweep saves a dead run that was being stopped as `stopped`. Contract: `422` on `stopReply`.
