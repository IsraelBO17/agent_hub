# Alignment review: screens, data model, stream and API

| | |
|---|---|
| Status | **Resolved.** Owner answered D1–D4; fixes applied to docs, diagrams, schema and the design file (§8). |
| Date | 2026-09-29 |
| Inputs | `design/fleet_dev.pen` (278 frames, read as JSON: Pencil didn't have the file open, so text and structure were checked, not visuals), `PRODUCT_PLAN.md`, `ARCHITECTURE.md` (D1–D18, P1–P8), `SEND_MESSAGE.md` + both sequence diagrams, `DATA_MODEL.md` + `er.mmd`, `api/app/db/models.py` |
| Missing | Nothing required. Not present but not needed: the PNG renders of P0 screens promised in `PRODUCT_PLAN.md` M0, and `BACKEND_CONTRACT.md` (step 5's OpenAPI replaces it). No front-end code, as expected. |

## Verdict

**Now: ready for the OpenAPI spec.** All five blockers are fixed in the docs, the diagrams and the schema (migration `0002`, tested), and the four decisions are recorded as ARCHITECTURE D19–D22, with the API defaults as D23. What remains is either for the OpenAPI to define (#9, block schemas) and the design-only fixes from `design/ALIGNMENT_FIXES.md` are applied in `fleet_dev.pen` (commits `3d81fbe`, `b7baa0f`). §8 lists every finding and what happened to it.

**Initial verdict (kept for the record): not ready for OpenAPI yet, but close.** The model is sound: the send path, statuses, composite keys, indexes and the blocks-plus-side-tables split all hold up against the screens. Five things would make the spec wrong or unstable if we wrote it today:

1. Approvals have no message state and no decision operation (B1).
2. The first send in a new session isn't idempotent, so a token-refresh resend creates a second session (B2).
3. Rolling deploys briefly run two tasks, which breaks Stop and the startup "mark as interrupted" sweep (B3).
4. Agents have no way to receive attachments (B4).
5. Timeout and Retry rules contradict each other across the design, the plan and `SEND_MESSAGE.md` (B5).

B1–B5 are findings 1–5 below.

Each fix is a short doc change plus, for B2 and B3, one small migration. Three need your call (decisions D1–D3 at the end). After that, about half a day of edits and the spec can start.

Finding numbers below are referenced as **#n** in the tables. API names are provisional (the OpenAPI fixes them), all under `/v1`.

---

## 1. Screen inventory

Scope: **v1** = P0; **P1** = soon after v1; **P2** = later; **cut** = not building.

| Surface | Designed states (node IDs) | Scope | Implied but not designed |
|---|---|---|---|
| Sign in | default `MMxdZ`, loading `vkBhc`, not allowed `zte2v`, signed out `DfY8F`; mobile `U0HaRi`, `dLCVX` | v1 | Google popup closed or network error (#18) |
| Auth expired, draft kept | `N8ysh`, mobile `DxTnt` | v1 | none |
| Catalog | `PBQLh`/F2.1, mobile `ulBUE`; loading (States board, F11.1 `EP1MN`); error `Jchi9`, `sMh7q`; empty `j8NhJ`, `iX1f6` | v1 | none |
| New session | `uBRCZ`, F2.3–F2.4, F8.3, mobile F11.2–F11.4 | v1 | none |
| Chat: waiting, thinking, tools, streaming, finished | `wtDYF`, F2.5–F2.8, F3.1–F3.3, F5.4–F5.5, F8.1/F8.4, mobile F11.5 | v1 | none |
| Plan card, long task | F4.5, F4.7, `sx5f0` §3–4, mobile F11.6 | v1 | none |
| Reply end states: stopped, interrupted, failed, still replying | `sx5f0` §7–8, F6.1–F6.2, F11.9 | v1 | none |
| Connection lost / back online | F6.3–F6.4, F11.8 | v1 | none |
| Agent offline / degraded / not found / orphaned / updated | `D21ObU`, F6.8, F11.11, `V97EP`, `OFj2k`; degraded F9.7–F9.8 | v1 (degraded detail: P1) | none |
| Session not found | `H7ZqtC`, F11.19 | v1 | none |
| Sidebar / drawer, row menu, delete + undo | `hj5RV`, F10.5, F7.3, F7.6–F7.7, F11.15–F11.18, `sV0Oz`, `ABwYF` | v1 (pin, archive, share, export: P1) | Sidebar fails to load (#18) |
| Agent switcher, ⌘J | F8.2, F8.5, F11.10 | v1 (⌘J: P1) | none |
| Composer: attachments, drag-drop, limits, disabled | `Q6kwA2` §1–2, F5.1–F5.3, F11.3–F11.4 | v1 (voice: P2) | none |
| Artifact card + panel (document, code, html, table) | `oQYrz`, `fUZV4`, `j2uc1W`, `LrhPn`, F3.4–F3.5, F3.7, `F9oiRc`; mobile `JLUHx`, `KXQcB`, `SZqQD`, `ZQvzZ`, F10.2–F10.4 | v1 (edit, compare, run console: P2) | Panel/version fails to load (#18); mobile code, html and table views |
| Approval card: pending, approved, denied, expired, decided elsewhere, expired while away | F4.1, F4.3, F4.4, `Lwlwe` §4, `OFj2k`; mobile F10.6, F11.12–F11.14 | v1 | Decision request fails (#18) |
| Approval waiting in another session | `r5Gru`, `B6G93s` | v1 | none |
| Questions: quick reply, single, multi | `Lwlwe` §1–2, F11.7 | v1 | none |
| Tool permission prompt (Allow once / Always allow / Deny) | `Lwlwe` §5 | **P2** (#15) | none |
| Session info drawer | `E3lQz`, F7.2 | v1 (Share/Export/Archive buttons: P1) | Mobile version |
| ⌘K palette | `B5LZKO`, `vBr4V`, F7.1, mobile `P7n48` | P1 | none |
| Share dialog, public page | `vBr4V`, F7.4, `q1bvDq`, mobile `W2aSQ` | P1 | Revoked link (404) public page (#18) |
| Export | F7.5 | P1 (Markdown only, F27) | none |
| Archived, artifacts library | `HbIFz`, `g2nGvw`, F7.8–F7.9, mobile `grrlx`, `GSi1C` | P1 | none |
| Agent detail | `x05s4W`, F2.2, F9.5, mobile `mN9zj` | P1 | none |
| Settings, delete all | `RHrDH`, F9.1–F9.3, mobile `RT72e` | P1 (Account + Sign out needed in v1) | none |
| Forms | `Lwlwe` §3, mobile `m4Kt4` | P1 | none |
| Rich content: citations, images, charts, files, diagrams | `IVLvU` | P1 (diagrams: not in any list, #15) | none |
| Feedback, regenerate, message edit | `Q6kwA2` §4–5 | P1 feedback and regenerate; P2 edit | none |
| Add/edit agent, onboarding, voice, Face ID, compare, doc edit, shortcuts overlay, rate-limit countdown, session too long, background-task toasts | Flow 1, F9.6, `yzVIz`, `RPCu8`, F5.6–F5.7, F4.2, F3.6, F3.8, F9.4, F6.5–F6.7, F4.6 | P2 | none |

---

## 2. Traceability: screen → data → API

Legend: ✅ backed; ⚠ gap (see finding); **computed** = derived on read, no column.

### Auth, account

| Screen | Shows / action | Stored in | API op / event | |
|---|---|---|---|---|
| Sign in `MMxdZ` | Continue with Google | `users.google_sub`, `refresh_tokens` | `POST /v1/auth/google` | ✅ |
| App load | Restore session | `refresh_tokens` (rotate) | `POST /v1/auth/refresh` | ✅ |
| Not allowed `zte2v` | Google email of the rejected account | not stored (from ID token) | `403 not_invited` with `email` | ✅ |
| Signed out `DfY8F`, Settings | Sign out | `refresh_tokens.revoked_at` (family) | `POST /v1/auth/logout` | ⚠ not in docs yet (#16) |
| Sidebar footer, Settings `RHrDH` | Name, email, avatar | `users.name`, `email`, `avatar_url` | `GET /v1/me` | ⚠ not in docs yet (#16) |
| Settings | Default agent, reopen last session | `users.preferences` | `PATCH /v1/me` | ✅ |
| Auth expired `N8ysh` | Draft kept, "Signed in as …" | browser | `401 session_expired` | ✅ |

### Catalog, new session, agent pages

| Screen | Shows / action | Stored in | API op / event | |
|---|---|---|---|---|
| Catalog `PBQLh` | Name, description, icon, colour, Beta tag, status dot | `agents.name`, `description`, `icon`, `color`, `stage`, `status` | `GET /v1/agents` | ✅ |
| Catalog | "Strands · AgentCore", "LangGraph · HTTP adapter" | `agents.framework`, `runtime_type` | same | ✅ |
| Mobile catalog `ulBUE` | Short description ("Symptoms, meds and lab results") | none | none | ⚠ #7 |
| Catalog | "14 sessions · 2h ago" per agent | **computed** count / max `last_message_at` (`ix_sessions_sidebar`) | `stats` in `GET /v1/agents` | ✅ define field |
| Catalog | "Offline since Sep 24", "Beta since Sep 20" | none | none | ⚠ #7 |
| Catalog | "6 registered · 5 available" | **computed** client-side | none | ✅ |
| Catalog | Continue where you left off | `sessions.title`, `agent_id`, `last_message_at` (`ix_sessions_recent`) | `GET /v1/sessions?limit=3` | ✅ (exclude archived) |
| Catalog error `Jchi9` | "GET /agents returned 503" | none | error format (§6) | ✅ |
| New session `uBRCZ` | Greeting ("What are we building today?") and intro line | none | none | ⚠ #7 |
| New session | Starter title + subtitle | `agents.starters` | `GET /v1/agents/{slug}` | ✅ define shape `{title, description, prompt}` |
| New session | Disclaimer; "+" only if attachments allowed | `agents.disclaimer`, `capabilities.attachments` | same | ✅ |
| New session | First send creates the session | `sessions`, `messages` | `POST /v1/agents/{slug}/sessions` (SSE) | ⚠ #2 |
| Agent detail `x05s4W` (P1) | Tools with Auto / Asks first | `agents.tools[].requiresApproval` | `GET /v1/agents/{slug}` | ✅ |
| Agent detail | Model, region, "Strands 1.8", "v14 · deployed Sep 26" | `version` only | none | ⚠ #7 |
| Agent detail | p95 latency | none | none | ⚠ #7 (Later, F23) |
| Agent detail | "31 sessions · 212 messages", recent sessions | **computed** | `stats`; `GET /v1/sessions?agent=&limit=3` | ✅ (drop message count, #23) |
| Agent not found `V97EP` | Unknown slug | `agents.slug` | `404 agent_not_found` | ✅ |
| Orphaned session `OFj2k` | "No longer available" | `agents.retired_at` | `GET /v1/agents/{slug}` must still return retired agents | ✅ note for spec |

### Sidebar, sessions

| Screen | Shows / action | Stored in | API op / event | |
|---|---|---|---|---|
| Sidebar | Sessions grouped Today / Yesterday / … | `sessions.last_message_at` (grouped client-side) | `GET /v1/sessions?agent=&cursor=` | ✅ |
| Sidebar `sV0Oz` (P1) | Pinned section | `sessions.pinned_at` | `GET /v1/sessions?pinned=true` | ✅ |
| Sidebar | Working dot on a session | **computed** from `uq_messages_streaming_per_session` | `isRunning` in list | ⚠ #6 (how it refreshes) |
| Sidebar `r5Gru` | Approval badge, "approval needed in another session" toast | **computed** from `ix_approvals_pending` | `pendingApprovals` in list | ⚠ #6 |
| Row menu | Rename | `sessions.title`, `title_source = user` | `PATCH /v1/sessions/{id}` | ✅ |
| Row menu (P1) | Pin, Archive, Restore | `pinned_at`, `archived_at` | `PATCH /v1/sessions/{id}` | ✅ |
| Row menu | Delete, Undo | `deleted_at`, purge job | `DELETE /v1/sessions/{id}`, `POST /v1/sessions/{id}/restore` | ⚠ #11 (running session), #17 (8 s vs 10 s) |
| Mobile row menu `G6iHV`, Archived | "12 messages" | **computed** | list field | ✅ #23 |
| Session not found `H7ZqtC` | 404 (also for deleted or another user's) | none | `404 session_not_found` | ✅ |
| Session info `E3lQz` | Created, last activity, messages, tool calls, tokens, id | `created_at`, `last_message_at`, **computed** counts, sum of `messages.usage` | `GET /v1/sessions/{id}` with `stats` | ✅ (id format: #17) |
| Session info | Artifacts, files ("Uploaded by you", "From run_tests") | `artifacts`, `files.purpose` | `GET /v1/sessions/{id}/artifacts`, `/files` | ✅ |

### Chat transcript and stream

| Screen | Shows / action | Stored in | API op / event | |
|---|---|---|---|---|
| Chat `wtDYF` | User text, time | `messages.blocks[text]`, `created_at` | `GET /v1/sessions/{id}/messages` | ✅ |
| `Q6kwA2` §4, F5.4 | Attachment cards, image grid | `files.filename`, `content_type`, `size_bytes` | same, with short-lived URLs | ✅ |
| same | "PDF · 4 pages", "CSV · 214 rows" | none | none | ⚠ #13 |
| F2.5 | Waiting dots | browser, after `run.started` | `run.started` | ✅ |
| `sx5f0` §1 | "Thought for 8s", expandable reasoning | `thinking` block | `block.*` | ✅ needs start/end times (#9) |
| F2.6, F3.1 | "Working · 2 of 4 steps", labelled steps, Queued | `plan` block | `block.*` | ⚠ #9 |
| `wtDYF` | Tool chip: name, summary, duration, state, Input / Output | `tool_calls.name`, `summary`, `started_at`/`completed_at`, `status`, `input`, `output` | `tool.*` events | ✅ (summary source: #9) |
| F2.7 | Streaming text, caret | `text` block | `block.delta` | ✅ |
| F5.5 | "This isn't a diagnosis" care callout | none | none | ⚠ #9 (callout not a block type) |
| F2.8 | "10:43 · 3 tool calls" | `completed_at`, **computed** | none | ✅ |
| `OFj2k` | "Agent updated to v15" divider | `messages.agent_version` | none | ✅ |
| Chat | Stop / Esc; plan card "Cancel task" | `messages.status = stopped` | `POST /v1/messages/{id}/stop` | ⚠ #3, #9 (one name) |
| `sx5f0` §8 | Stopped / Interrupted / Failed / Still replying | `messages.status`, `error` | `run.*` events | ✅ |
| F6.1 | "500 · req_8f2a" | `messages.error` | error object | ⚠ add `requestId` (§6) |
| Stopped, failed, interrupted | Retry | reset in place | `POST /v1/messages/{id}/retry` (SSE) | ⚠ #5, #11 |
| `sx5f0` §6 | "No updates for 60s" + Retry | none | none | ⚠ #5 |
| F6.3–F6.4 | Connection lost, back online | `messages.status` | poll `GET /v1/messages/{id}` | ✅ |
| F2.8 | Suggested follow-up pills | none | none | ⚠ #15 |
| `Q6kwA2` §5 | Copy | browser | none | ✅ |
| same (P1) | Regenerate, pager "2 / 3" | `messages.reply_to_id` | retry-as-sibling | ⚠ #20 |
| same (P1) | 👍 / 👎 + reasons + details | `feedback` | `PUT /v1/messages/{id}/feedback` | ✅ ("trace ID": #21) |
| same | Read aloud, Share reply, Copy link, View raw JSON, Report | none | none | ⚠ #15 |

### Composer, uploads

| Screen | Shows / action | Stored in | API op / event | |
|---|---|---|---|---|
| Composer | Add file → upload | `files` (`pending` → `uploaded`) | `POST /v1/files` (presign), S3 PUT/POST, `POST /v1/files/{id}/complete` | ✅ |
| Chips | Progress, failed + retry, remove | browser; `DELETE /v1/files/{id}` | same | ✅ |
| Chips, drop overlay | "Up to 20 MB each · 10 files · PDF, images, CSV or TXT" | `capabilities.attachments` | enforced at presign | ⚠ #13 |
| Send | Text + files | `messages`, `files.message_id` | `POST /v1/sessions/{id}/messages` (SSE) | ✅ |
| Agent side | The agent reads the files (F5.4) | none | agent payload | ⚠ #4 |
| Disabled `Q6kwA2` §1, F6.8 | Offline, "unlocks automatically" | `agents.status` | `503 agent_unavailable`; poll agent | ⚠ #6 |
| F6.5 | Rate-limit countdown | none | `429` + `retryAfter` | ⚠ #15 (P2 countdown) |

### Artifacts

| Screen | Shows / action | Stored in | API op / event | |
|---|---|---|---|---|
| F3.3 | Card: title, type, version, Open | `artifacts.title`, `type`, `current_version`; `artifact` block | `artifact.*` events | ✅ |
| F3.2, `ZQvzZ`, `F9oiRc` | "Writing document… 62%" | none | none | ⚠ #12 |
| F3.4 | Panel body by version | `artifact_versions.content` / `file_id` | `GET /v1/artifacts/{id}/versions/{n}` | ✅ |
| F3.4 | "6 sources · Updated 2 min ago" | `created_at` only | none | ⚠ #12 (drop sources count) |
| F3.5 | Version list, time, note | `version`, `created_at`, `change_note` | `GET /v1/artifacts/{id}` | ✅ |
| F3.5, `oQYrz` | "v2 · You", Restore, Compare | none | none | ⚠ #12 (P2) |
| F3.7 | "Editing 'Recommendations'", live body | `artifact_versions.status = streaming` | `artifact.update` | ✅ define: each update streams a full new version (#9) |
| Panel, `SZqQD` | Copy, Download | content or presigned URL | same | ✅ native only; PDF/DOCX ⚠ #12 |
| `F9oiRc`, `OFj2k` | Generation failed / interrupted, "v3 kept" | `artifact_versions.status = incomplete` | `artifact.*` | ✅ |
| F4.7, library | PDF report, image, diagram, ZIP as artifacts | not in `artifacts.type` | none | ⚠ #12 |
| Library `g2nGvw` (P1) | Filter by type and agent, sort | `ix_artifacts_library`; agent via `sessions` | `GET /v1/artifacts?type=&agent=` | ✅ |

### Approvals, questions

| Screen | Shows / action | Stored in | API op / event | |
|---|---|---|---|---|
| F4.1 | Title, fields, warning note | `approval_requests.display`, `arguments` | `approval.requested` | ✅ |
| F4.1 | "Expires in 9:42", "Requested by … · 14:32" | `expires_at`, `agent_id`, `created_at` | same | ✅ |
| F4.1 | Approve / Deny | `status`, `decided_at` | none defined | ⚠ #1 |
| F4.4 | Deny reason | `decision_reason` | same | ⚠ #10 (no input designed) |
| F4.3, `OFj2k` | "Approved by you", "on your phone", "Ref TRX-88213" | `decided_at`, `decided_user_agent`, `tool_calls.output` | same | ✅ |
| F11.14 | Expired, "Ask again →" | `status = expired` | none | ⚠ #10 |
| `OFj2k` | Decided elsewhere updates live | `approval_requests.status` | poll | ⚠ #6 |
| `Lwlwe` §1–2, F11.7 | Question, options, single / multi, Other… | `question` block | `block.*` | ✅ define (#9) |
| same | Answer; "Answered at 09:14" (locked) | next user message with an `answer` block | `POST /v1/sessions/{id}/messages` | ✅ define (#9) |

### P1 surfaces (checked, not blocking)

| Screen | Shows / action | Stored in | API op | |
|---|---|---|---|---|
| ⌘K `B5LZKO` | Sessions by title and text with snippet, agents, artifacts | `sessions.title`, `messages.search_vector`, `artifacts.title` | `GET /v1/search?q=` | ⚠ #22 |
| Share `vBr4V`, F7.4 | Create, copy, stop sharing, "3 views" | `share_links`, `view_count` | `POST /v1/sessions/{id}/share`, `DELETE /v1/shares/{id}` | ✅ |
| same | "Include tool calls", "Only me / Anyone" | none | none | ⚠ #19 |
| Public page `q1bvDq` | Snapshot, "Shared by Israel B." | messages with `seq <= up_to_seq`, `users.name` | `GET /v1/public/shares/{slug}` (no auth) | ✅ |
| Export F7.5 | PDF / Markdown / JSON "full event log" | not stored as events | none | ⚠ #26 |
| Settings F9.1 | Export all, delete all | `files.purpose = export`; bulk delete | `POST /v1/me/export`, `DELETE /v1/sessions` | ⚠ #26 (export job) |
| Archived `HbIFz` | List, restore, "Delete forever" | `ix_sessions_archived` | `GET /v1/sessions?archived=true` | ✅ |

**Stored but never shown:** `messages.usage` beyond the token total, `tool_calls.output_file_id` (only as a file row), `refresh_tokens.user_agent`/`ip` (no "active sign-ins" screen; fine), `agents.sort_order` (catalog order, fine), `share_links.expires_at` (no expiry UI; leave unused or drop), `users.last_login_at`. None is a problem.

---

## 3. Findings

### Blockers (fix before the OpenAPI)

**1. Approval pause has no message state and no decision operation.** *Blocker.* Screens F4.1, F4.3, F4.4, F11.12–F11.14, `r5Gru`. Entities `messages.status`, `approval_requests`. While an approval waits (10 min in the design), the assistant message can only be `streaming`, which holds the one-run-per-session lock, counts against the 15-minute run cap, and dies on a deploy. There is no endpoint to approve or deny, and nothing says what happens if the user types a new message instead. The design also shows the agent replying after a deny ("Okay, I won't send it"), so a deny must reach the agent; an expiry doesn't. **Fix:** decision D1. My recommendation: the run ends when an approval is requested, with a new status `awaiting_approval`. `POST /v1/approvals/{id}/decision` re-invokes the agent with the decision and streams the continuation into the same assistant message. Sending a new message cancels a pending approval (`cancelled` already exists). The P8 spike then proves the agent side.

**2. The first send in a new session isn't idempotent.** *Blocker.* Screens F2.4 → F2.5, `N8ysh`. Entity `messages` unique `(session_id, client_message_id)`. With lazy creation (F03) there is no session yet, so a resend after `401 token_expired` can't find the first attempt and creates a second session and message. **Fix:** make the constraint `(user_id, client_message_id)` so a resend finds the existing message and its session wherever it is. One-line migration; `run.started` returns `sessionId`.

**3. Rolling deploys run two tasks; Stop and the startup sweep assume one.** *Blocker.* Screens `sx5f0` §7–8. Entity `messages`. P2 deploys with max 200 %, so for up to 5 minutes an old task is still streaming while a new one starts. The new task's startup rule ("rows still `streaming` become `interrupted`", P1) marks live replies interrupted, and a Stop that lands on the new task can't reach the run held in the old task's memory (P4 notes this for "more tasks later"; deploys make it now). **Fix:** add `messages.heartbeat_at` (written with every checkpoint and on the 15 s keep-alive timer) and `messages.cancel_requested_at`. The sweep only touches `streaming` rows with a heartbeat older than 60 s. Stop sets `cancel_requested_at`; the run task checks it at each checkpoint (≤ 2 s) and on the keep-alive tick. No shared state beyond Postgres.

**4. Agents have no way to receive attachments.** *Blocker.* Screens F5.1–F5.5, F11.3–F11.4 (F12 is P0). Entities `files`, the agent payload (D18). The payload is `{messages, input}`; there is no field for files, and nothing says how a Strands agent on AgentCore reads a private S3 object. **Fix:** decision D2. Recommendation: add `attachments: [{fileId, name, contentType, sizeBytes, url}]` to the payload, where `url` is a presigned GET valid for 15 minutes. It needs no IAM changes on agent roles and works for `http` runtimes (LangGraph) too. History turns list earlier attachments by name only.

**5. Timeout and Retry rules contradict each other.** *Blocker.* Screens `sx5f0` §6 ("No updates for 60s … Retry"), `D21ObU` ("Stream closed after 60s without a done event"), `sx5f0` §7–8 (Retry on Stopped). Docs: F08 in `PRODUCT_PLAN.md` (60 s = error, resume from `Last-Event-ID`); `SEND_MESSAGE.md` (45 s stall → poll; status table allows Retry on `stopped`, while its state diagram and P3 allow Retry only from `failed`/`interrupted`). Retrying a reply the agent is still working on returns `409 run_in_progress`, so the designed 60 s Retry can't work. **Fix:** (a) there is no "agent silent" error. After 60 s without events the message shows a soft "Still working · 1:05" note with no Retry; only the 45 s transport stall switches to polling. (b) Retry is allowed from `stopped`, `failed` and `interrupted`, and returns `409` while `streaming`. (c) No stream resume in v1 (P3). Update the state diagram, P3, F08 and the two design notes.

### Should fix (before or during the matching build slice)

**6. Cross-session presence has no API.** Screens `r5Gru`, `B6G93s` (P0 approval badge + toast), sidebar working dot, `OFj2k` "decided elsewhere", F6.8 "unlocks automatically". v1 has no cross-session event channel (F4.6 was cut for that reason), yet the P0 approval badge needs one. **Fix:** polling. `GET /v1/sessions` rows carry `isRunning` and `pendingApprovals`; the client refreshes the list every 20 s while the tab is visible, and polls the open agent every 30 s while it is offline. Both are cheap, indexed queries. The same poll makes the "Task complete" toast (F4.6, P2) nearly free: decision D4.

**7. Descriptor fields the screens show aren't stored.** Screens `uBRCZ`/F2.3/F11.2 (greeting "What are we building today?" and intro line), `ulBUE` (short description), `x05s4W`/`mN9zj` (model, region, "Strands 1.8", deployed date), `PBQLh` ("Offline since Sep 24"), F6.8 ("last seen 2 min ago"), `uBRCZ`/F8.2 ("Deploying" status). Entity `agents`. **Fix:** add `tagline` and `greeting` columns; put model, region and framework version in a `details` JSON; add `status_changed_at` and `deployed_at`. Remove "Deploying" from the design (not a status) and "Beta since …" copy. p95 latency waits for F23.

**8. Session titles: who writes them is undefined.** Screens F2.5 (title appears right after the first send), sidebar. Entity `sessions.title`. `SEND_MESSAGE.md` auto-titles "in the background" after the stream closes, so the client never learns the title, and the API has no model to call (it only invokes AgentCore). **Fix:** decision D3. Recommendation: title = the first user message trimmed to about 60 characters, set at creation; no event, no model call.

**9. Block and event schemas that P0 screens need.** Screens F2.6, F3.1, F4.5, F11.6, F11.7, F3.7, F5.5. For the OpenAPI to define:
- Every block has a stable `id` (questions are answered by reference).
- One `plan` block covers both the timeline (F2.6) and the plan card (F4.5): `steps[{id, label, status, toolCallIds?}]`. Elapsed time comes from `messages.started_at`. Drop the "about 1 min left" ETA, since agents can't estimate it. "Cancel task" is Stop.
- `thinking` carries `startedAt`/`endedAt`.
- The tool chip summary ("4 of 20 failed") comes from the agent's tool result if present, else a truncated output.
- An artifact update streams a full new version body (no diffs in v1).
- `question` has `options[{id, label, description?}]`, `multiple`, `allowOther`. The answer is an `answer` block `{questionRef: {messageId, blockId}, optionIds, text?}`. A question followed by a user message without an answer shows as skipped.
- The care callout in F5.5 is either a markdown admonition inside `text` or a small `callout` block. Recommend markdown, to keep the set closed.

**10. Approval card gaps.** Screens F4.4/F11.13 (no deny-reason input, though F10 and `decision_reason` expect one), F11.14 "Ask again →" (no operation), `Lwlwe` §4 "Confirmed with device auth" (Face ID leftover). **Fix:** add an optional reason field on Deny, or drop reasons from v1 (recommend adding it: the column exists and the agent uses it). "Ask again" pre-fills the composer, with no special API. Change the copy to "Approved by you".

**11. Retry and delete side effects are undocumented.** Entities `tool_calls`, `approval_requests`, `artifact_versions`, `messages.error`. **Fix:** Retry keeps the message id and `seq`, clears `blocks` and `error`, deletes that message's `tool_calls` (approvals cascade) and marks its unfinished artifact versions `incomplete`. Deleting a session with a running reply first stops it and cancels pending approvals; the purge job skips rows still `streaming`.

**12. Artifact screens drift outside v1.** F4.7 (PDF report as an artifact card, in a P0 flow), `F9oiRc`/`g2nGvw` (Image, Diagram, PDF and ZIP artifacts), F10.4/`SZqQD` (Download PDF/DOCX), `oQYrz`/F3.5 (versions by "You", Restore), F3.2/`ZQvzZ` (percent progress), F3.4 ("6 sources"). Entity `artifacts.type` (document, code, html, table). **Fix:** v1 artifacts are the four types. Generated PDFs, ZIPs and images are `file` blocks (F22, P1), so F4.7 should show a File Card. Downloads are native format only. The version menu lists agent versions without Restore. Progress is indeterminate with a section label. Drop the sources count.

**13. Attachment limits and storage keys.** Screens `Q6kwA2` §1 ("PDF, images, CSV or TXT · up to 20 MB each · 10 files max", fixed copy), F11.4, `Q6kwA2` §4 ("4 pages", "214 rows"). Docs: F12 says images and PDFs; F02 says per-agent `{types, maxMB}`. **Fix:** global ceiling of 20 MB per file, 10 per message, types `pdf, png, jpeg, webp, gif, csv, txt`. An agent can narrow these in `capabilities.attachments`, and the copy is rendered from them. Drop page and row counts from the design, or add `files.metadata` later. Use S3 keys of the form `u/{userId}/…`; this is cheap now and costly to change once there are more users.

**14. The refresh cookie path breaks with `/v1`.** D8 sets `Path=/auth`; the API will serve `/v1/auth/*`, so the browser would never send the cookie. **Fix:** `Path=/v1/auth` in D8 and the sequence diagram.

**15. P0 screens show features outside v1.** Suggested follow-up pills (F2.8, F8.1, `Lwlwe` §6), "Was this helpful?" (`Lwlwe` §6), thumbs (P1, but in every Message Actions bar), Read aloud, the More menu (Share reply, Copy link, View raw JSON, Report), mic/Dictate and "Connect tool · Soon" in the composer, the "Always allow" permission prompt (`Lwlwe` §5, and the F9.6 toggle), "Notify me" (F4.5, `r5Gru`), rate-limit countdown (F6.5), session too long (F6.6–F6.7), the edit-message pager, and Mermaid diagrams (`IVLvU` §7, in no scope list). None has a block, table or endpoint. **Fix:** hide them in v1 builds and label them in the design. D4 lets you pull the cheap ones forward.

**16. Stale docs that are still the test basis.** `PRODUCT_PLAN.md` F01 (CLI → DynamoDB), F08 (Last-Event-ID, 60 s), F13 (Cognito), F14 (`AgentApi`, `BACKEND_CONTRACT.md`), and the "resume" success metric; `SEND_MESSAGE.md` paths `/runs/{runId}/stop` (becomes `/v1/messages/{id}/stop`); no `logout` or `me` operations anywhere. **Fix:** update these when the fixes are applied; OpenAPI becomes the contract F14 refers to.

**17. IDs and timings shown in the design don't match the model.** `E3lQz` shows `ses_7f3a91`; `vBr4V`/F7.4 shows `agenthub.app/s/7f3a91-kq2` (short slug, unconfirmed domain, Q2); toasts say "undo in 8s" against a 10 s undo; `yzVIz` says toasts auto-dismiss after 5 s. **Fix:** show the first 8 characters of the UUID; show a 22+ character share slug on `app.<domain>`; the undo toast lasts 10 s.

**18. P0 error states not designed.** Sidebar fails to load; artifact panel or version fails to load; approval decision request fails (the card must stay pending and let you retry); Google sign-in popup closed or failed. **Fix:** four small states for the design session; the API side is just the common error format.

### Later

**19. Share options (P1).** `vBr4V`, F7.4 show "Include tool calls", "Only me / Anyone with the link", and "uploaded files and tool inputs are left out unless you include them". `share_links` has no options. Add `options jsonb` and a unique partial index for one active link per session when F18 is built; shared pages leave out `thinking` by default. The block references already freeze artifact versions, so the snapshot holds.

**20. Regenerate siblings (P1).** `Q6kwA2` §5 pager "2 / 3". `reply_to_id` allows siblings, but nothing marks which one is shown or sent as history (D18). Add `messages.superseded_at` with F20, and allow Regenerate on the latest reply only, so `seq` stays linear.

**21. Feedback extras (P1).** The popover says "Sent with this session's trace ID" but no trace id is stored; add `messages.trace_id` if AgentCore exposes one, or drop the line.

**22. Search details (P1).** `B5LZKO` shows artifact title matches and "6 sessions mention 'auth'" per agent; archived sessions are excluded unless included. Add artifact title search (sequential scan is fine); drop the per-agent mention count.

**23. Counts.** Messages per session (Archived, mobile row menu) and per agent (agent detail) are computed. Drop the per-agent message count, and add a counter column only if it gets slow.

**24. Leftover names.** The design file is still `fleet_dev.pen`. The design uses Bank Agent and Home Ops throughout, while the plan and `architecture.mmd` say Ledger, Scenario Agent, and Home Ops cut. The `IVLvU` diagram shows "Next.js" and "LangGraph · Lambda". F1.8 shows Travel Planner as Strands/AgentCore. "Mock API" appears in onboarding (P2). The product name "Agent Hub" is consistent everywhere else. Rename sample agents when screens are next touched; renaming the `.pen` file is optional.

**25. Multi-user choices that would be costly later.** Almost all are already safe: `user_id` is on every row, composite keys are in place, agents are global with `agent_access` planned. Three to keep in mind: S3 key prefix per user (#13), a `users.role` for who may invite users and register agents (add with the invite flow), and "Always allow" tool rules, which are per user and per agent (P2 table).

**26. Export (P1).** The export dialog offers PDF and a JSON "full event log, including SSE events". Events aren't stored; JSON export means messages with blocks. v1 of F27 is Markdown only, and export-all needs a background job, decided with F24.

**27. ER diagram detail.** `er.mmd` omits `artifacts.created_message_id` and `artifact_versions.message_id` (links to `messages`). Add them when the diagram is next redrawn.

---

## 4. Message and block coverage

| Block / state | Rendered on | Data home | Stream event | Status |
|---|---|---|---|---|
| text | everywhere | `blocks[text]` | `block.start/delta/end` | ✅ |
| thinking | `sx5f0` §1, F2.6 | `blocks[thinking]` | same | ✅ times (#9) |
| tool step | F2.6, `wtDYF` | `blocks[tool]` → `tool_calls` | `tool.started/completed` | ✅ |
| plan / progress | F2.6, F4.5, F11.6 | `blocks[plan]` | `block.*` | ⚠ #9 |
| artifact + versions | F3.x, `F9oiRc` | `blocks[artifact]` → `artifacts`, `artifact_versions` | `artifact.created/delta/completed` | ✅ (#12 scope) |
| question + answer | `Lwlwe`, F11.7 | `blocks[question]`, next message `blocks[answer]` | `block.*` | ✅ define (#9) |
| approval + decision | F4.x, F11.12–14 | `blocks[approval]` → `approval_requests` | `approval.requested`; decision op | ⚠ #1 |
| stopped / failed / interrupted | `sx5f0` §8 | `messages.status`, `error` | `run.stopped/failed/completed` | ✅ (#5 rules) |
| regenerate | `Q6kwA2` §5 (P1) | `reply_to_id` | retry-as-sibling | ⚠ #20 |
| edit and resend | `Q6kwA2` §4 (P2) | none | none | P2, not modelled on purpose |
| feedback | `Q6kwA2` §5 (P1) | `feedback` | REST | ✅ |
| attachments | F5.x | `files` | REST (presign) | ⚠ #4 |
| citation, chart, image, file, form | `IVLvU`, `Lwlwe` §3 (P1) | reserved block types | `block.*` | P1 |
| suggestions, callout, diagram | F2.8, F5.5, `IVLvU` | none | none | ⚠ #9, #15 |

## 5. Flow check against the sequence diagrams

| Flow | Diagram covers it? | Gap |
|---|---|---|
| Sign-in, session check on load | ✅ normal path | Logout and `GET /v1/me` missing (#16); cookie path (#14) |
| Expired access token → refresh → resend | ✅ failures | Resend before the session exists duplicates it (#2) |
| Refresh expired / reused | ✅ | none |
| New session + first message | ✅ (note on step 13) | Title timing (#8) |
| Stop | ✅ | Wrong task during deploys (#3); Retry after Stop (#5) |
| Retry | Rule 8 only | Side effects (#11) |
| Disconnect, reconnect, poll | ✅ | 60 s error in design (#5) |
| Agent offline (503) | ✅ | Live unlock needs polling (#6) |
| Agent error / unreachable | ✅ | Error needs `requestId` (§6) |
| Deploy mid-reply | ✅ | Two tasks (#3) |
| File upload | ✗ not drawn | Presign → PUT → complete; agent access (#4) |
| Artifact download | ✗ not drawn | Short-lived URL from `GET /v1/artifacts/{id}/versions/{n}`; HTML origin still open (D7) |
| Approval request → decision → continue | ✗ not drawn | #1 |
| Share link | ✗ not drawn (P1) | #19 |

Recommend adding one small sequence diagram for upload + approval once D1 and D2 are decided.

## 6. Non-functional defaults for the API (picked; say if you disagree)

| Topic | Default |
|---|---|
| **Error format** | RFC 9457 `application/problem+json`: `{type, title, status, detail, code, requestId, retryable, retryAfter?}`. The SSE `run.failed` event and `messages.error` carry the same object. Every response has `X-Request-Id`. |
| **Pagination** | Opaque `cursor` + `limit` (default 50, max 100) on sessions, artifacts, search. Messages page backwards by `seq` (`?before=<seq>&limit=50`), returned oldest-first within a page. |
| **Search** | P1. `GET /v1/search?q=&agent=&includeArchived=false`; Postgres full-text on messages, title match on sessions and artifacts; snippets from `ts_headline`. |
| **Rate limits** | None per request in v1 (single user). Cost guard: at most 3 concurrent runs per user (`429 too_many_runs`) on top of one per session. AgentCore throttling becomes `run.failed` with `code: rate_limited, retryAfter`. |
| **Upload limits** | 20 MB per file, 10 per message, `pdf png jpeg webp gif csv txt`; enforced with a presigned POST `content-length-range` and checked again at `complete` (HeadObject). Unsent uploads are deleted after 24 h. Max message text 32,000 characters (`422 message_too_long`). |
| **Idempotency** | Send: `clientMessageId`, unique per user (#2). Approval decision: conditional update; the same decision again returns 200, a different one `409 approval_not_pending`. Stop: 202, and a no-op if already ended. Retry: `409` unless `stopped`/`failed`/`interrupted`. Share create returns the active link. Delete and `complete` are idempotent. |
| **Ordering** | `seq` per session is the only order. SSE events have `id: <messageId>:<n>` (n increases per run) and carry `blockId`; the client applies them in order. After any gap, REST state wins. |
| **In-flight during deploy** | P2 draining plus #3. Replies longer than the 120 s stop timeout end `interrupted` with Retry. |
| **Formats** | UUID strings; RFC 3339 UTC timestamps; camelCase JSON. Agents are addressed by `slug` in URLs and the API (slugs never change; a renamed agent gets a new row). |
| **Agent status in v1** | Set by hand with the CLI; no automatic flipping. The client polls as in #6. Computed status stays F23 (P1). |

---

## 7. Decisions only you can make

**D1. How a run pauses for approval** (#1). **Answer: A** → ARCHITECTURE D19.
- **A. The run ends; the decision continues it (recommended).** Status `awaiting_approval`; `POST /v1/approvals/{id}/decision` re-invokes the agent and streams into the same message; a new message cancels the approval. Stateless (D18), survives deploys, frees the session lock and the 15-min cap.
- B. Hold the run open until decided. Simplest data model, but the composer stays locked, the wait counts against the 15-min cap, and a deploy kills it.
- C. Like A, but the continuation is a new assistant message. Fewer rules, but the reply splits in two, unlike F4.3.

**D2. How agents get attached files** (#4). **Answer: A** → D20.
- **A. Presigned GET URLs in the payload, valid 15 min (recommended).** No IAM coupling; works for any runtime.
- B. S3 URIs, with each agent role granted read on the uploads prefix. No expiry issues, but IAM work per agent and AWS-only.
- C. Inline base64 in the payload. No S3 access at all, but payload size limits bite with 20 MB files.

**D3. Session titles** (#8). **Answer: A** → D21.
- **A. First user message, trimmed, at creation (recommended).** Instant, free, no event.
- B. The API asks a small Bedrock model after the first reply, and emits `session.updated`. Nicer titles; adds a model call, IAM and cost.
- C. Each agent returns a title in its final event. Every agent must implement it.

**D4. Which cheap extras come into v1?** (#6, #15). **Answer: task-complete toast and 👍 / 👎 feedback**; suggestion pills and Regenerate stay P1 → D22, `PRODUCT_PLAN.md` F20 and §3. Each costs a day or less:
- Task-complete toast anywhere (F4.6): free once the sidebar polls (#6).
- 👍 / 👎 feedback (F20 half): the table already exists.
- Suggested follow-up pills: needs a `suggestions` block and agent support.
- Regenerate with pager (F20 other half): needs #20.

My recommendation: take the first two, leave the last two in P1.

---

## 8. What changed

Applied 2026-09-29 after the owner's answers. "Design session" items came from a design-session prompt (`design/ALIGNMENT_FIXES.md`, removed after use; see commit `63b0ca7`), run in a separate design session (`BUILD_PLAN.md`) and committed as `3d81fbe` (design) and `b7baa0f` (screen inventory in `PRODUCT_PLAN.md`).

| # | Finding | Outcome | Where |
|---|---|---|---|
| 1 | Approval pause | ✅ Fixed: `awaiting_approval` status, decision endpoint, new message cancels, deny re-invokes, expiry doesn't; one open reply per session enforced in the DB | ARCHITECTURE D19, P8; `SEND_MESSAGE.md` rules 2, 12; `approval-and-upload.mmd`; `0002`; test `test_reply_waiting_for_approval_blocks_another_open_reply` |
| 2 | Idempotent first send | ✅ Fixed: unique `(user_id, client_message_id)` | `0002`; `SEND_MESSAGE.md` rule 4; both sequence diagrams; test `test_send_is_idempotent_across_a_users_sessions` |
| 3 | Two tasks during deploys | ✅ Fixed: `heartbeat_at` sweep (60 s stale), Stop via `cancel_requested_at` | ARCHITECTURE D11, P1, P4; `SEND_MESSAGE.md` rules 6, 7, 13 and timers; failures diagram; `0002` |
| 4 | Attachments to agents | ✅ Fixed: signed GET URLs (15 min) in `attachments` | ARCHITECTURE D18, D20; `approval-and-upload.mmd` |
| 5 | Timeout and Retry rules | ✅ Fixed in docs: no "agent silent" error, Retry from stopped / failed / interrupted, no resume | ARCHITECTURE P3; `SEND_MESSAGE.md` rules 8, 9; `PRODUCT_PLAN.md` F08 and metrics. Design session §2 |
| 6 | Cross-session presence | ✅ Fixed: polling | ARCHITECTURE D22; `SEND_MESSAGE.md` timers |
| 7 | Descriptor fields | ✅ Schema fixed (`tagline`, `greeting`, `details`, `status_changed_at`, `deployed_at`) | `0002`, `DATA_MODEL.md`, `er.mmd`. Design session §4 ("Deploying", "Beta since") |
| 8 | Session titles | ✅ Fixed: first message at creation | ARCHITECTURE D21; `SEND_MESSAGE.md` rule 11; `PRODUCT_PLAN.md` F06 |
| 9 | Block and event schemas | ➡ Input to the OpenAPI (step 5); answer shape recorded | `DATA_MODEL.md` (answer block); design session §3 (plan ETA, "Stop") |
| 10 | Approval card gaps | ✅ Design session §1 (deny reason, cancelled state, copy); "Ask again" prefills the composer | `approval-and-upload.mmd` |
| 11 | Retry and delete side effects | ✅ Documented | `SEND_MESSAGE.md` rules 8, 14; `DATA_MODEL.md` defaults |
| 12 | Artifact drift | ✅ Design session §3, §5 | none needed in the model |
| 13 | Attachment limits, S3 keys | ✅ Limits and key prefix decided | ARCHITECTURE D7, D23; `PRODUCT_PLAN.md` F12; design session §6 |
| 14 | Cookie path | ✅ Fixed: `Path=/v1/auth` | ARCHITECTURE D8; `send-message.mmd` |
| 15 | Out-of-v1 features on P0 screens | ✅ Scope set (D4); ➡ design session §7 | `PRODUCT_PLAN.md` §3, F20 |
| 16 | Stale docs | ✅ Fixed | `PRODUCT_PLAN.md` F01, F06, F08, F10, F12, F13, F14, metrics; paths under `/v1` in all docs and diagrams |
| 17 | IDs and timings in the design | ✅ Design session §2, §8 | none |
| 18 | Missing P0 error states | ✅ Design session §9 | none |
| 19–23, 25–26 | Later items | ⏸ Deferred to their feature slices | as listed in §3 |
| 24 | Leftover names | ✅ Design session §10 (optional); `fleet_dev.pen` name kept | none |
| 27 | ER detail | ✅ Fixed: message → artifact links drawn | `er.mmd` |

**Consistency check after the edits.** The design is consistent with the data model and the stream: every P0 screen field in §2 now has a column, a computed value or a planned API operation, except the design-only items above, which remove or relabel things rather than add data. A search of `docs/`, `api/` and the diagrams finds no remaining unprefixed paths (`/auth`, `/sessions`), no `runs/{runId}` stop path, no `uq_messages_streaming_per_session` and no stale board id. Schema: `alembic upgrade head`, `downgrade 0001`, `upgrade head` and `alembic check` (no drift) pass on Postgres 17, and all 14 schema tests pass.

**Design check.** A text scan of `fleet_dev.pen` after the design session finds none of the removed copy ("Deploying", "about 1 min left", "undo in 8s", "Notify me", "Confirmed with device auth", "Beta since"), and finds the new states: Approval Card / Cancelled, deny reason, decision failed, "Still working", sidebar and artifact load failures (`P3wQ4`, `p0Nx1`), sign-in failed (`G7FDcP`) and the revoked share page. "6 sources" remains only on the parked P2 compare screens (`F8d7U`, F3.8), which is fine. This checked text, not visuals.

**Not verified:** the Strands resume-after-approval behaviour (D19) is still the P8 spike.

## 9. Change log

| Date | Change |
|---|---|
| 2026-09-29 | First draft. No other documents, diagrams or screens edited. |
| 2026-09-29 | Owner answered D1 A, D2 A, D3 A, D4 toast + feedback. Fixes applied (§8); verdict now ready for OpenAPI. |
| 2026-09-29 | Design fixes applied in `fleet_dev.pen` by the design session; §8 updated. |
