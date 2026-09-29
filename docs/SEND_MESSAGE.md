# Sending a message: flow, states and timers

Step 3 of the build plan. Diagrams:
- Normal path, including sign-in and the session check: [`diagrams/send-message.mmd`](diagrams/send-message.mmd) ([PNG](diagrams/send-message.png))
- Failure paths: [`diagrams/send-message-failures.mmd`](diagrams/send-message-failures.mmd) ([PNG](diagrams/send-message-failures.png))

Decisions behind this are in [`ARCHITECTURE.md`](ARCHITECTURE.md) (D5, D8, D10, D11, D18, P1–P4). Endpoint paths and event names here are **provisional**; step 5 (OpenAPI) fixes them.

## Rules

1. **Save before calling the agent.** The user message and an empty assistant message (`streaming`) are written in one transaction before `InvokeAgentRuntime`. If the send is refused (auth, agent offline, run in progress), nothing is saved and the draft stays in the browser.
2. **One run per session at a time.** A second send while a reply is streaming gets `409 run_in_progress`.
3. **The run id is the assistant message id.** No separate runs table. Stop and polling address the assistant message.
4. **Sends are idempotent.** The browser generates `clientMessageId` (UUID). A resend with the same id (for example after refreshing an expired access token) returns the existing message instead of creating a second one.
5. **The agent call is decoupled from the HTTP response.** It runs in its own task. The SSE response only mirrors it, so a disconnect stops the mirroring, not the agent (D11).
6. **Checkpoints.** The assistant message's blocks are saved when a block ends, and at least every 2 s while text streams (P1).
7. **Only Stop cancels.** `POST /sessions/{id}/runs/{runId}/stop` cancels the agent call and saves `stopped`. Closing the connection does not.
8. **Retry reruns the same user message.** It resets the failed or interrupted assistant message and starts a new run; it does not create a new user message.
9. **No stream resume in v1.** Events carry ids, but after a drop the client reads the message from the API and polls while it is `streaming` (P3).
10. **History goes in the payload.** The API sends recent turns from Postgres with every call; `runtimeSessionId` is our session id, but agents may not depend on it (D18).

## Assistant message status

```
streaming ──► complete      agent finished
          ──► stopped       user pressed Stop (partial kept)
          ──► failed        agent or AgentCore error (partial kept, if any)
          ──► interrupted   API task died, or the 15-min run cap was hit (partial kept)
failed / interrupted ──► streaming   Retry
```

| Status | UI (design states on board `R9pQQP`) | Retry |
|---|---|---|
| `streaming` | Streaming reply; "Still replying…" when opened from elsewhere | n/a |
| `complete` | Finished reply | n/a (Regenerate is P1) |
| `stopped` | Partial reply + "Stopped" | Yes |
| `failed` | "Reply failed" | Yes |
| `interrupted` | Partial reply + "Interrupted" (or "Stopped after 15 minutes") | Yes |

## Timers

| Timer | Value | Where | Why |
|---|---|---|---|
| Keep-alive comment | every 15 s | API, its own timer | Keeps the ALB and proxies from closing an idle stream |
| Client stall detection | 45 s with no bytes | Browser | Three missed pings means the connection is gone; switch to polling |
| ALB idle timeout | 300 s | Terraform | Explicit, well above the ping interval (D5) |
| ALB deregistration delay | 300 s | Terraform | Lets streams finish during a deploy (P2) |
| Container stop timeout | 120 s (ECS max) | Task definition | Time to finish open streams after SIGTERM (P2) |
| Run time cap | 15 min, per-agent override | API | Ends runaway runs as `interrupted` (D11) |
| Checkpoint | block end, or 2 s | API | Crash safety (P1) |
| Poll while streaming | every 2 s | Browser | Picks up a reply that kept running after a disconnect |
| Access token | ~15 min | API | Short-lived, held in memory (D8) |
| Refresh token | 30 days, rotated on every use | API | Picked as a default; the "Auth expired" screen appears after this |
| Google JWKS cache | per Google's `Cache-Control` | API | Avoid a Google call per sign-in |

## Error codes used in these flows

| Code | HTTP / event | Meaning | Client action |
|---|---|---|---|
| `token_expired` | 401 | Access token expired | Refresh, then resend (same `clientMessageId`) |
| `session_expired` | 401 | Refresh token expired, revoked or reused | "Auth expired" screen, keep draft, sign in again |
| `agent_unavailable` | 503, or `run.failed` | Agent offline in the table, or AgentCore unreachable | Composer disabled (503) or "Reply failed" + Retry (event) |
| `run_in_progress` | 409 | A reply is already running in this session | Keep draft; wait |
| `agent_error` | `run.failed` | The agent failed mid-run | "Reply failed" + Retry |
| `run_time_limit` | `run.failed` with status `interrupted` | Hit the 15-min cap | "Stopped after 15 minutes" + Retry |

## Not verified yet

- **What AgentCore actually streams.** The translator (step 22 in the normal-path diagram) is drawn against the app's block format; the real Strands/AgentCore output is recorded in step 8 before the translator is written.
- **Whether closing the AgentCore response stream actually stops the agent run** on the runtime side, or only stops us reading it. Stop must be checked against the real runtime in step 8; if closing isn't enough, the agent needs a cancel signal.
- **SSE through the ALB with keep-alives.** Proven in step 8.
