# Delivery plan: from foundations to v1

| | |
|---|---|
| Status | **Approved 2026-09-29** (§7). Tracked in GitHub: milestones M1–M4, issues #2–#10 for M1, pinned #11 Weekly status, [board](https://github.com/users/IsraelBO17/projects/3) |
| Date | 2026-09-29 |
| Target | **v1 on Fri 18 Dec 2026** (PRODUCT_PLAN A3), about 20 focused hours a week |
| Replaces | The roadmap in `PRODUCT_PLAN.md` §8 (written before the stack decisions). `BUILD_PLAN.md` steps 8 and 9 are milestones M1–M4 here. |

This is the product manager's plan: what gets built in which order, how we know a milestone is done, and how progress, risk and spend are tracked each week.

---

## 1. Backend or frontend first? Neither: a thin slice through both

**Recommendation:** build one **walking skeleton** first: the thinnest path from the browser, through the API and AgentCore, back to the browser, deployed on `fleet.programmeos.com`. After that, build every feature as a **vertical slice**: contract change, API, UI and test together, shipped in one pull request.

**Why not backend first?** The API would be built blind to how the UI uses it, and nothing is demoable for weeks.

**Why not frontend first on mocks** (the old PRODUCT_PLAN M1)? It front-loads the work we already understand (layout, rendering) and postpones every risk that could force a redesign:

| Risk | Found out by | If it goes wrong |
|---|---|---|
| What a Strands agent on AgentCore actually streams | Recording real output (D10) | The translator and possibly block shapes change |
| SSE through the ALB with keep-alives | A real deploy (D5) | Streaming design changes |
| Pausing and resuming a run for approval | The P8 spike | Approvals fall back to holding the run open (D19) |
| Neon's pooler with async Postgres drivers | A real deploy (D3) | Driver settings |

The skeleton retires the first, second and fourth in about two weeks. The spike for the third opens M3, before any approval UI is built.

**Where mocks still help:** the OpenAPI contract is fixed, so the front end can run ahead on a mock client whenever the back end is blocked (for example, the approval card while the P8 spike runs). The mock client is also the Scenario Agent's player and the test harness (F14).

## 2. Which agent first? Research Analyst, starting small

**Recommendation:** the first real agent is a **Research Analyst v0**: a Strands agent on AgentCore with one model and one simple tool (`fetch_url`). No search API yet.

- It is a real v1 agent, so nothing is thrown away. v0 grows into the full Research Analyst in M2–M3 (search, plan, citations, document artifacts).
- One tool is enough to record everything the translator must handle first: text, thinking (if the model emits it) and tool calls.
- It has no outside dependencies: no search API key, no synthetic bank.

**The order after that:**

| Order | Agent | Built in | What it proves |
|---|---|---|---|
| 1 | Research Analyst v0 → full | M1 → M3 | Streaming, thinking, tools, plan, document artifacts with versions, PDF attachments |
| 2 | Scenario Agent (mock player in the web app) | M2 | Every event and failure state on demand; the Playwright suite in CI. The AgentCore replayer version comes later, if needed |
| 3 | Ledger (synthetic bank) | M3 | Approvals end to end (after the P8 spike), questions, tables |

Health Assistant, Coding Agent and Travel Planner (LangGraph) stay after v1 (PRODUCT_PLAN §10A).

**If an agent is already deployed on AgentCore** (Q9), it can stand in for Research Analyst v0 in M1: recording its output matters more than what it does.

---

## 3. Milestones

Each milestone ends with something you use on `fleet.programmeos.com`, and passes only if every exit criterion passes.

### M0: Decide and design (done 29 Sep)
Build steps 1–7 (Terraform written, not applied): decisions, diagrams, schema, contract, repo layout.

### M1: Walking skeleton, Wed 30 Sep – Fri 16 Oct (≈ 50 h)

| Slice | Contents |
|---|---|
| Infra up | Profile chosen; bootstrap applied; `fleet` NS records in GoDaddy; dev applied with `enable_api = true`; Neon project; Google OAuth client; secrets set |
| Agent | Research Analyst v0 deployed on AgentCore; **its raw stream recorded and committed** |
| API | FastAPI app with `/v1/health`, Google sign-in/refresh/logout/`me`, `GET /agents`, create session + send + stream (text, thinking, tool), list messages, stop; heartbeat and cancel flag; the registry CLI and `agents/research-analyst.yaml` |
| Web | Vite app with the design tokens; the typed client from `openapi.yaml`; sign-in, catalog, new session, streaming chat with thinking and tool chips, Stop |
| Delivery | API image to ECR, service at 1 task, Amplify branch and custom domain; a manual deploy script is fine |

**Exit:** you sign in and chat with Research Analyst on `fleet.programmeos.com` from laptop and phone; a 3-minute reply streams through the ALB without dropping; reload shows the full history; Stop works; `/v1/health` is green behind the ALB.

### M2: Chat core, Mon 19 Oct – Fri 6 Nov (≈ 60 h)

- Sessions: sidebar grouped by date, rename, delete with undo, agent switcher, 404s (F06, F07).
- Every reply end state: failed, stopped, interrupted, Retry, reconnect polling, "Still working", agent offline, auth expired with draft kept (F08).
- Plan block, Markdown, code blocks, "Jump to latest" (F04, F05).
- Activity polling (D22): the sidebar working dot and the "Task complete" toast. 👍/👎 feedback (D4).
- Mock client, Scenario Agent scripts, Playwright suite and deploys in GitHub Actions; logs and alarms (step 9).

**Exit:** Flows 2, 6 (v1 parts) and 8 pass on the real back end and on the mock; the scenario suite is green in CI; a push to `main` deploys.

### M3: Artifacts, attachments, approvals, Mon 9 Nov – Fri 4 Dec (≈ 80 h)

- **Week 1 gate: the P8 spike.** A Strands agent ends its turn on an approval request and resumes when re-invoked with the decision. If it fails: fall back to holding the run open (D19), decided that week.
- Artifacts (F09): Research Analyst writes documents, with versions; panel on desktop, sheet on mobile.
- Attachments (F12): upload, limits, and the agent reads a PDF.
- Approvals and questions (F10, F11): the Ledger agent, the approval card in every state, the sidebar badge and toast, the audit record.

**Exit:** Flows 3, 4 and 5 (v1 parts, no voice) pass on the real back end; the audit query shows 0 executions without an approval.

### M4: Hardening and launch, Mon 7 Dec – Fri 18 Dec (≈ 40 h)

- Mobile web for the core flows (F15); accessibility (axe clean, keyboard-only P0 flows); the "nothing hangs" and first-render targets (PRODUCT_PLAN §6).
- Cost review against the budget; recorded demo videos; docs brought up to date.

**Exit:** every P0 acceptance criterion passes on desktop and at 390 px. **v1 launches 18 Dec.**

### After v1
P1 features by usage (⌘K, share links, agent detail, artifacts library, forms, rich content), then the next agents (PRODUCT_PLAN §4, §10A).

### If it runs late: cut in this order
The schedule has no slack (≈ 230 h in ≈ 11.5 weeks). If a milestone slips by more than 3 working days, cut from the top of this list before moving the date:

1. "Task complete" toast (back to P1)
2. Questions (F11) (back to P1; approvals stay)
3. Mobile polish beyond the core flows
4. Artifact types beyond document and code (html and table to P1)

---

## 4. How work is tracked

**One place: GitHub, next to the code.**

- **Milestones** M1–M4 with their due dates. The milestone page shows the burn-up for free.
- **One issue per slice**, written as: what the user can do; the acceptance criteria it closes (PRODUCT_PLAN F-numbers); the Definition of Done checklist below.
- **Labels:** `area:api`, `area:web`, `area:infra`, `area:agent`; `P0` / `P1`; `risk` for spikes; `agent-onboarding` for PRs that only add an agent (they must not touch `web/` or `api/`, PRODUCT_PLAN §6).
- **A Project board**, [Agent Hub v1](https://github.com/users/IsraelBO17/projects/3), linked to the repo, with Todo / In Progress / Done. At most 2 items in progress. New issues are added to it when they are written.
- **Issue template** `.github/ISSUE_TEMPLATE/slice.md` for new slices. M2–M4 issues are written at the start of each milestone, so the board holds only work that is next.
- **Branches and PRs** per slice, merged to `main` when the Definition of Done holds.

**Definition of Done (every slice):**
- [ ] Contract changes first: `openapi.yaml` updated and linted, if the slice changes the API
- [ ] API and UI built, with tests (API unit/integration; web component or Playwright where it renders a flow)
- [ ] Works on `fleet.programmeos.com`, not only locally
- [ ] Docs changed where a decision or flow changed (ARCHITECTURE change log)
- [ ] The issue's acceptance criteria checked off

## 5. How progress is monitored

**Every Friday, a 10-minute review, posted as one comment on a pinned "Weekly status" issue:**

```
Week of <date> · Milestone M<n> · <on track | at risk | late>
Done:      <slices closed, with links>
Next:      <slices planned for next week>
Risks:     <new or changed; decision needed?>
Numbers:   P0 criteria passed <x>/<y> · hours this week <h> · AWS month-to-date $<n> (forecast $<m>)
```

| What | Target | Where it comes from |
|---|---|---|
| Milestone burn-up | On the line to the due date | GitHub milestone (closed vs. open issues) |
| P0 acceptance criteria passed | All 15 features (F01–F15) by 18 Dec | Checklist in each feature's issue |
| Hours spent vs. plan | ≈ 20 per week | Your own log; one number in the weekly comment |
| AWS spend | ≤ $50/month | Budget alarm (email) and Cost Explorer |
| Slip | ≤ 3 working days per milestone | Milestone due date; past that, apply the cut list |
| Spikes and gates | Decided within their week | The `risk` issues |

Product metrics (sessions per week, first-render time, "nothing hangs", approvals) start collecting at M2 and are reviewed from v1 onward (PRODUCT_PLAN §6).

## 6. Risks to watch

| Risk | Likelihood / impact | Mitigation | Checked |
|---|---|---|---|
| AgentCore's real stream doesn't fit the block model | M / H | Record in M1 before writing the translator | M1 |
| Approval pause/resume doesn't work (P8) | M / H | Spike opens M3; fallback in D19 | M3 week 1 |
| SSE drops through the ALB or on deploys | L / H | 300 s idle timeout, 15 s pings, 300 s drain; a 3-minute stream is an M1 exit test | M1 |
| Schedule: 230 h of work, no slack | H / M | Vertical slices, cut list, weekly status | Every Friday |
| Model spend from long or orphaned runs | M / M | 15-minute run cap, 3 concurrent runs, a model-spend alarm (to set) | M2 |
| Solo builder: illness, other work | M / M | Each milestone ships something usable; the plan survives a week's loss by cutting | Every Friday |

## 7. Decisions (owner, 2026-09-29)

1. **Approach:** walking skeleton, then vertical slices.
2. **First agent:** Research Analyst v0 (answers ARCHITECTURE Q9).
3. **Timeline:** v1 on 18 Dec at ~20 h/week, with the cut list (answers PRODUCT_PLAN §11 rank 2).
4. **Tracking:** GitHub milestones, issues and a Project board.

## 8. M1 issues

| # | Slice |
|---|---|
| [#2](https://github.com/IsraelBO17/agent_hub/issues/2) | Infra: bring up bootstrap and the dev environment |
| [#3](https://github.com/IsraelBO17/agent_hub/issues/3) | Agent: Research Analyst v0 on AgentCore, raw stream recorded |
| [#4](https://github.com/IsraelBO17/agent_hub/issues/4) | Web: app shell, tokens, typed client, Amplify |
| [#5](https://github.com/IsraelBO17/agent_hub/issues/5) | API: FastAPI shell, health, Docker, behind the ALB |
| [#6](https://github.com/IsraelBO17/agent_hub/issues/6) | Auth: Google sign-in and the API session |
| [#7](https://github.com/IsraelBO17/agent_hub/issues/7) | Agents: registry CLI, `GET /v1/agents`, catalog |
| [#8](https://github.com/IsraelBO17/agent_hub/issues/8) | Chat: new session, send and stream, reload |
| [#9](https://github.com/IsraelBO17/agent_hub/issues/9) | Chat: Stop generation |
| [#10](https://github.com/IsraelBO17/agent_hub/issues/10) | Verify: 3-minute stream through the ALB and deploy draining |

Rough order: #2 and #3 first (they unblock everything), #4 and #5 in parallel, then #6 → #7 → #8 → #9, and #10 last.
