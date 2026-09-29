# Agent Hub: product plan

| | |
|---|---|
| Status | Draft v1 for owner review |
| Date | 2026-09-28 |
| Owner | Israel B. (product, engineering, approver) |
| Inputs | `design/fleet_dev.pen` as pushed to this repo on 2026-09-28 (222 frames, 85 components, 74 flow screens), the project brief |

This is the plan to build from. It makes decisions; where a decision rests on something I don't know, it is marked **[A#]** (assumption) and collected in §7. Open questions that block the build are ranked at the end (§11).

**Two corrections to the brief before anything else:**
- **There is no coded prototype.** The repo has only the design file and its index. The "working coded prototype" in the brief doesn't exist yet, which changes decision B (§10).
- **Mobile screens do exist.** There are 9 of them: 3 artifact screens and the 6 in Flow 10. They are incomplete, and three have a broken composer (§9), but the work starts from 9 screens, not zero.

---

## 1. Vision, users, problem (one page)

**Vision.** One calm, fast place to talk to every agent I build. A new agent shows up in the catalog the day it's deployed, with no UI work. It handles everything an agent can produce: streamed answers, visible tool work, documents and code, and requests for my approval.

**The problem.** Every agent I build today ends up with its own throwaway front end [A1]: the Strands CLI, the AgentCore console test pane, curl, a quick Streamlit page. That has four costs:
1. **UI work per agent.** Each new agent needs new interface work, or it gets demoed through a terminal.
2. **No memory.** There's no history across agents, so I can't come back to yesterday's session.
3. **Rich output is unreadable.** Tool calls, plans, documents and approvals show up as raw JSON or not at all.
4. **Weak portfolio.** Showing agents to someone else looks like a dev environment, not a product.

**Target users**

| Priority | User | What they need | v1 stance |
|---|---|---|---|
| Primary | **You, the builder and daily user.** AI engineer and team lead who ships Strands agents on AgentCore. | Use your agents daily, test new ones, and come back to past work. | Everything in v1 is built for you. |
| Secondary | **Portfolio audience:** hiring managers, clients, meetup and demo audiences. | See what the agents can do, often on a phone, without an account. | They see agents through **your live demos** and **read-only shared session links** (P1). They cannot chat. [A2] |
| Later | **Teammates** | Use shared agents with their own history. | Out of v1. This needs multi-user auth and data separation (P2). |

**Pushback on the requirements.** "Single user" and "portfolio" pull against each other: a portfolio exists to be seen by others. If strangers can chat with your agents, you take on cost, abuse and data-safety work (quotas, guest identity, demo-safe tools) that roughly doubles the auth and backend scope. I recommend v1 stays owner-only for chat, and others see the work through read-only share links and recorded demos. Live guest chat moves to P2, behind quotas, and only for agents marked demo-safe.

**Why now.** You're about to build agents one by one. Build the hub first and every agent after the first gets a finished UI for free; build it later and each agent adds another throwaway UI to retire.

---

## 2. Jobs to be done and key journeys

**Jobs**

| # | When I… | I want to… | So that… |
|---|---|---|---|
| J1 | finish deploying a new agent | have it appear in the hub without touching the UI | shipping an agent is the only work |
| J2 | have a task for a specific agent | open it and start a fresh session in two clicks or fewer | I get to the work without friction |
| J3 | am waiting on an agent | see what it's doing (thinking, tools, plan, progress) and stop it | I trust it, and I can step in early |
| J4 | get a big result (a document, code, a table or an app) | read, copy, download it and look at earlier versions beside the chat | the output is usable, not buried in a transcript |
| J5 | an agent wants to do something consequential | approve or deny from what the backend says it will do, not what the model claims | nothing happens behind my back |
| J6 | come back later | find any past session by agent, date or text and continue | the hub becomes my working memory |
| J7 | show my work to someone | share a read-only session or demo it live on any screen size | the portfolio sells itself |

**Key journeys** (these map to the prototype flows in `design/INDEX.md`)

| Journey | Job | Flow | Priority |
|---|---|---|---|
| Pick an agent → new session → streamed reply with tool calls | J2, J3 | F2 | P0 |
| Ask for work → artifact created → open in panel → revise → view an older version | J4 | F3.1–F3.5 | P0 (editing and compare: P2) |
| Agent asks for approval → approve or deny → result, including expiry | J5 | F4.1, F4.3, F4.4 | P0 (Face ID: P2) |
| Attach files → agent reads them → answer | J4 | F5.1–F5.5 | P0 (voice: P2) |
| Something fails → clear state → recover without losing text | J3 | F6 | P0 (the core set; see F08) |
| Switch agent from anywhere → fresh session; reopen a past one | J2, J6 | F8 | P0 (⌘J: P1) |
| Find and organise: ⌘K, rename, delete with undo, archive, library | J6 | F7 | Rename and delete P0; the rest P1 |
| Register a new agent → appears in catalog | J1 | F1 in the design | P0 through the registry CLI; the UI flow is P2 (see §3) |
| Share a session read-only; demo on a phone | J7 | F10 plus a new share view | P1 |

---

## 3. Scope: MVP vs later

**v1 (MVP) definition.** You use Agent Hub every day with three real agents: Research Analyst, Ledger and the Scenario Agent (see §10A). Adding a fourth agent needs zero front-end changes. It works well on desktop and holds up on mobile web.

**Deliberately cut from MVP (these move to P1 or P2)**

| Cut | Designed in | Why |
|---|---|---|
| Add / Edit agent UI with connection test (F1.3–F1.7, F9.6) | Yes | Agents are data, and data can be registered with a CLI (`hub agents add agent.yaml`) in minutes. The UI flow needs write APIs, ARN validation and IAM checks, all for one user who is comfortable in a terminal. P2. |
| Document editing in the artifact panel, formatting bar | Yes | A rich-text editor is a product on its own. In v1 the agent revises the document from chat, which is the core loop anyway. P2. |
| Version compare (diff) | Yes | Viewing older versions covers about 90% of the need. P2. |
| Code "Run" console, HTML device switcher, spreadsheet sheet tabs | Yes | Each needs its own runtime or UI. v1 gets code view, a sandboxed HTML preview, and a CSV/table view. P2. |
| Voice dictation and read-aloud | Yes | Nice, not core. Browser speech APIs are uneven. P2. |
| Face ID / passkey step-up for approvals (F4.2) | Yes | An in-app approval is enough while the bank is synthetic. The design copy also implies a real bank integration ("sent to your bank"), which we are not building. P2, and only if real money ever becomes real. |
| Message edit and branching | Yes | Turns the transcript into a tree and complicates every backend. Regenerate with a version pager (P1) covers most of it. P2. |
| Session too long → auto-summary new session (F6.6–6.7) | Yes | Depends on agent memory strategy. Show a clear error and a "New session" action in v1. P2. |
| Background task toasts "anywhere" (F4.6) | Yes | Needs a cross-session event channel. In v1 the sidebar shows a working dot on the session instead. P2. |
| Rate-limit countdown | Yes | A generic "try again" with the backend's `retryAfter` is enough. |
| Dark mode | Only the settings picker | No dark tokens or dark screens exist. Shipping it undesigned produces bad contrast. Hide it in v1; P2. |
| Onboarding tips, shortcuts overlay | Yes | Single expert user. P2. |

**Would not build at all**

- **Native iOS / Android apps.** Responsive web, installable as a PWA, covers phone demos and approvals.
- **An agent builder, prompt editor or tool configuration in the UI.** Agents are built in code. The hub is a client, not a platform console.
- **Real money movement, real bank connections or real health records (PHI).** Bank and health agents run on synthetic data. Otherwise PCI / HIPAA-class obligations land on a portfolio project.
- **Per-agent custom renderers or a plugin system.** That breaks "agents are data". Agents pick from a closed set of content types (§5), and a new type is a platform release, not an agent release.
- **A model picker.** The agent owns its model.
- **Team or org admin, billing, real-time co-editing.**

---

## 4. Feature list (prioritised, with acceptance criteria)

- **P0:** required for v1.
- **P1:** follows within about four weeks of v1, some pulled into M4 if time allows.
- **P2:** later, and only if usage asks for it.

"AC" means acceptance criteria. All ACs must pass against the mock and against the real backend.

### P0

| ID | Feature | Acceptance criteria |
|---|---|---|
| F01 | **Agent registry and catalog** | `GET /agents` drives the catalog; there is no agent list in front-end code. Registering a new agent descriptor (CLI → DynamoDB) makes it appear on reload with its icon, colours, description and status. Catalog search appears only when there are more than 8 agents. Loading, empty and error states exist. |
| F02 | **Descriptor-driven UI** | Each agent descriptor declares `icon`, `color`, `starters[]`, `disclaimer`, `capabilities` (`attachments: {types, maxMB}`, `artifacts`, `approvals`, `questions`), `tools[]` (`name`, `description`, `requiresApproval`), `stage` (`beta`/`stable`) and `runtime` (`agentcore`/`http`). The UI hides what an agent doesn't support: no "+" button without attachments. The disclaimer under the composer is the agent's own text. |
| F03 | **New session, lazy creation** | `/agents/:id` shows starters and the composer. No session exists until the first send. The server creates it and returns an id, and the URL becomes `/agents/:id/:sessionId` without a reload. If the first send fails, no session is created, the draft is kept, and Retry works. |
| F04 | **Streaming chat** | Tokens render progressively with no layout jumps. The view auto-scrolls only when already at the bottom; otherwise "Jump to latest" appears. Stop (button or Esc) ends generation, keeps the partial reply and marks it "Stopped". Markdown covers headings, lists, tables, inline and fenced code with a copy button, and links. Each message has Copy and a timestamp. |
| F05 | **Agent activity** | `thinking` events render as a collapsed "Thought for Ns" row; if the agent emits none, the row doesn't appear. Tool calls render as chips (name, short summary, duration, state) that expand to input and output. `plan`/`progress` events render the Plan Card with steps. All of these persist and look the same after reload. |
| F06 | **Session history** | The sidebar lists the current agent's sessions, grouped Today / Yesterday / Previous 7 days / Earlier, newest first. A new session appears at the top the moment it's created (this fixes the design bug). Sessions are auto-titled by the backend after the first reply. Rename inline. Delete removes the session immediately with a 10-second Undo toast and no dialog. Reopening a session restores its full transcript, including tool calls, artifacts and approvals. |
| F07 | **Agent switching** | The Agent Switcher in the sidebar lists all agents with status. Choosing one opens a fresh session for it. The header always shows agent, status and session title. Offline agents can be selected but are read-only. |
| F08 | **Errors and recovery** | Six states each have their own copy and next action: reply failed (Retry resends the same message); stream dropped (the partial reply is kept, Retry, and the stream resumes from the last event id if the backend supports it); connection lost (banner, then "Back online"); agent offline (composer disabled, past sessions readable); agent or session not found (404 view); auth expired (re-login keeps the draft). No spinner can hang: 60 s without an event is an error. |
| F09 | **Artifacts v1** | `artifact.create` and `artifact.update` events create a versioned artifact. A card in the chat opens the side panel, split 50/50; on mobile it opens as a full-screen sheet. Supported types: **document** (markdown, serif rendering), **code** (syntax highlight, line numbers), **html** (sandboxed iframe on a separate origin, no `allow-same-origin`), **table** (CSV/JSON with sticky header, sortable). The version menu lists versions, and choosing one shows that version read-only. Copy, Download (native format), and Expand are available. |
| F10 | **Approvals (human in the loop)** | When a tool with `requiresApproval` is called, the backend pauses the run and emits `approval.request`. The card is rendered from backend-validated tool arguments, not model prose. It supports pending, approved, denied (with an optional reason sent to the agent) and expired, and shows a visible countdown. The approval survives reload and shows on the session in the sidebar. Double-submit is impossible. The backend refuses to execute a denied or expired call. There is an audit record per decision. |
| F11 | **Agent questions** | `question` events render as quick replies or single / multiple choice. Answering sends a structured reply. Once answered, the question shows its answer and becomes read-only. |
| F12 | **Attachments** | Images and PDFs can be added by the "+" button, drag and drop, or paste. They upload to S3 through a presigned URL and show progress, failure with retry, and "not allowed" states, enforcing the type and size limits in the descriptor. Sent attachments render in the user message and can be downloaded. |
| F13 | **Auth** | Cognito, single user. `useAuth()` is the only auth surface in the UI. Every route and API call is authenticated. No AWS credentials reach the browser; the backend calls AgentCore with its own IAM role. |
| F14 | **AgentApi and the contract** | One `AgentApi` interface with two implementations: a mock (localStorage, scripted scenarios) and an HTTP/SSE client, switched by an env var. `docs/BACKEND_CONTRACT.md` documents endpoints, JSON shapes and every SSE event. A Playwright suite runs every Scenario Agent script against the mock in CI. |
| F15 | **Mobile web, core flows** | At 390 px width, these work: catalog, new session, chat with streaming, sessions drawer, artifact sheet, approval. The composer stays above the keyboard. Tap targets are at least 44 px. No horizontal scroll. |

### P1

| ID | Feature | Acceptance criteria |
|---|---|---|
| F16 | ⌘K palette | Searches session titles and message text across all agents plus agents by name. Arrow keys and Enter work. The top result opens in 1 keystroke. Empty and no-result states exist. |
| F17 | Pin and archive | Pinned sessions show in their own section at the top. Archived sessions are hidden from the sidebar and ⌘K by default and shown in an Archived view with Restore. |
| F18 | Read-only share link | "Share" creates an unguessable link to a frozen snapshot of the session and its artifacts. Viewers don't need to log in and can't send messages. The link can be revoked, after which it returns 404. It renders well on mobile. |
| F19 | Agent detail page | `/agents/:id/about` shows the descriptor: capabilities with "Asks first" flags, starters, runtime details and recent sessions. |
| F20 | Feedback and regenerate | 👍 / 👎 (with a reason) is stored per message and exportable as an eval signal. Regenerate creates a sibling reply, with a pager between versions (1/2). |
| F21 | Structured forms | A `form` event renders labelled fields with validation. Submitting sends structured JSON; afterwards the form becomes a read-only summary. |
| F22 | Rich reply content | Citations as chips, with a source preview and a Sources list. Images in replies with a lightbox. Charts from a declarative spec (line and bar, one library; see `docs/CHART_SPEC.md`). Download for generated files. |
| F23 | Computed status | The backend health check sets Online / Degraded / Offline from probes and error rate. "Beta" becomes a separate stage tag, not a status (see §9). |
| F24 | Settings and data | Default agent, export all data (ZIP of JSON and files), and delete all (type DELETE to confirm). |
| F25 | Artifacts library | All artifacts across sessions, filterable by agent and type, each opening in its session context. |
| F26 | LangGraph adapter | One LangGraph agent works through the same contract with no UI changes (proves J1 across frameworks). |
| F27 | Export session | Export a session as Markdown. PDF comes later. |

### P2
Voice; artifact editing; version compare; code run console; HTML device switcher; Add / Edit agent UI; dark mode; passkey step-up; web push; message edit and branching; auto-summary continuation; background task toasts; guest live-chat demo mode with quotas; teams; onboarding.

---

## 5. UX principles, information architecture, screens

### Principles (each one settles real disputes)
1. **Always know where you are.** Agent, status and session title are always in the header. The agent's colour is an identity cue, used only on its icon tile, never as decoration.
2. **The transcript is the record.** Everything the agent did (tools, approvals, questions, artifacts) is recorded inline, in order, and looks the same after reload or on another device.
3. **Calm streaming.** No layout jumps, no auto-scroll while the user is reading, and progressive disclosure: thinking and tool detail are collapsed by default.
4. **Control before speed.** Consequential actions wait for explicit approval, showing data the backend validated. Destructive actions in the hub itself use undo, not confirmation dialogs; the one exception is Delete all.
5. **Capabilities, not special cases.** The UI adapts to what the descriptor declares. There is no `if (agent.id === 'bank')` anywhere.
6. **A closed set of content types.** Text, code, table, chart, image, file, citation, question, form, approval, artifact (document / code / html / table). New agents reuse these renderers.
7. **Keyboard-first on desktop, thumb-first on mobile.** Every flow can be completed with the keyboard alone, and on mobile, with one thumb.

### Information architecture

```
/                                   Catalog (all agents, continue where you left off)
/agents/:agentId                    New session (starters, composer)
/agents/:agentId/:sessionId         Session (chat + optional artifact panel ?artifact=:id&v=:n)
/agents/:agentId/about              Agent detail (P1)
/artifacts                          Artifacts library (P1)
/archived                           Archived sessions (P1)
/settings                           Settings (P1)
/s/:shareId                         Public read-only shared session (P1, no auth)
⌘K                                  Global overlay, not a route

Sidebar (desktop; drawer on mobile)
├─ Brand · collapse
├─ Agent Switcher (current agent, status)
├─ New session  ⌘⇧O
├─ Search  ⌘K
├─ Pinned (P1)
├─ Sessions for current agent: Today / Yesterday / Previous 7 days / Earlier
└─ Footer: user · Artifacts · Archived · Settings
```

Change from the original design (done 2026-09-29): "All agents", "Artifacts" and "Archived" moved out of the main nav into footer icons in the `Sidebar Footer` component (and ⌘K). This applies to the desktop sidebar and the mobile drawer. See §9.

### Screen inventory

Status key:
- **✅** designed and usable as is.
- **🔧** designed, but needs the fix noted.
- **➕** missing; must be designed or specified before build.

| Surface | Desktop | Mobile (390) | Priority |
|---|---|---|---|
| Catalog | ✅ `PBQLh` | ✅ F10.1 `UK1JP` (filter chips removed, §9 item 7) | P0 |
| Catalog: loading / error | ✅ error `Jchi9` (loading: skeleton on the States board) | ✅ loading F11.1 `EP1MN`, error `sMh7q` | P0 |
| Catalog: empty (no agents) | ✅ `j8NhJ`: "How to register an agent", search and sort hidden | ✅ `iX1f6` | P0 |
| New session (starters) | ✅ `uBRCZ` | ✅ F11.2 `HgtnP` | P0 |
| Chat: streaming, tools, plan, thinking | ✅ `wtDYF`, F2.5–F2.8 | ✅ F11.5 `DNypg`, plan F11.6 `DuSPU` | P0 |
| Chat: all failure states | ✅ "Agent Working & Failure States" board | ✅ reconnecting F11.8 `e6XAO`, reply failed F11.9 `vBCdH` | P0 |
| Chat: auth expired, draft kept | ✅ `jlDzd` | ✅ `xBrZk` | P0 |
| Composer states (attachments, disabled, drag-drop) | ✅ | ✅ `Composer / Mobile` `OUcXN`; keyboard open F11.3 `w1IZ2`; disabled F11.11 | P0 |
| Sessions sidebar / drawer | ✅ | ✅ F10.5 `i46aRN` | P0 |
| Sessions: loading skeleton | ✅ States board | ✅ F11.15 `JgaZ9` | P0 |
| Delete + undo | ✅ no dialog: F7.6 `Ba2LD`, F7.7 `ZX9nG` | ✅ long-press F11.16 `G6iHV`, swipe F11.17 `mepQO`, undo F11.18 `XRu2z` | P0 |
| Agent switcher | ✅ F8.2 | ✅ bottom sheet F11.10 `wE4kz` | P0 |
| Agent offline / not found | ✅ States board | ✅ offline F11.11 `t4QWfb`, agent not found `V97EP` | P0 |
| Artifact panel: document / code / html / table | ✅ `oQYrz`, `fUZV4`, `j2uc1W`, `LrhPn` (trim to v1 scope) | ✅ sheet `KXQcB`, chat `JLUHx` | P0 |
| Artifact: streaming while generating | ✅ F3.2 | ✅ `ZQvzZ` | P0 |
| Approval card (all 4 states) | ✅ | ✅ pending F10.6 `GCuQ2`; approved F11.12 `c16G99`, denied F11.13 `s9qGv`, expired F11.14 `AKLDi` | P0 |
| Approval waiting in another session (sidebar dot) | ✅ `r5Gru` (session badge + toast); other agent: Edge States board | ✅ `B6G93s` (menu dot + toast) | P0 |
| Questions (quick reply / choice) | ✅ Agent-Initiated board | ✅ choice F11.7 `wiL50` | P0 |
| Attachments: upload, fail, too large, wrong type | ✅ Chat Interaction Details board, "Too large or wrong type" `jSKjM` | ✅ attach sheet F11.4 `BXfKu`; unsupported type F11.3 | P0 |
| 404 session | ✅ `H7ZqtC` | ✅ F11.19 `HfWCC` | P0 |
| ⌘K palette | ✅ `B5LZKO` | ➕ search screen | P1 |
| Share dialog + public shared view | ✅ dialog | ➕ public read-only page (desktop and mobile) | P1 |
| Agent detail | ✅ `x05s4W` | ➕ | P1 |
| Settings | 🔧 `Za8Qd`: move shortcuts out (Dark and System already hidden) | ➕ | P1 |
| Artifacts library / Archived | ✅ | ➕ | P1 |
| Forms | ✅ | ➕ | P1 |
| Add / Edit agent, Face ID, voice, doc edit, compare, onboarding, shortcuts overlay | ✅ (parked) | n/a | P2 |

**Mobile screens for v1: done.** The 13 missing items (new session, streaming with tool chips, plan card, error and reconnect, keyboard-open composer with attachments, agent switcher sheet, approval approved / denied / expired, question card, agent offline, 404, catalog loading, sessions loading, row menu) are designed as Flow 11, 19 screens in all (F11.1–F11.19). Variants got their own step so every screen has a trigger note. Delete on mobile supports both long-press and swipe.

The remaining P0 mobile states (catalog error and empty, auth expired, artifact streaming, approval waiting elsewhere, agent not found) are reference screens named `Mobile — …` at y 39,600. All P0 rows above are now ✅.

P1 adds the public shared session, search and agent detail.

**Edge states (P0), designed on the "Edge States (P0)" board `OFj2k`:**
- **Orphaned sessions.** An agent is removed from the registry but its sessions still exist. They stay readable, with the note "This agent is no longer available".
- **Mid-session version change.** The agent was redeployed during a session; show an inline "Agent updated to v15" divider.
- **Same session in two tabs.** The second tab becomes read-only until focused.
- **Approval decided elsewhere.** The approval was decided on another device; the card updates to the result.
- **Expiry while away.** The approval expired while the tab was in the background.
- **Artifact interrupted.** The stream dropped mid-artifact; the version is marked incomplete, with Retry.
- **Very long messages.** Long code blocks collapse after 30 lines, with "Show all".
- **Huge tables.** Show the first 50 rows, then "Show all N".

---

## 6. Success metrics

No third-party analytics. The client sends a small set of events to `POST /telemetry` → CloudWatch (Embedded Metric Format) → one dashboard. CI covers the rest.

| Goal | Metric | Target | How measured |
|---|---|---|---|
| It's the daily driver (north star) | Sessions you complete per week, across ≥ 3 agents | ≥ 15 / week by 4 weeks after v1 | `session_created` and `reply_done` events |
| Agents are data | Time from a deployed agent to appearing in the catalog; front-end changes needed | ≤ 30 min; **0** front-end commits | Per-agent checklist; PRs labelled `agent-onboarding` touch no `app/` code |
| Contract is complete | Scenario coverage of SSE event types | 100 % of event types, all states | Playwright scenario suite in CI |
| Responsive | Send → first rendered event (UI overhead only) | ≤ 150 ms after first SSE byte | `send_started`, `first_event`, `first_render` timestamps |
| Smooth streaming | Long tasks during a 2k-token reply; layout shift in chat | 0 tasks > 50 ms; CLS = 0 | Playwright + PerformanceObserver in CI |
| Nothing hangs | Sends that end in `done` or a handled error state | ≥ 99.5 % | `reply_done`, `reply_error`, `reply_abandoned` |
| Recovers | Streams that drop for < 30 s and resume without data loss | ≥ 99 % | Fault-injection scenarios, plus `stream_resumed` events |
| Trust | Sensitive tool calls executed without an approval record; executions after deny or expiry | **0** / **0** | Backend audit log query, alarmed |
| Accessible | axe serious / critical issues; P0 flows completable by keyboard | 0; 100 % | axe in Playwright; keyboard-only e2e |
| Portfolio | Shared-link views, median time on page; demos given | Tracked, no target in v1 | `share_viewed` events (no personal data) |
| Agent quality (P1) | 👍 rate per agent | Baseline, then trend | Feedback events, exportable as eval data |

---

## 7. Risks, assumptions

### Risks

| Risk | L | I | Mitigation |
|---|---|---|---|
| **Pause and resume for approvals on AgentCore.** A run must pause mid-tool-call, wait minutes for a human, then resume. AgentCore sessions end after idle timeouts (verify current limits), and a Strands run's state must survive that. | H | H | **Spike in M0** before any UI work on F10. The backend owns approval state in DynamoDB. On approval it resumes by re-invoking with the decision, using Strands interrupts or hooks plus AgentCore Memory. Approval expiry is kept shorter than the idle timeout. |
| **SSE through AWS infrastructure.** API Gateway REST APIs time out at 29 s, and some proxies buffer. | M | H | API service on ECS Fargate behind an ALB (idle timeout raised) or a Lambda Function URL with response streaming, chosen in the M0 spike. Heartbeat comments every 15 s. Resume with `Last-Event-ID`. |
| **Contract bakes in Strands concepts,** so LangGraph doesn't fit later. | M | H | Write the event taxonomy from the UI's needs, not from Strands events. Map both frameworks on paper in M0. Prove LangGraph in M5 (F26). |
| **Scope.** 74 designed screens is about a quarter's work for a small team; here it's one person plus AI agents. | H | H | P0 is about 40 % of the designed surface. The rest is parked on purpose (§3). Phase exit criteria are pass/fail. |
| **HTML artifacts run agent-written code** (XSS, data theft). | M | H | Sandboxed iframe served from a separate origin, no `allow-same-origin`, strict CSP, no network by default. Markdown is sanitised. |
| **Prompt injection triggers a harmful action.** | M | H | Approvals are enforced in the backend, not the UI. The card shows validated arguments. Tools only reach synthetic systems. |
| **Bank and health demos read as real** (compliance and reputation). | M | M | Synthetic data only, "Demo data" badges, agent disclaimers, no PHI or PCI data stored. |
| **Model and AWS cost from demos or loops.** | M | M | Per-session token and time caps in the backend, a budget alarm, and no public chat in v1. |
| **Design debt copied into code.** 99 raw hex colours and 26 font sizes, including half-pixel sizes. | H | M | Token cleanup in M0 (§9). The code uses only tokens and a 7-step type scale. |
| **Design and code drift.** Pencil can't run in the cloud sessions. | M | M | `design/INDEX.md` plus a PNG render of each P0 screen committed in M0; code review against those renders. |
| **Bus factor and time** (solo builder). | H | M | Small milestones, each shippable. The contract doc makes the backend and the agents independent tracks. |
| **Visible thinking isn't always available** (depends on the model or provider). | M | L | The `thinking` event is optional; the UI never waits for it. |

### Assumptions (confirm or correct)

| # | Assumption |
|---|---|
| A1 | Today you test agents with the CLI, the AgentCore console, curl and ad-hoc UIs. |
| A2 | v1 is owner-only for chat. Others see the work through read-only share links (P1) and your demos. |
| A3 | About 20 focused hours a week, you plus AI coding agents. v1 targets **Fri 18 Dec 2026**. |
| A4 | Monthly budget of about $50 AWS excluding model tokens, with a model-spend alarm at a limit you set. |
| A5 | AWS region `us-east-1`. Stack: CloudFront + S3 or Amplify for the Next.js front end; API on ECS Fargate or a Lambda Function URL; DynamoDB; S3; Cognito. |
| A6 | Backend in Python (FastAPI), the same language as the Strands agents, sharing types via a JSON Schema generated from the contract. |
| A7 | Bank and health agents use synthetic data only, now and for v1. |
| A8 | You approve everything; no other sign-off is needed. |
| A9 | The warm editorial visual direction in the design file is the direction. "Apple-quality" means craft and polish, not Apple's visual language. |
| A10 | The repo copy of `fleet_dev.pen` is the latest design, not the pen.dev share link. |

---

## 8. Roadmap

This assumes A3: about 20 hours a week, starting Tue 29 Sep 2026. Each milestone has pass/fail exit criteria and ends shippable.

| Milestone | Dates | Deliverables | Exit criteria |
|---|---|---|---|
| **M0: Decide and de-risk** | Sep 29 – Oct 9 | Answers to §11. `docs/BACKEND_CONTRACT.md` v0.1: endpoints, the agent descriptor, all SSE events, Strands and LangGraph mapping on paper. **Spike 1:** a Strands agent on AgentCore streams tokens through the API to `curl -N`. **Spike 2:** a tool call pauses for approval, the process idles 5 minutes, then resumes after approval. Design fix pass (§9). PNG renders of P0 screens committed. | Both spikes demoed. Contract reviewed. No open P0 design bugs. |
| **M1: Chat core on mock** | Oct 12 – Oct 30 | Next.js scaffold with tokens. App shell. Catalog. New session. Streaming chat. Activity rows. Sessions (rename, delete with undo). Switcher. Error states. `AgentApi` mock with the Scenario Agent scripts. CI running Playwright scenarios. | Flows F2, F6 (P0 subset) and F8 run end-to-end on the mock. Scenario suite green. axe clean. |
| **M2: Real backend, first real agent** | Nov 2 – Nov 13 | API service with Cognito auth. DynamoDB persistence. Registry CLI. HTTP/SSE `AgentApi`. **Research Analyst** live on AgentCore. Scenario Agent deployed. | You use the Research Analyst daily for a week. It meets the "nothing hangs" and first-render targets. |
| **M3: Artifacts, approvals, attachments** | Nov 16 – Dec 4 | F09–F12. The **Ledger** agent (synthetic bank) with approvals and questions. Document artifacts from Research Analyst with versions. | Flows F3 (P0 part), F4 (P0 part) and F5 (minus voice) pass on the real backend. Audit log shows 0 unapproved executions. |
| **M4: v1 hardening** | Dec 7 – Dec 18 | F15 mobile web. Performance and a11y pass. Pull in F16 ⌘K, F18 share links and F19 agent detail if there's room. Recorded demo videos. | All P0 ACs pass on desktop and at 390 px. **v1 launch Dec 18.** |
| **M5: Prove the platform** | Jan – Feb 2027 | Coding Agent and Health Assistant (P1 agents). LangGraph Travel Planner through the adapter (F26). Remaining P1 features by usage. | A new agent and a new framework both ship with 0 front-end commits. |

---

## 9. Critique of the existing designs

**What's strong (keep it):**
- The component system: 85 components, used consistently.
- An unusually complete states catalogue, covering failure, offline and not-found.
- Approval card structure.
- The artifact panel layout.
- The calm, editorial palette.
- Numbered flows with trigger notes.

This is a good base. The changes below are ordered by importance.

**Bugs to fix before build (design fix pass, M0):**
1. **The agent disclaimer is hard-coded to "Coding Agent… isolated sandbox"** on 21 screens belonging to other agents (F3.1–F3.3, F4.1–F4.5, F4.7, F5.1–F5.7, F6.5, F6.8, F8.4–F8.5, F9.8). **Fix:** make the disclaimer a Composer property fed from the descriptor (F02). **Done:** `Composer Disclaimer` component `QTWM6`, per-agent copy.
2. **Mobile composer replaced by a Checkbox** on `JLUHx` (Mobile — Chat with artifact), `j57Yaa` (F10.2) and `i46aRN` (F10.5). These screens have no composer. **Fix:** rebuild the mobile composer as a component variant. **Done:** `Composer / Mobile` component `OUcXN`.
3. **Delete copy contradicts itself.** The States board dialog says "This can't be undone", while F7.6 and F7.7 offer a 10-second undo. F7.6 also asks for confirmation *and* offers undo, which is double friction. **Fix:** no dialog; delete immediately with Undo. Keep typed confirmation for Delete all only. **Done:** F7.6 is now "Delete from row menu"; the Confirm Dialog is kept for Delete all only.
4. **Wrong composer placeholder:** the HTML preview screen (`j2uc1W`) says "Ask for changes to the brief…" for a budget dashboard. **Fix:** "Ask for changes to Budget dashboard…" **Done**, and the same fix on the Spreadsheet screen (`LrhPn`).
5. **New sessions don't appear in the sidebar** in several flow screens (a known issue). This also hides the core session-creation moment. **Fix:** add the new session at the top with a "new" state. **Done** on F2.3–F2.4, F5.1–F5.7, F6.7 and F8.3.

**Structural changes:**
6. **"Beta" is mixed up with health status.** Online / Degraded / Offline is *health* (computed); Beta is *maturity* (declared). A beta agent can be offline. **Fix:** a status dot plus a separate `Beta` tag. The filter chips become: All · Available · Unavailable, or just go away (next item). **Done:** new `Stage Tag` component; Travel Planner shows Online plus a Beta tag in every catalog, the mobile catalog and ⌘J.
7. **The catalog is over-built for 6 agents.** **Done:** filter chips, sort and search removed from the desktop and mobile catalogs (F1.8 in the parked Add-agent flow is unchanged); "Add agent" became a quiet "Register an agent" link; the "Catalog — sort menu open" screen was deleted.
8. **The sidebar nav is heavy.** Seven items sit above the session list (switcher, New, Search, All agents, Artifacts, Archived, plus settings), which pushes the list, the thing you actually come back for, down. **Fix:** keep the switcher, New session and Search; move All agents, Artifacts and Archived to the footer and ⌘K. **Done** in the `Sidebar` and `Sidebar Footer` components.
9. **Trash icon in the chat header.** A destructive action sits one click away in primary chrome, next to the session title. **Fix:** move it into the ⋯ menu. Also move the session id and message count (`ses_7f3a91 · 6 messages`) into the Session info drawer. **Done:** the Chat Header shows only ⋯, which opens Session info (id, message count and Delete session are there).
10. **Face ID step (F4.2) implies a real bank integration** ("Your approval is sent to your bank"). **Fix:** park it for P2. The v1 approval is an in-app decision with an audit record; its copy should say "Nothing is sent until you approve". **Done:** F4.2 is marked "(P2, parked)" and the Flow 4 notes skip it; "Approved by you with Face ID" became "Approved by you"; the card note already says "Nothing moves until you approve".
11. **Approvals need a presence outside their own session.** If you're in another session, a pending approval is invisible and quietly expires. **Fix:** a sidebar badge on the session plus a toast. Design it. **Done:** `r5Gru`, `B6G93s`, and the switcher badge on the Edge States board.
12. **Dark mode is offered but not designed.** **Fix:** remove the option from Settings for v1. **Done:** Dark and System are hidden; only Light remains.
13. **"Mock API" chip in the app header.** It's dev chrome in a portfolio product. **Fix:** show it only in dev builds. **Done:** the design shows the production build: the App Header chip and the footer's "Mock API · local" line are hidden, and Settings says data is stored in DynamoDB and S3. Dev builds add the chip back.

**System hygiene:**
14. **Contrast.** `text-tertiary` #8E897E is 3.3:1 on `bg` and 2.9:1 on `surface-muted`. It fails WCAG AA for the small text it's used for (timestamps, helper text, the disclaimer; 842 fills in the file). **Fix:** #6F6A62, which passes AA on every surface (4.5–5.1:1). `busy` (#C98A1B, 2.8:1) is fine as a dot but not as text; use #8A5A12 for amber text. **Done** for `text-tertiary`; amber text uses the new `warning` token (#8A5A12).
15. **Type scale sprawl.** There are 26 font sizes, including 12.5, 13.5, 14.5 and 15.5. **Fix:** 7 steps: 12 / 13 / 14 / 15 / 20 / 28 / 40. **Done:** 1,025 font sizes moved onto the 7 steps (half sizes rounded up); no new text clipping. Flow header cards and the index are canvas chrome and were left alone.
16. **Colour sprawl.** There are 99 raw hex fills next to 17 tokens. **Fix:** tokenise the agent palette (`agent-{hue}-bg/fg`), the amber warning set, hover states and chart colours. Callout variants become component variants, not per-instance overrides. **Done:** 65 new colour tokens (82 colour tokens in all): `agent-{red,blue,green,purple,amber,grey}-{bg,fg}`, amber / danger / accent / info sets, scrims, `hover`, `control-border`, `prose`, diff, `code-*` and `syntax-*`, `chart-1`–`6`. About 1,800 fills and strokes now use tokens. Agent colours are used only for agent identity; Callout, badges and favicons use `info` / `highlight`. Left raw on purpose: agent-authored content (the HTML budget app's Tailwind palette, artifact thumbnails, Settings theme previews), canvas chrome, transparent fills and a few alpha overlays. Callout variants are still overrides because Pencil has no variant system.
17. **Charts are hand-drawn with fixed coordinates.** **Fix:** specify them as a component spec (axes, series, tooltip) implemented with one chart library. Don't copy them from the file. **Done:** `docs/CHART_SPEC.md` (Recharts, one `<ChartBlock>` wrapper, the `chart` block schema, tokens, limits, accessibility). The drawn charts are labelled as illustrations.

---

## 10. Decisions

### A. Do we need to define the agents now?

**Yes, but as platform test cases, not a product roadmap.** The hub is only as good as the variety of what flows through it. Each agent is chosen to prove one part of the contract, so that when v1 ships every content type and interaction has at least one real producer. The plan still stands if agents change later; the set of *capabilities* being proved does not.

| Agent | Priority | Stack | Tools | What it proves |
|---|---|---|---|---|
| **Scenario Agent** (internal, hidden from catalog outside dev) | P0, M1 | Mock script player, plus a tiny Strands agent on AgentCore that replays the same scripts | `emit_scenario(name)` | Every SSE event and state renders correctly: offline, degraded, slow, dropped stream, expired approval. It powers e2e tests and fault injection. Replaces Home Ops for the offline state. |
| **Research Analyst** | P0, M2 | Strands, AgentCore Runtime | `web_search` (search API through AgentCore Gateway), `fetch_url`, `write_document` (artifact) | Streaming, tool timeline, plan and progress on a long task, citations, a document artifact with versions revised through chat. |
| **Ledger** (the Bank Agent, on a synthetic ledger) | P0, M3 | Strands, AgentCore; DynamoDB ledger | `get_balances`, `list_transactions`, `categorize`, `draft_transfer`, `execute_transfer` (**requires approval**) | Human in the loop end to end: pause and resume, expiry, deny with a reason, the audit log. Agent questions ("Which account?"), tables, charts (P1). |
| **Coding Agent** | P1, M5 | Strands, AgentCore Code Interpreter | `run_python`, `write_file`, `create_html_app` | Code and HTML artifacts, the sandboxed preview, file outputs (CSV / XLSX). Runs in a sandbox only; no git write access to real repos in v1. |
| **Health Assistant** | P1, M5 | Strands, a multimodal model | `extract_lab_values` (from PDF or image), `reference_ranges`, `interaction_check` (open dataset) | Attachments and image input, domain disclaimers from the descriptor, cautious-answer patterns. Synthetic records only. |
| **Travel Planner** | P1, M5 | **LangGraph**, through the HTTP adapter | Mock flight and hotel search, `itinerary` artifact, preference form | Framework independence (J1): a second framework with 0 front-end changes. Also structured forms (F21). |
| ~~Home Ops~~ | Cut | | | Needs hardware and proves nothing new. The Scenario Agent covers the offline state. |

The design shows Research Analyst as "LangGraph · Lambda". I recommend Strands on AgentCore for it, because your first real agent should be on your main stack. LangGraph is proved separately by Travel Planner.

### B. Is a clickable Figma prototype worth it?

**No.** There is no coded prototype yet, so the real choice is between spending that effort on a Figma prototype or on the real front end running on mock data. Build the real thing:
- **A chat product's quality is in time-based behaviour:** streaming speed, scroll anchoring, stop and retry, reconnection, approval countdowns. Figma can't simulate any of that, so a Figma prototype would validate what is already settled (layout) and miss what is actually at risk (behaviour).
- **Wiring 74 screens costs 3–5 days and creates a third source of truth** (Pencil, Figma, code) that goes stale by M2.
- **There are no stakeholders to convince.** You're the user and the approver.

**Do this instead:**
1. **Design fix pass in Pencil (M0, about 2 days).** Fix §9 items 1–13 and add the 13 missing P0 mobile screens.
2. **Build a scenario player** into the M1 front end: `?scenario=approval-expired` drives the real UI through the mock `AgentApi`. The 10 flows become 10 scripted scenarios you can click through, demo and test. That is your prototype, and it becomes the product and the test suite.
3. **Record 60–90 s videos** of scenarios for the portfolio before real agents exist.

**When I'd change my mind:** if you need to pitch a client before the end of M1, make a Figma prototype of **Flow 2 (start chatting) and Flow 4 (approval)** only, in 1 day or less, and throw it away afterwards.

---

## 11. Open questions (ranked by how much they block)

| Rank | Question | Blocks | My default if you don't answer |
|---|---|---|---|
| 1 | **Who uses v1 besides you, and how?** Owner-only with read-only share links, or strangers chatting live with your agents? | Auth model, backend cost controls, data model (visibility), security review, P0 vs P1 of sharing | Owner-only chat. Share links in P1. Guest chat in P2. |
| 2 | **Time and date:** how many hours a week, and is Dec 18 a real date or a wish? | Roadmap, what gets cut from M4 | About 20 h/week, Dec 18. |
| 3 | **Bank and health: synthetic data only, confirmed?** Any plan to connect real accounts, records or payment rails? | Agent design, compliance scope, whether step-up auth becomes P0 | Synthetic only, permanently for this project. |
| 4 | **Backend stack and hosting:** Python / FastAPI on ECS Fargate (or a Lambda Function URL), DynamoDB, S3, Cognito, `us-east-1`? | M0 spikes, the contract's type sharing | Yes, as stated (A5, A6). |
| 5 | **Budget ceiling:** monthly AWS spend and model spend? | Hosting choice (ALB baseline cost), token caps, whether public demos are ever possible | $50 AWS; model alarm at $50. |
| 6 | **First real agent:** is Research Analyst right, and do you have or want a search API (Tavily, Exa, Brave)? | M2 scope | Research Analyst, using a search API with a free tier. |
| 7 | **Data retention:** keep sessions forever? Hard-delete after the undo window, or soft-delete for 30 days? | Data model, delete semantics, export | Hard delete after 10 s undo. Attachments deleted with their session. |
| 8 | **Visual direction:** keep the warm editorial look, or did "Apple-style" mean a different visual language? | Token cleanup in M0 | Keep the current direction. |
| 9 | **Is the pen.dev share link newer than the repo copy?** | Critique accuracy, design fix pass | The repo copy is the latest. |
| 10 | **Name and domain:** is "Agent Hub" final? Custom domain for share links? | Share link URLs (P1), portfolio branding | "Agent Hub" on a subdomain of your portfolio domain. |
