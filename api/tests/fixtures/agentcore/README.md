# What AgentCore actually streams (recorded 2026-09-30)

*Copied from `docs/AGENTCORE_STREAM.md` in the private `fleet-agent-research-analyst` repository, where the agent, the recorders and the replaying contract tests live. The `.sse` files here are the raw response bodies; each `.json` holds the request, the response headers and when each frame arrived.*

Build step 7 for issue #3. Input for the hub's stream translator (D10, agent_hub#8) and for SEND_MESSAGE's "Not verified yet" list.

**Setup:** Research Analyst v0 (Strands Agents 1.57.1, bedrock-agentcore 1.24.0, Claude Sonnet 5 with adaptive thinking, `display: "summarized"`, effort `medium`) on AgentCore Runtime `fleet_dev_research_analyst_runtime_us_east_1-J5QFpm41XD`, version 2 (image `023722a5dedc`). Recorded with `boto3` `InvokeAgentRuntime` by the agent repository's `scripts/record_stream.py`, reading byte by byte so each frame is timed when it arrives; its `tests/contract/test_stream.py` replays them.

| Fixture | Request | Frames | Bytes | First byte | Total |
|---|---|---|---|---|---|
| `plain-answer` | One-line general question, no tool | 26 | 2,721 | 1.04 s | 3.40 s |
| `thinking` | A small reasoning question, no tool | 39 | 5,376 | 0.69 s | 5.40 s |
| `tool-call` | `fetch_url` on example.com, success | 40 | 4,751 | 0.64 s | 4.72 s |
| `tool-error` | `fetch_url` on an IANA page that 404s | 45 | 4,998 | 0.66 s | 5.12 s |
| `invalid-payload` | `{"input": "hi"}` (no `messages`) | 1 | 118 | 0.66 s | 0.66 s |

Each recording used a new runtime session.

## What the agent sends, and why it's filtered

The entrypoint streams Strands' `stream_async` events through `research_analyst.stream.to_wire`. Unfiltered (runtime version 1), about one frame in three was a JSON **string** holding a Python `repr()` of a Strands callback event: AgentCore falls back to `json.dumps(str(event))` for events carrying live objects (the Agent, spans, the AgentResult). Those frames were 94 % of the bytes of a tool call (120 KB; a three-page run streamed 494 KB), grew with every turn, contained the system prompt, tool schemas and whole message history including fetched page text, and the run's end state existed only as `"{'result': AgentResult(...)}"`. The filter drops them and ends the run with one JSON `result` frame; the tool-call stream went from 120 KB to under 5 KB. Every frame is now a JSON object.

## The transport

- HTTP **200**, `content-type: text/event-stream; charset=utf-8`, chunked; the only AgentCore header is `x-amzn-bedrock-agentcore-runtime-session-id`.
- Every frame is one `data: <json object>\n\n` line. No `event:`, `id:` or `retry:` fields, and no keep-alive comments: the stream is silent while the model thinks or a tool runs.
- Errors raised by the agent also arrive as **HTTP 200**, as a single frame, then the stream ends:
  `{"error": "messages is required", "error_type": "ValueError", "message": "An error occurred during streaming"}`.

## The frames

| Frame | Meaning |
|---|---|
| `{"init_event_loop": true}` | Always first (about 0.6–1 s after the request) |
| `{"start": true}`, `{"start_event_loop": true}` | A model call is starting (`start` repeats after tool results) |
| `{"event": {"messageStart": {"role": "assistant"}}}` | Start of one model call: the Bedrock ConverseStream events follow, unchanged |
| `{"event": {"contentBlockStart": {"start": {"toolUse": {"toolUseId", "name", "type"}}, "contentBlockIndex"}}}` | A tool call begins (text and reasoning blocks have no start event) |
| `{"event": {"contentBlockDelta": {"delta": {"text": "..."}, "contentBlockIndex"}}}` | Answer text |
| `{"event": {"contentBlockDelta": {"delta": {"reasoningContent": {"text": "..."}}}}}` | Thinking (summarised); the block ends with a delta carrying `reasoningContent.signature` |
| `{"event": {"contentBlockDelta": {"delta": {"toolUse": {"input": "<partial JSON>"}}}}}` | Tool arguments, streamed as partial JSON |
| `{"event": {"contentBlockStop": {"contentBlockIndex"}}}` | End of a block |
| `{"event": {"messageStop": {"stopReason": "tool_use" \| "end_turn"}}}` | End of one model call |
| `{"event": {"metadata": {"usage": {...}, "metrics": {"latencyMs", ...}}}}` | Tokens and latency of that model call; always last in the call |
| `{"message": {"role": "assistant", "content": [...], "metadata"}}` | The complete assistant message of that model call: text, `reasoningContent` (with signature), `toolUse` (with parsed `input`) |
| `{"message": {"role": "user", "content": [{"toolResult": {"toolUseId", "status": "success" \| "error", "content": [{"json": {...}}]}}]}}` | A tool result. fetch_url failures have `status: "error"` and `{"error": code, "detail"}` |
| `{"result": {"stopReason": "end_turn", "usage": {"inputTokens", "outputTokens", "totalTokens", ...}}}` | **Last frame** of a completed run: the run's stop reason and total tokens. Other stop reasons: `cancelled` (300 s limit), `limit_turns` (10 model calls), `max_tokens` |
| `{"force_stop": true, "force_stop_reason": "..."}` | The run failed inside Strands; an `error` frame follows |

## Sequences and timing

```
plain-answer:  init_event_loop → start → start_event_loop → messageStart → contentBlockDelta(text)×n
               → contentBlockStop → messageStop(end_turn) → metadata → message(assistant) → result

thinking:      init_event_loop → start → start_event_loop → [4.1 s of silence] → messageStart
               → reasoningContent deltas … signature → contentBlockStop → text deltas → contentBlockStop
               → messageStop(end_turn) → metadata → message(assistant: [reasoningContent, text]) → result

tool-call /    … messageStart → contentBlockStart(toolUse fetch_url) → toolUse input deltas → contentBlockStop
tool-error:    → messageStop(tool_use) → metadata → message(assistant: [toolUse]) → message(user: [toolResult success|error])
               → start → start_event_loop → messageStart → text deltas → contentBlockStop → messageStop(end_turn)
               → metadata → message(assistant: [text]) → result
```

- **Thinking isn't streamed while it happens.** In `thinking`, nothing arrives for 4.1 s after `start_event_loop`; then the summarised reasoning arrives in a burst of about 350 ms, immediately followed by the answer. The UI needs a "thinking" state between `start_event_loop` and the first delta.
- **Tool steps:** in `tool-call`, the tool-use message arrived at 2.49 s and the tool result at 2.79 s; the second model call started at 4.06 s. The result `message` is the only signal that the tool finished; nothing marks the tool starting to run except the tool-use `message`.
- The plain answer produced no thinking at `medium` effort; the reasoning question did. Thinking always comes before the text of the same model call, as its own content block.

**For the translator:** `event.*` frames give streaming text, thinking and tool-argument deltas; `message` frames give each finished block (tool call with parsed input, tool result with status); `result` gives the run's stop reason and token totals; an `error` frame means the run failed; the end of the body without `result` or `error` means the connection dropped.

## Does closing the response stream stop the run?

**No.** Checked twice with the agent repository's `scripts/stop_probe.py` (on runtime version 1; the filter doesn't change this): a request to read three pages one after another, each URL tagged with a probe id; the caller closes the response stream as soon as the first bytes arrive, before the model has chosen a tool; the runtime's log is then searched for the probe URLs.

| Probe | What the caller did | Fetches after it (seconds) | Result |
|---|---|---|---|
| `3b1e19dc2ab2` | Closed the stream | page 1 at +0.5, page 2 at +3.9, page 3 at +5.9 | The run carried on to the end with nobody reading |
| `d47c77a08952` | Closed the stream, then `StopRuntimeSession` (HTTP 200, 0.67 s later) | page 2 at +1.6, page 3 at +3.4 | **`StopRuntimeSession` didn't stop the run in progress either** |

(Times are the runtime's log timestamps against the caller's clock.)

A third check: while a run was in progress, a second `InvokeAgentRuntime` on **the same runtime session** was accepted within 0.6 s and reached the agent's own code, and the first run finished normally.

**Consequence for the hub (SEND_MESSAGE rule 7, "Only Stop cancels"):** stopping the hub's reading stops the mirroring and the saving, not the agent. So the agent has a cancel signal.

## Stop: the cancel invocation

To stop a running reply, the hub invokes **the same runtime session** (AgentCore routes a session to one microVM, so it reaches the process running the reply) with:

```json
{"cancel": {"messageId": "<context.messageId of the running reply>"}}
```

The reply to that invocation is one frame, then the stream ends:

```json
{"cancel": {"messageId": "…", "cancelled": true}}
```

`cancelled: false` means no reply with that id is running in this process: it already finished, or it never ran there (e.g. the session was restarted). The hub can treat both as stopped.

The running reply then ends at its next checkpoint, with its usual last frame:

```json
{"result": {"stopReason": "cancelled", "usage": {…}}}
```

- **During model output** (including the silent thinking period), Strands' Bedrock provider aborts the request in flight.
- **During a tool call**, `fetch_url` gives up within 0.1 s. The tool result is `{"error": "cancelled"}` with `status: "error"`, and no further model call is made.
- **Between steps**, Strands checks before each tool call and each model call.

Details:
- A new run for a message id that is still running (a Retry) cancels the old run first.
- The agent's 300 s run limit also ends a run with `stopReason: "cancelled"`. The hub knows whether it sent Stop.
- A cancelled reply's partial text is whatever the hub already received; the agent doesn't resend it.

**Checked on the deployed runtime** (version 3, image `7ee34936c986`, 2026-09-30):

| Where the run was | Probe | Result |
|---|---|---|
| Between tool calls (page 1 read, page 2 next) | `stop_probe.py --cancel`, probe `af6df798a6a8` | `cancelled: true`; run ended 0.67 s after the cancel was sent with `stopReason: "cancelled"`; page 3 never fetched (page 2's fetch had already completed when the cancel arrived) |
| Writing the final answer | `stop_probe.py --cancel`, probe `da74ec8560b2` | `cancelled: true`; run ended 0.64 s after the cancel was sent; no fetch after the cancel reply |
| Inside a fetch of a page that takes 10 s | `record_cancel.py` → fixtures `cancelled-mid-fetch`, `cancel-reply` | `cancelled: true`; the tool returned `{"error": "cancelled"}` and the run ended 1.9 s after the cancel was sent, 7.0 s after the request |

So the cancel reaches the process running the reply, and the reply stops at whichever point it has reached.

Implementation: `research_analyst.contract.parse_payload`, `research_analyst.runs.Runs`, `app.py`; tested in `tests/test_cancel.py` (in-process, with a scripted model) and in `tests/contract/test_stream.py` against the recorded cancel fixtures.
