# Design review: the screens against the problems

| | |
|---|---|
| Status | **Approved 2026-10-04** and applied in three batches (step 4): `33a9484` (1–5), `6ab80a3` (6, 7, 10–12), batch 3 (8, 9) |
| Date | 2026-10-04 |
| Inputs | [`PROBLEM_BRIEF.md`](PROBLEM_BRIEF.md) (approved), ARCHITECTURE D31, the gallery [`design/renders/index.html`](../design/renders/index.html), build screenshots in [`screenshots/`](screenshots/) (issue-8 and `m1-mock/`, main `251a14a`) |

## 1. Each problem through the screens

### Problem 1: colleagues can't use Qucoon's agents
| Step | Built | Designed | Verdict |
|---|---|---|---|
| Sign in | `MMxdZ`, not allowed `zte2v` | Same | **Works.** "Access is by invitation" already fits invites by CLI |
| First look at the catalog | Cards with `Strands · AgentCore`, "Register an agent", and the footnote "Agents are loaded from GET /v1/agents…" | Same, plus "Continue where you left off" | **Weak.** Builder language on a staff member's first screen (13 screens carry the footnote) |
| Open an agent, first session | New session with starters; sidebar "Your sessions will appear here" | Sidebar always full of sessions; no first-visit state | **Missing:** the empty sidebar for a new user |
| The sidebar header | Agent Switcher "Online · Strands" | Same, on 41 screens | **Weak:** the framework name means nothing to staff |
| Privacy | Nothing | Nothing | **Missing:** what's private, and what the HR team sees |

### Problem 2: waiting for a reply feels slow and uneven
| Step | Built | Designed | Verdict |
|---|---|---|---|
| 0–4 s after Send | "Thinking…" row at once (`issue-8/desktop-3-streaming.png`) | Three dots (F2.5 `qky6s`, Agent Working `sx5f0` §1) | **The build is better:** it says what's happening. Neither shows elapsed time |
| First words | Text as it arrives, in bursts | No rule | **Missing:** a steady reveal rule |
| 60 s with no events | "Still working" footer | `K5UJmM` | Works |

### Problem 3: builders can't see what a reply did
| Step | Built | Designed | Verdict |
|---|---|---|---|
| Tool calls | Chip expands to input and output | Same, plus the timeline (`sx5f0` §2) | Works for tools only |
| Everything else about a reply | Nothing | "View raw JSON" in a P2 More menu (`Q6kwA2` §5, which renders empty); session tokens in Session info (`E3lQz`) | **Missing:** model, version, timings, tokens and cost, request ID and raw events, per reply, for builders |

### Problem 4: a builder can't ship an agent to the right people
| Step | Built | Designed | Verdict |
|---|---|---|---|
| Register | CLI only | F1.3–F1.7 Add agent UI (P2) | CLI or a PR is enough; **the Add agent UI solves a problem nobody has** at this size |
| Who sees it | Everyone | Everyone | **Missing:** a "Draft · builders only" marker on the card and in the switcher |

### Problem 5: work outside the live reply doesn't reach the person
| Step | Built | Designed | Verdict |
|---|---|---|---|
| Approval | — (M3) | Full set of states, all with Ledger moving synthetic money | **Content is a demo:** re-cast with the documents agent filing a file |
| Reply from a person, later (HR) | — | Nothing; every design assumes the agent's own run continues | **Missing:** the message, an unread marker, a toast |
| Task done while away | — (M2) | Task complete toast (F4.6) | Works |

**Designed but solving no current problem** (keep parked, spend nothing on them): the Add agent flow F1, onboarding `RPCu8`, Face ID `RPA2L`, voice F5.6–5.7, version compare, ⌘K, ⌘J, share and export, the artifacts library, the shortcuts overlay. The fictional roster (Health Assistant, Coding Agent, Ledger, Travel Planner, Home Ops) also no longer matches the agents that will exist (Research Analyst, an HR agent, a documents agent).

## 2. Built vs designed

| Where | Difference | Better | Action |
|---|---|---|---|
| Waiting (F2.5) | Build shows "Thinking…" at once; design shows dots | **Build** | Into the design (change 2) |
| Catalog empty / error | Build: "Agents come from the registry", "The server had a problem. Try again in a moment." Design: `GET /agents`, "returned 503" | **Build** | Into the design (change 3) |
| Session expired | Build adds Cancel | Build | Into the design (small) |
| Error references | Build shows `Reference: req_agent_error` (an error code); design shows `500 · req_8f2a` | Neither, for staff | Change 3: plain message for staff; request ID in the builder's details |
| Agent offline | Design: notice banner with "Switch agent", the draft kept; build: only the composer placeholder | **Design** | Follow-up for web (W2) |
| Session not found | Design offers "New session" and "Back to agents"; build only "New session" | Design | Follow-up (W3) |
| Agent icons | Blank tiles in the built catalog and new-session hero | Design | Follow-up (W1): likely a regression |
| Agent switcher | Design has a search row; build doesn't | Build, at ≤ 8 agents | Keep the design's rule: search only above 8 |
| Catalog "Continue where you left off" | Not built | Design | Arrives with the sessions list in M2 |
| Mobile catalog | Both are a list | Same | — (the gallery note saying "built as a list, not cards" was wrong; fixed) |

**Follow-ups for the web sessions** (not changed here):
- **W1.** Agent icons render as blank tiles in the catalog and on the new-session hero (mock mode, main `251a14a`). Check the icon lookup.
- **W2.** Agent offline: add the notice banner with "Switch agent" (`sx5f0` §6, F6.8 `j5dD9g`). In the `agent-offline` mock scenario the sidebar switcher still says "Online" while the header says "Offline".
- **W3.** Session not found: add "Back to agents" (`H7ZqtC`, F11.19 `HfWCC`).
- **W4.** While the session is restored, a sidebar-shaped skeleton shows on the catalog, which has no sidebar.
- **W5.** Error references show a code (`req_agent_error`), not the request ID. After change 3, the request ID belongs in the builder's details.

## 3. M2 and M3 readiness

**M2 (DELIVERY_PLAN §3, plus D31):**
- **Designed and clear:**
  - **Sessions:** the sidebar grouped by date, inline rename (States board), the row menu and delete with undo (F7.3, F7.6, F7.7, F11.16–18), the sidebar loading and failed states (`P3wQ4`).
  - **Every reply end state:** Stopped, Interrupted, Failed, Still working, Still replying, reconnecting and back online (`sx5f0` §6–8, F6.1–6.4).
  - **Content:** the plan card, code blocks, Jump to latest, 👍 / 👎 with reasons (`Q6kwA2` §5), and the Task complete toast (F4.6).
- **Missing:**
  - The builder's details view.
  - The waiting state and the reveal rule.
  - Staff copy.
  - The first-visit sidebar.
  - The draft-agent marker.
  - Hover, pressed and disabled states beyond the composer and message actions.
  - 44 px touch targets.
- **Unclear:**
  - **Markdown typography.** Code and tables are drawn (`IVLvU` §4 and §10); headings, lists, quotes and links in a reply aren't shown together anywhere. The build can follow the document artifact's styles, so this is a Should.

**M3:**
- **Designed:** artifacts (document, code, html, table; panel, sheet, versions, streaming, failed version), attachments (every chip state, drag and drop, the attach sheet), questions, and the approval card in every state.
- **Missing:**
  - **Approvals with the real agent.** The documents agent's filing request and its result, with a link to the filed document.
  - **The outside reply.** A message from a person, an unread session and a notification.

## 4. Open gaps and consistency

- **UI_COMPONENTS §5 item 2, hover, pressed and disabled:** drawn only for the composer (`Q6kwA2` §1) and message actions (§5). Not drawn for buttons, Icon Button, Session Item, Starter Prompt, Agent Card, Menu Item, chips or Suggestion Pill.
- **Item 6, touch targets:**
  - **Undersized on mobile:** 40 px icon buttons, 32 px buttons, 28 px chips and the 30 px Jump to Latest.
  - **Hard to audit:** the mobile screens are mostly hand-drawn frames (46 component instances across 44 screens).
  - **Fix:** a rule plus one board, not redrawing.
- **Type scale:** all text on 12/13/14/15/20/28/40. ✓
- **Icons:** all 212 lucide. ✓
- **Colours:** raw hex only where intended (Settings theme previews, the agent-made HTML app, a few alpha overlays). ✓
- **Fonts:** 32 texts use a literal "Inter" instead of `$font-ui`; 48 use "Source Serif 4" (documents) with no token.
- **Board defects:**
  - The "More menu (P2)" example in `Q6kwA2` §5 renders empty.
  - `Q6kwA2` exports 2391 wide (a child overflows the 2280 board).
  - About 20 flow screens are detached copies of reference screens and will drift.
- **Accessibility:** contrast was fixed in M0; focus is drawn (`Crc4x`). The new states (unread, draft, details) need a text equivalent, not colour alone.

## 5. Design changes, ranked (approved 2026-10-04; all applied)

| # | Change | Tag | Screens and components | Why |
|---|---|---|---|---|
| 1 | **Reply details for builders.** A "Details" action on each reply (builders only) opens a side panel (a sheet on mobile): model, agent version, request ID (copy), timings (sent → first event → first words → done), tokens in / out and cost, every tool call in full, and the raw event list (copy as JSON). Also fix the empty More menu | Must (M2) | `Message Actions` `SnIqS`, new `Reply Details` component, a new desktop and mobile reference screen, `Q6kwA2` §5 | Problem 3 |
| 2 | **Waiting and streaming.** Replace the dots with the build's "Thinking…" row, plus elapsed seconds ("Waiting for Research Analyst · 4 s"); write the steady-reveal rule on the board | Must (M2) | `Typing Indicator` `eFeRx`, F2.5 `qky6s`, `sx5f0` §1 and §5, F11.5 `DNypg` | Problem 2 |
| 3 | **Staff copy, builder extras.** For staff: no runtime line, no `GET /agents` footnote, no "Register an agent", the switcher says "Online" (not "Online · Strands"), errors say what to do without codes. Builders keep the runtime line and the registration link | Must (M2) | `Agent Card` `VZuIf`, `Agent Switcher` `RZF5q` (41 screens), catalog and its empty and error states (desktop and mobile), `Inline Error` | Problem 1 |
| 4 | **A colleague's first visit.** The empty sidebar for an agent ("No sessions with Research Analyst yet"), the catalog without "Continue" | Must (M2) | `Sidebar` session list, a new state on the States board | Problem 1 |
| 5 | **An agent's audience.** A "Draft · builders only" tag on the card, in the switcher and in the chat header; staff never see drafts | Must (M2) | `Stage Tag` `nC6tf` (new variant), `Agent Card`, `Agent Menu Item` | Problem 4 (D31) |
| 6 | **Hover, pressed and disabled for every control** on one "States · Interaction" board | Must (M2) | Button ×3, Icon Button, Session Item (plus selected, working), Starter Prompt, Agent Card, Menu Item, chips, Suggestion Pill | UI_COMPONENTS §5 item 2; M2 builds these rows and actions |
| 7 | **Touch targets.** Rule: on touch every control's hit area is at least 44 × 44 without changing its drawn size; one "States · Touch" board marks the hit areas on the mobile top bar, composer, session row, message actions and chips | Must (M2) | New board; UI_COMPONENTS §5 item 6 | F15; M2 builds the mobile drawer, long-press and swipe |
| 8 | **Approvals with the real agent.** Re-cast the approval examples from Ledger's transfer to the documents agent filing a file ("File *Q3 supplier contract.pdf* to SharePoint › Legal › Contracts"), with a result that links to the filed document | Must (M3) | `Approval Card` and its variants' content, F4.1, F4.3, F4.4, F10.6, F11.12–14, `r5Gru`, `B6G93s`, `zaZHd` §4 | Problem 5, D31 |
| 9 | **A reply from outside the run.** A new message from a person or system ("HR team"), clearly not the agent; an unread marker on the session; a toast; mobile too. A new Flow 12 of about 4 steps, with the privacy note that tells staff what HR sees | Must (M3) | New `Outside Message` component, `Session Item` unread state, `Toast`, Flow 12 desktop and mobile | Problem 5, D31 |
| 10 | **A realistic roster.** Example agents become Research Analyst, HR Assistant, Documents and one draft, in the screens changes 3–5 touch | Should | Catalog, switcher and sidebar examples | Designs that match the real product |
| 11 | **Markdown in a reply.** One reference showing headings, lists, a quote, links and inline code together | Should | `IVLvU` | M2 builds Markdown |
| 12 | **Hygiene.** Literal "Inter" → `$font-ui`; a `font-serif` token for documents; fix the `Q6kwA2` overflow | Should | 80 texts, one board | Consistency |
| 13 | Inbox (F30), task forms (F28), the Add agent UI, share and export, ⌘K | Later | — | No current problem (D30) |
