# Sending a message: flow, states and timers

Step 3 of the build plan, updated by the alignment review (step 4b). Exact request, response and event shapes: [`api/openapi.yaml`](../api/openapi.yaml). Diagrams:
- Normal path, including sign-in and the session check: [`diagrams/send-message.mmd`](diagrams/send-message.mmd) ([PNG](diagrams/send-message.png))
- Failure paths: [`diagrams/send-message-failures.mmd`](diagrams/send-message-failures.mmd) ([PNG](diagrams/send-message-failures.png))
- Attachments and approvals: [`diagrams/approval-and-upload.mmd`](diagrams/approval-and-upload.mmd) ([PNG](diagrams/approval-and-upload.png))

Decisions behind this are in [`ARCHITECTURE.md`](ARCHITECTURE.md) (D5, D8, D10, D11, D18–D23, P1–P4). Endpoint paths and event names match the OpenAPI spec (step 5). All routes are under `/v1` (D23).

## Rules

1. **Save before calling the agent.** The user message and an empty assistant message (`streaming`) are written in one transaction before `InvokeAgentRuntime`. If the send is refused (auth, agent offline, run in progress), nothing is saved and the draft stays in the browser.
2. **One open reply per session.** A second send while a reply is `streaming` gets `409 run_in_progress`. A reply that is `awaiting_approval` is not blocking: the new send cancels the approval and completes the paused reply in the same transaction (D19). The database enforces at most one `streaming` or `awaiting_approval` reply per session.
3. **The run id is the assistant message id.** No separate runs table. Stop, Retry and polling address the assistant message.
4. **Sends are idempotent per user.** The browser generates `clientMessageId` (UUID), unique per user, not per session. A resend with the same id (for example after refreshing an expired access token) returns the existing message and its session instead of creating new ones, including on the first send of a new session.
5. **The agent call is decoupled from the HTTP response.** It runs in its own task. The SSE response only mirrors it, so a disconnect stops the mirroring, not the agent (D11).
6. **Checkpoints and heartbeat.** The assistant message's blocks are saved when a block ends and at least every 2 s while text streams (P1). The running task writes `heartbeat_at` with every checkpoint and on its 15 s keep-alive tick.
7. **Only Stop cancels.** `POST /v1/messages/{id}/stop` sets `cancel_requested_at`; whichever task runs the reply sees it within 2 s, cancels the agent call (a `cancel` invocation on the same runtime session; closing the stream isn't enough, see Verified) and saves `stopped`. It works during deploys, when two tasks run. Closing the connection does not cancel.
8. **Retry reruns the same user message.** Allowed from `stopped`, `failed` and `interrupted` (`409` otherwise). It keeps the assistant message id and `seq`, clears its blocks and error, deletes its tool calls (their approvals go with them), marks its unfinished artifact versions `incomplete`, and starts a new run. No new user message.
9. **No stream resume in v1.** Events carry ids, but after a drop the client reads the message from the API and polls while it is `streaming` (P3). There is no "agent silent" error: after 60 s without events the reply shows a soft "Still working" note with no Retry.
10. **History goes in the payload.** The API sends recent turns from Postgres with every call, plus the new message's attachments as 15-minute signed URLs (D18, D20). `runtimeSessionId` is our session id, but agents may not depend on it.
11. **Title at creation.** The first send creates the session and titles it from the first message (D21). There is no title event.
12. **Approvals end the run.** An approval request saves the approval, sets the message to `awaiting_approval`, sends the `approval` block (`block.started`) and closes the stream with `run.awaiting_approval`. `POST /v1/approvals/{id}/decision` re-invokes the agent and streams the continuation into the same message; deny re-invokes too, expiry doesn't (D19).
13. **Dead runs are found by heartbeat.** On startup and every minute, `streaming` rows whose heartbeat is older than 60 s become `interrupted`. A reply still running on the old task during a deploy keeps its heartbeat fresh and is left alone.
14. **Deleting a session** stops its running reply and cancels its pending approvals first; the purge job skips rows still `streaming`.

## Assistant message status

```
streaming ──► complete            agent finished
          ──► awaiting_approval   agent asked for approval; run ended (D19)
          ──► stopped             user pressed Stop (partial kept)
          ──► failed              agent or AgentCore error (partial kept, if any)
          ──► interrupted         task died (stale heartbeat) or the 15-min run cap was hit (partial kept)
awaiting_approval ──► streaming   approved or denied: the agent continues in the same message
                  ──► complete    approval expired, or cancelled by a new message
stopped / failed / interrupted ──► streaming   Retry
```

| Status | UI (design states on board `sx5f0`) | Retry |
|---|---|---|
| `streaming` | Streaming reply; "Still replying…" when opened from elsewhere; soft "Still working" after 60 s without events | No |
| `awaiting_approval` | Reply with a pending approval card; composer enabled | No |
| `complete` | Finished reply | No (Regenerate is P1) |
| `stopped` | Partial reply + "Stopped" | Yes |
| `failed` | "Reply failed" | Yes |
| `interrupted` | Partial reply + "Interrupted" (or "Stopped after 15 minutes") | Yes |

## Timers

| Timer | Value | Where | Why |
|---|---|---|---|
| Keep-alive comment | every 15 s | API, its own timer | Keeps the ALB and proxies from closing an idle stream; also writes the heartbeat |
| Client stall detection | 45 s with no bytes | Browser | Three missed pings means the connection is gone; switch to polling |
| "Still working" note | 60 s with no events (pings don't count) | Browser | Reassures during long tool calls; not an error |
| Stale heartbeat | 60 s | API sweep, every minute and on startup | Marks runs of a dead task `interrupted` (P1) |
| Stop pickup | ≤ 2 s | Running task | Checks `cancel_requested_at` at each checkpoint and keep-alive tick |
| ALB idle timeout | 300 s | Terraform | Explicit, well above the ping interval (D5) |
| ALB deregistration delay | 300 s | Terraform | Lets streams finish during a deploy (P2) |
| Container stop timeout | 120 s (ECS max) | Task definition | Time to finish open streams after SIGTERM (P2) |
| Run time cap | 15 min, per-agent override | API | Ends runaway runs as `interrupted` (D11); time waiting for an approval doesn't count (D19) |
| Approval expiry | 10 min default, per agent | API sweep | Pending approvals become `expired`; the paused reply becomes `complete` |
| Checkpoint | block end, or 2 s | API | Crash safety (P1) |
| Poll while streaming | every 2 s | Browser | Picks up a reply that kept running after a disconnect |
| Sessions list refresh | every 20 s while visible | Browser | Working dot, approval badge and toast, "Task complete" toast (D22) |
| Offline agent poll | every 30 s | Browser | Unlocks the composer when the agent is back (D22) |
| Attachment URL | 15 min | API | Signed GET in the agent payload (D20) |
| Access token | ~15 min | API | Short-lived, held in memory (D8) |
| Refresh token | 30 days, rotated on every use | API | Picked as a default; the "Auth expired" screen appears after this |
| Google JWKS cache | per Google's `Cache-Control` | API | Avoid a Google call per sign-in |

## Error codes used in these flows

Errors use the common format in D23 (`code`, `requestId`, `retryable`, optional `retryAfter`).

| Code | HTTP / event | Meaning | Client action |
|---|---|---|---|
| `token_expired` | 401 | Access token expired | Refresh, then resend (same `clientMessageId`) |
| `session_expired` | 401 | Refresh token expired, revoked or reused | "Auth expired" screen, keep draft, sign in again |
| `not_invited` | 403 | Google account not on the allowlist | "Not allowed" screen with the account's email |
| `agent_unavailable` | 503, or `run.failed` | Agent offline in the table, or AgentCore unreachable | Composer disabled (503) or "Reply failed" + Retry (event) |
| `run_in_progress` | 409 | A reply is already streaming in this session | Keep draft; wait |
| `too_many_runs` | 429 | Three replies already running for this user | Keep draft; try again shortly |
| `not_retryable` | 409 | Retry on a message that isn't stopped, failed or interrupted | Refresh the message |
| `approval_not_pending` | 409 | Decision on an approval that was already decided, expired or cancelled | Show the approval's current state |
| `agent_error` | `run.failed` | The agent failed mid-run | "Reply failed" + Retry |
| `rate_limited` | `run.failed` | AgentCore or the model throttled the call | "Reply failed" + Retry after `retryAfter` |
| `run_time_limit` | `run.failed` with status `interrupted` | Hit the 15-min cap | "Stopped after 15 minutes" + Retry |
| `message_too_long` | 422 | Text over 32,000 characters | Keep draft; show the limit |

## Verified (2026-09-30, Research Analyst v0 on AgentCore, issue #3)

- **What AgentCore actually streams:** recorded for a plain answer, thinking, a tool call, a tool error and an invalid payload in [`api/tests/fixtures/agentcore/`](../api/tests/fixtures/agentcore/README.md). HTTP 200 SSE of `data: <json>` frames only: Bedrock ConverseStream events unchanged, finished `message`s (tool calls and results), and a final `result` with the stop reason and tokens. Agent errors also arrive as HTTP 200, as one `error` frame. No keep-alives: the stream is silent while the model thinks (4 s in the recording) or a tool runs. The translator (#8) is written against these.
- **Closing the AgentCore response stream does not stop the run**, and neither does `StopRuntimeSession`: in both probes the agent kept fetching pages seconds later. So a Strands agent stops on a second invocation **on the same runtime session**: `{"cancel": {"messageId": "<assistant message id>"}}` (`AgentCancel` in `openapi.yaml`). It answers `{"cancel": {"messageId", "cancelled": true | false}}` and the running reply ends with `{"result": {"stopReason": "cancelled"}}`. Verified on Research Analyst's runtime: stopped between tool calls (0.67 s), during the final answer (0.64 s) and inside a 10 s fetch (1.9 s); recorded as `cancelled-mid-fetch` and `cancel-reply`.

## Not verified yet

- **SSE through the ALB with keep-alives.** Proven in step 8 (#10). Locally (issue #8, 2026-10-03): a real reply streams to `curl -N`; a client that hangs up after 2 s leaves the reply running to `complete`, and polling `GET /v1/messages/{id}` picks it up; SIGTERM mid-reply lets it finish, then the process exits.
- **Resuming a Strands agent after an approval** by re-invoking it with the decision (D19). Spiked at the start of the approvals slice (P8).
