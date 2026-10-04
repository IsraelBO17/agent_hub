# Problem brief

| | |
|---|---|
| Status | **Approved 2026-10-04** (owner), with the decisions in §5 |
| Date | 2026-10-03, after M1 closed |
| Evidence | The owner's answers on real use since M1 (below), the repo (`agents/` holds one descriptor), issue #31, the gallery `design/renders/index.html` |
| Changes | PRODUCT_PLAN §1–2 (users, problem, jobs) and ARCHITECTURE D31, which supersedes D9's single active user |

**Principle (owner, 2026-10-03).** The hub is the front end for conversational agents. It isn't the custom app for any one agent. An agent with its own workflow (an admin dashboard, a document pipeline) gets its own front end, and the hub shows the conversations.

## 1. What changed since the plan

PRODUCT_PLAN §1 was written for one person: a builder who wants a front end for their own agents, with a portfolio audience watching. Real use since M1 says something different:

- **10–20 Qucoon colleagues have asked to use it**, engineers and non-technical staff. Some want Research Analyst as an everyday tool; others are building agents and want the hub as their front end. Each needs their own sign-in and private history. Qucoon knows, and the Bedrock cost is acceptable.
- **The owner's use is light so far:** a few sessions, all with Research Analyst, the only deployed agent. Without the hub the owner would have used Claude.ai. What would make the hub win: the harness around each agent, and every agent's work in one history.
- **The only annoyance is streaming:** a long wait after sending with too little feedback, then text in uneven bursts. The model's first words take 3.5–5.8 s; the hub renders each event 10–21 ms after it arrives, so the bursts come from upstream.
- **Never used except to test:** switching agents (there's one), Stop, reopening an old session.
- **Agents by 18 Dec:** Research Analyst, then an HR agent and a business documents agent for Qucoon. Nobody needs Ledger for real work, but real agents will need approvals.
- **The portfolio is real but has no audience or date.** It's both the owner's portfolio and an internal Qucoon tool.

## 2. Users

| User | Who | What they need from the hub | In the plan today |
|---|---|---|---|
| **Staff** | Qucoon colleagues, many non-technical, often on a phone | Ask Qucoon's agents for real work; their own private history | Not covered: teammates are P2, sign-in is one allowlisted user (D9) |
| **Agent builders** | The owner and colleagues building agents | Put an agent in front of its users with no UI work; see exactly what each reply did | Partly: J1 covers the owner only; there's no per-reply detail beyond tool chips |
| **Portfolio viewers** | Anyone the owner shows it to | Watch a polished demo; open a read-only link | P1 share links; no date |
| *Agent admins* | e.g. the HR admin | Work in **the agent's own app**, not the hub (principle above) | Out of scope, but their replies must reach staff in the hub (problem 5) |

## 3. The problems, ranked

| # | Problem | Who has it | Evidence | Frequency |
|---|---|---|---|---|
| 1 | **Colleagues can't use Qucoon's agents.** There's no shared, signed-in place where staff reach the agents, with their own private history | Staff (10–20), builders | 10–20 people asked; the HR and documents agents are for them | Every day, once they're let in |
| 2 | **Waiting for a reply feels slow and uneven** | Everyone, on every message | Owner's only annoyance; first words 3.5–5.8 s, then bursts | Every message |
| 3 | **Builders can't see what a reply actually did** | Builders | Owner and colleague builders asked for raw events, tokens and cost, timing, model, request ID, full tool calls | Every test of a new agent or a new version |
| 4 | **A builder can't ship an agent to the right people without the owner** | Builders | Colleagues are building agents for the hub; today only the owner can register one, and every agent is visible to everyone | Each new agent or version |
| 5 | **Work that happens outside the live reply doesn't reach the person** | Staff, builders | HR admin replies in the HR app and must appear in the staff member's conversation; the documents agent files into SharePoint, Drive or Git (needs approval); triggered agents are expected | Per agent; grows with every agent that isn't a pure chat |

Demoted, with reasons:
- **Coming back to past work (J6)** is table stakes for everyday users, who expect history as in Claude.ai, so the M2 sessions sidebar stays. But no one has asked for search, archive or the artifacts library yet, and they stay P1.
- **Approvals as a Ledger demo (J5).** The need is real, but it should be met with a real agent. Ledger proves a capability nobody uses.
- **Showing work (J7).** Real, but there's no audience or date. Share links stay P1, and the polish they need comes from the work for problem 1.

## 4. Each problem: how the hub solves it today, and what's missing

### 1. Colleagues can't use Qucoon's agents
- **Built:** Google sign-in with an allowlist (`MMxdZ`); "This Google account doesn't have access" (`zte2v`, `dLCVX`); the catalog (`PBQLh`, mobile `ulBUE`); chat on desktop and phone.
- **Designed:** Settings → Account (`RHrDH`). Nothing for a second user.
- **Missing:**
  - **Inviting people.** The schema is ready (D9: `user_id` everywhere, `users.status = invited`), so this can be a CLI first, with no screen.
  - **Who can see which agent.** The HR agent is for all staff, but a colleague's draft agent is only for its builder. D9's "Revisit if" already names an `agent_access` table.
  - **Copy for non-technical staff.** The catalog's footnote ("Agents are loaded from GET /v1/agents…"), "Register an agent", and "Strands · AgentCore" on every card are builder language shown to everyone (`PBQLh`, built catalog).
  - **Privacy that's stated.** Staff will ask the HR agent personal questions. The hub must say plainly what is private and what the HR team sees.

### 2. Waiting for a reply feels slow and uneven
- **Built:** Typing Indicator, then "Thinking…" and "Thought for Ns" (`qky6s`, `KfCS1`; `issue-8/desktop-3-streaming.png`), and tool chips. The web batches events per frame and flushes every 250 ms (SEND_MESSAGE.md).
- **Designed:** F2.5 "Waiting for the agent" (`qky6s`), Message Footer / Still working at 60 s (`K5UJmM`).
- **Missing:**
  - **The first 3.5–5.8 s say nothing useful.** The design has a few dots and no sense of progress or of what the agent is doing.
  - **There's no rule for how text appears.** Text shows exactly as it arrives. A steady reveal rate (smoothing bursts on the client) isn't designed or specified.
  - **Where the bursts start hasn't been measured.** It could be the model, Strands, AgentCore or the ALB. It's worth one check by the API session before designing around it.

### 3. Builders can't see what a reply actually did
- **Built:** Tool Call Detail with input and output (`pkhri`; `issue-8/desktop-2-reply.png`) and the Thinking row.
- **Designed:** the tool activity timeline (Agent Working board `sx5f0`, section 2), and Session info (`E3lQz`: session ID, message count).
- **Missing:**
  - **A per-reply details view:** model, agent version, timings (time to first event, first words, total), tokens and cost, request ID, every tool call in full, and the raw event list.
  - **Shown to builders only.** Staff shouldn't see it by default.

### 4. A builder can't ship an agent to the right people without the owner
- **Built:** agents are data. The registry CLI and `agents/*.yaml` mean a new agent needs no front-end change, and the Stage Tag shows Beta.
- **Designed:** the Add / Edit agent UI (F1.3–F1.7, F9.6), parked as P2; agent detail (`x05s4W`, P1).
- **Missing:**
  - **How a colleague registers or updates their agent.** A PR to `agents/` reviewed by the owner may be enough.
  - **Draft agents visible only to their builder, then released to a group.** This is the same `agent_access` as problem 1.

### 5. Work outside the live reply doesn't reach the person
- **Built:** nothing yet.
- **Designed:**
  - Approval card states (`m1FtM` and its variants, F4, F11.12–14).
  - Approval waiting elsewhere (`r5Gru`, `B6G93s`).
  - Task complete toast (F4.6 `pwVxh`), from activity polling (D22, M2).
- **Missing:**
  - **A message that arrives later from a person or another system,** such as the HR admin's reply, in a session the user isn't watching. Every design assumes the agent's own run continues the reply. This needs an unread state on the session and a notification, and it touches D30's precaution ("don't assume a person started every session").
  - **Approvals with a real agent:** for example, the documents agent asking before it files into SharePoint.
  - **An Inbox (F30)** for triggered runs. D30 keeps this after v1, and that still holds unless a triggered agent arrives before 18 Dec.

## 5. Decisions (owner, 2026-10-04: yes to all five, as recommended; ARCHITECTURE D31)

1. **Colleagues use v1.** Invites by CLI, no admin screens. Reverses PRODUCT_PLAN §1 (teammates P2), A2 and §11 rank 1, and D9's single active user. The cost is invites, agent access, copy, privacy and per-user limits; HTML and table artifacts (cut list item 4) and replacing Ledger make room.
2. **Agent access** (`agent_access`): an agent is visible to everyone or to named people; a new agent is visible only to its builders until released.
3. **Ledger is replaced in M3** by a real agent's approval: the documents agent asking before it files. The P8 spike is unchanged.
4. **Messages from outside the run** (the HR admin's reply) are designed in M3, and built in v1 only if the HR agent ships by 18 Dec.
5. **A builder's details view of each reply** is built in M2, shown to that agent's builders.

## 6. Beyond chat (D30)

The principle sharpens D30 rather than changing it. Agents with their own workflow get their own app, and the hub stays the place for conversations and the runs people start or receive. What moves closer to v1 is the smallest piece of D30: **a session can receive a message the user didn't trigger** (the HR reply now, triggered runs later). Task agents with a form (the documents agent, maybe) and a full Inbox stay after v1 unless one of those agents is due before 18 Dec.
