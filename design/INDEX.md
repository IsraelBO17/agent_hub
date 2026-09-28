# Design index

Generated from `fleet_dev.pen` by `design/tools/pen_index.py`. Do not edit by hand.

- Top-level frames: 222
- Reusable components: 85 (2475 references, nested ones included)
- Reference screens and boards: 34
- Flow screens: 74

Node IDs are stable Pencil IDs; use them to find a node in the file (`"id": "<ID>"`).

## Variables

| Token | Type | Value |
|---|---|---|
| `bg` | color | `#FBFAF7` |
| `surface` | color | `#FFFFFF` |
| `sidebar` | color | `#F3F1EC` |
| `surface-muted` | color | `#EEEBE4` |
| `border` | color | `#E3DFD6` |
| `text-primary` | color | `#1B1A17` |
| `text-secondary` | color | `#5E5A52` |
| `text-tertiary` | color | `#8E897E` |
| `accent` | color | `#1F5C4A` |
| `accent-soft` | color | `#E2EEE8` |
| `on-accent` | color | `#FFFFFF` |
| `online` | color | `#2F9E6B` |
| `busy` | color | `#C98A1B` |
| `offline` | color | `#A8A398` |
| `danger` | color | `#B3372B` |
| `danger-soft` | color | `#F7E4E1` |
| `code` | color | `#1E1D1A` |
| `font-ui` | string | `Inter` |
| `font-mono` | string | `JetBrains Mono` |

## Components

### 1 Foundations & Actions

| Component | ID | Size | Slots | Refs |
|---|---|---|---|---|
| Button / Primary | `H0OSN` | auto×auto |  | 36 |
| Button / Secondary | `XBZK2` | auto×auto |  | 72 |
| Button / Danger | `HsXdL` | auto×auto |  | 5 |
| Icon Button | `btfe4` | 32×32 |  | 91 |
| Kbd | `rjWo1` | auto×20 |  | 124 |
| Tooltip | `fkIAs` | auto×auto |  | 3 |
| Checkbox | `llhcq` | 16×16 |  | 21 |
| Status Badge | `JQ0rx` | auto×auto |  | 17 |
| Agent Avatar | `vCJQN` | 26×26 |  | 60 |
| Inline Code | `Uzd9M` | auto×auto |  | 2 |
| Citation Chip | `q3C9LM` | auto×18 |  | 4 |
| Resize Handle | `accqR` | 1×400 |  | 9 |

### 2 Inputs & Selection

| Component | ID | Size | Slots | Refs |
|---|---|---|---|---|
| Search Field | `Wjnvx` | 240×auto |  | 19 |
| Select Button | `ZWD7y` | auto×auto |  | 20 |
| Segmented Item | `K1CWuA` | auto×auto |  | 14 |
| Filter Chip | `W0HHV` | auto×auto |  | 37 |
| Reason Chip | `c3s8Su` | auto×auto |  | 33 |
| Suggestion Pill | `wULfL` | auto×auto |  | 12 |
| Form Field | `s2kV7R` | 300×auto |  | 28 |
| Toggle Row | `sQir5` | 300×auto |  | 20 |
| Choice Option | `CxmKK` | 420×auto |  | 25 |
| Stepper | `sV1X6` | 516×auto |  | 9 |

### 3 Menus & Overlays

| Component | ID | Size | Slots | Refs |
|---|---|---|---|---|
| Menu Item | `koWWb` | 180×auto |  | 67 |
| Menu Panel | `QRlRa` | 220×auto | `Items` (p97XhG): Menu Item | 17 |
| Agent Menu Item | `UauTJ` | 288×auto |  | 12 |
| Palette Row | `QrHIB` | 600×auto |  | 33 |
| Command Palette | `ZHC9i` | 640×auto | `Results` (NF5Vl): Palette Row | 5 |
| Dialog | `dQMxZ` | 480×auto | `Body` (sYTH9) | 21 |
| Confirm Dialog | `i3B1e` | 400×auto |  | 3 |
| Toast | `IjtkQ` | 380×auto |  | 12 |
| Feedback Popover | `meKbs` | 380×auto |  | 1 |
| Source Preview | `Ypu1g` | 340×auto |  | 1 |

### 4 Navigation & Layout

| Component | ID | Size | Slots | Refs |
|---|---|---|---|---|
| App Header | `fqLch` | 1440×64 |  | 17 |
| Chat Header | `H0YWK` | 1156×60 |  | 62 |
| Sidebar | `hj5RV` | 284×1024 | `Session List` (uHSbn): Session Group Label / Session Item | 61 |
| Sidebar Brand | `T8TdZq` | 256×auto |  | 1 |
| Agent Switcher | `RZF5q` | 256×auto |  | 1 |
| Sidebar Nav Item | `MoK3u` | 256×auto |  | 29 |
| Sidebar Footer | `CpCSr` | 284×auto |  | 1 |
| Session Item | `SEJaD` | 248×auto |  | 311 |
| Session Group Label | `rQVuA` | auto×auto |  | 153 |
| Mobile Status Bar | `CLJUJ` | 390×44 |  | 9 |
| Home Indicator | `mSdhx` | 390×28 |  | 6 |
| Section Heading | `o1lqG` | auto×auto |  | 31 |
| Tile Label | `Vu7nt` | auto×auto |  | 97 |

### 5 Composer & Messages

| Component | ID | Size | Slots | Refs |
|---|---|---|---|---|
| Composer | `K6k66O` | 760×auto | `Attachments` (I5xpa): Attachment Chip / Image Attachment | 76 |
| User Message | `EfHME` | 760×auto |  | 98 |
| Agent Message | `BsXl7` | 760×auto | `Content` (BohzX) | 121 |
| Message Actions | `SnIqS` | auto×auto |  | 8 |
| Message Editor | `x0laEo` | 520×auto |  | 1 |
| Version Pager | `FVkS9` | auto×auto |  | 2 |
| Attachment Chip | `xdoWs` | auto×auto |  | 10 |
| Image Attachment | `z1ehKR` | 54×54 |  | 4 |
| File Card | `Mr5AY` | 260×auto |  | 10 |
| Jump to Latest | `R2yN9` | auto×auto |  | 2 |
| Typing Indicator | `eFeRx` | auto×auto |  | 3 |
| Thinking Row | `Fg95V` | 640×auto |  | 5 |
| Starter Prompt | `fkUCB` | 320×auto |  | 28 |

### 6 Agent Activity & Feedback

| Component | ID | Size | Slots | Refs |
|---|---|---|---|---|
| Tool Call Chip | `Hbhy0` | auto×auto |  | 93 |
| Tool Call Detail | `pkhri` | 640×auto |  | 15 |
| Timeline Step | `JGoho` | 640×auto |  | 15 |
| Plan Step | `aKwZB` | 480×auto |  | 38 |
| Plan Card | `I05g84` | 520×auto | `Steps` (LlLdq): Plan Step | 5 |
| Status Banner | `dcn54` | 720×34 |  | 6 |
| Inline Error | `Sl1FL` | 560×auto |  | 6 |
| Notice Banner | `D9HsR` | 560×auto |  | 9 |
| Callout | `TqvAv` | 560×auto |  | 9 |
| Empty State | `HUrKd` | 560×auto |  | 12 |

### 7 Rich Content & Artifacts

| Component | ID | Size | Slots | Refs |
|---|---|---|---|---|
| Code Block | `wW1XY` | 640×auto |  | 19 |
| Content Card | `l5WJH` | 640×auto | `Actions` (LibZM): Button / Secondary / Icon Button, `Body` (ZnzO6) | 5 |
| Source Row | `q7ISXo` | 320×auto |  | 4 |
| Download File | `s5qDxc` | 420×auto |  | 7 |
| Artifact Card | `SMBup` | 440×auto |  | 31 |
| Artifact Toolbar | `AwpSJ` | 720×52 | `Extra` (nkW3V) | 15 |
| Panel Tab | `HXUoW` | auto×auto |  | 6 |
| Version Row | `Z4Hd3` | 260×auto |  | 16 |
| Library Tile | `JCduD` | 260×auto |  | 24 |

### 8 Agent Interactions & Management

| Component | ID | Size | Slots | Refs |
|---|---|---|---|---|
| Approval Card | `m1FtM` | 520×auto |  | 9 |
| Permission Prompt | `YwhPJ` | 560×auto |  | 3 |
| Detail Row | `wGPRe` | 400×auto |  | 35 |
| Agent Card | `VZuIf` | 392×auto |  | 41 |
| Capability Row | `V6Dax` | 560×auto |  | 24 |
| Recent Session Row | `V8961f` | 800×auto |  | 30 |
| Info Row | `NEFiE` | 320×auto |  | 12 |
| Tip Card | `HFzDp` | 300×auto | `Extra` (IepYs): Kbd | 6 |

## Reference screens and boards

| Frame | ID | Size |
|---|---|---|
| Catalog — / | `PBQLh` | 1440×1024 |
| Chat — /agents/coding-agent/:sessionId | `wtDYF` | 1440×1024 |
| New Session — /agents/health-assistant | `uBRCZ` | 1440×1024 |
| States & Edge Cases | `D21ObU` | 1440×auto |
| Chat Interaction Details | `Q6kwA2` | 2280×auto |
| Agent Working & Failure States | `R9pQQP` | 2280×auto |
| Artifact — Document · Read | `oQYrz` | 1440×1024 |
| Artifact — Document · Edit | `lKqzP` | 1440×1024 |
| Artifact — Document · Agent editing | `rXi6e` | 1440×1024 |
| Artifact — Code · Expanded full width | `fUZV4` | 1440×1024 |
| Artifact — HTML/App preview | `j2uc1W` | 1440×1024 |
| Artifact — Spreadsheet | `LrhPn` | 1440×1024 |
| Artifact — Version history & compare | `F8d7U` | 1440×1024 |
| Mobile — Chat with artifact | `JLUHx` | 390×844 |
| Mobile — Artifact sheet | `KXQcB` | 390×844 |
| Mobile — Artifact overflow menu | `SZqQD` | 390×844 |
| Artifacts — Cards & States | `F9oiRc` | 2280×auto |
| Rich Reply Content | `IVLvU` | 2280×auto |
| Agent-Initiated Interactions | `Lwlwe` | 2280×auto |
| Sessions — Row menu + Pinned | `sV0Oz` | 1440×1024 |
| Sessions — Delete confirmation | `Hkcgi` | 1440×1024 |
| Sessions — Deleted, undo toast | `ABwYF` | 1440×1024 |
| Search — Command palette (⌘K) | `B5LZKO` | 1440×1024 |
| Archived sessions | `HbIFz` | 1440×1024 |
| Artifacts library | `g2nGvw` | 1440×1024 |
| Session info drawer | `E3lQz` | 1440×1024 |
| Sessions — Dialogs & states | `vBr4V` | 2280×auto |
| Catalog — sort menu open | `S1S8vL` | 1440×1024 |
| Catalog — empty | `j8NhJ` | 1440×1024 |
| Agent detail — /agents/coding-agent/about | `x05s4W` | 1440×1024 |
| Settings — /settings | `Za8Qd` | 1440×1024 |
| Keyboard shortcuts overlay (⌘/) | `x8PmN9` | 1440×1024 |
| Onboarding — first run | `RPCu8` | 1440×1024 |
| Agent management — flows & states | `yzVIz` | 2280×auto |

## User flows

### Flow 1 — First run

A new user meets Agent Hub, registers their first agent and tests the connection before chatting.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F1.1 Welcome | `Q8Pxn` | 1440×1024 | Clicks “Get started” |
| F1.2 Empty catalog | `uvCOZ` | 1440×1024 | Clicks “Add agent” |
| F1.3 Add agent · Details | `bqPha` | 1440×1024 | Fills name, icon, colour → Continue |
| F1.4 Add agent · Connect | `W44RC` | 1440×1024 | Picks AgentCore, pastes ARN → Continue |
| F1.5 Testing connection | `o0Tgcm` | 1440×1024 | Checks run automatically |
| F1.6 Connection verified | `wJQMG` | 1440×1024 | Clicks Continue |
| F1.7 Agent ready | `nXcUh` | 1440×1024 | Clicks “Back to catalog” |
| F1.8 Catalog with new agent | `h9bFF` | 1440×1024 | Opens an agent → Flow 2 |

### Flow 2 — Start chatting

From the catalog to a finished reply: pick an agent, start a session, watch it think, call tools and stream an answer.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F2.1 Catalog | `UwUMM` | 1440×1024 | Clicks the Coding Agent card |
| F2.2 Agent detail | `PHIgn` | 1440×1024 | Clicks “Start session” |
| F2.3 New session | `mU5UB` | 1440×1024 | Clicks a starter prompt |
| F2.4 Composing | `xpt2S` | 1440×1024 | Edits the prompt, presses Enter |
| F2.5 Waiting for the agent | `qky6s` | 1440×1024 | First event arrives |
| F2.6 Thinking & tool calls | `KfCS1` | 1440×1024 | Reply starts streaming |
| F2.7 Streaming reply | `jMA3f` | 1440×1024 | Reply completes |
| F2.8 Finished reply | `jX0Iq` | 1440×1024 | Picks a follow-up or keeps chatting |

### Flow 3 — Agent produces work

Research Analyst turns a request into a document artifact, then the user opens, edits, downloads and compares versions.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F3.1 Request & research | `fqfye` | 1440×1024 | Tools finish; writing starts |
| F3.2 Generating artifact | `iFd2Z` | 1440×1024 | Document completes |
| F3.3 Reply with artifact | `N6qx3e` | 1440×1024 | Clicks “Open” |
| F3.4 Artifact panel | `yQVzu` | 1440×1024 | Opens the version menu |
| F3.5 Version menu | `uQV6q` | 1440×1024 | Clicks the title to edit |
| F3.6 Edit & download | `p4zZq` | 1440×1024 | Chooses PDF; asks for a change |
| F3.7 Agent edits live | `V8FHhg` | 1440×1024 | Clicks “Compare versions” |
| F3.8 Compare versions | `C9b9ml` | 1440×1024 | Restores v2 or exits compare |

### Flow 4 — Human in the loop

Bank Agent pauses for approval before moving money, then runs a long background task and notifies the user when it's done.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F4.1 Approval requested | `C6Znz` | 1440×1024 | Reviews details, clicks “Approve transfer” |
| F4.2 Confirm with Face ID | `RPA2L` | 1440×1024 | Authenticates |
| F4.3 Transfer sent | `Xju40` | 1440×1024 | Asks for a monthly reconciliation |
| F4.4 Branch · Denied | `oTQRM` | 1440×1024 | If the user clicks Deny instead |
| F4.5 Long task running | `l7fEn` | 1440×1024 | Leaves the page |
| F4.6 Task complete, anywhere | `pwVxh` | 1440×1024 | Clicks “View result” |
| F4.7 Result | `z5d9eA` | 1440×1024 | Reviews flagged items |

### Flow 5 — Attachments & voice

The user shares a photo and a lab report with Health Assistant, gets an answer about them, then dictates a follow-up.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F5.1 Add attachments | `dHNiV` | 1440×1024 | Clicks “Add photos”, picks files |
| F5.2 Uploading | `q83nhv` | 1440×1024 | Uploads finish; types a question |
| F5.3 Ready to send | `Y5upBH` | 1440×1024 | Presses Enter |
| F5.4 Agent reads the files | `N3iNA` | 1440×1024 | Answer arrives |
| F5.5 Answer with care note | `NxvnJ` | 1440×1024 | Taps the mic to follow up |
| F5.6 Dictating | `RL8tk` | 1440×1024 | Taps ✓ to finish |
| F5.7 Transcribed, ready to send | `TNRet` | 1440×1024 | Presses Enter |

### Flow 6 — Recovering from problems

What the user sees when things go wrong: a failed reply, a dropped connection, rate limits, a session that's too long, and an agent going offline.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F6.1 Reply failed | `yVA1S` | 1440×1024 | Clicks Retry |
| F6.2 Retry succeeds | `BMzRs` | 1440×1024 | Connection drops mid-reply |
| F6.3 Reconnecting | `tPwOw` | 1440×1024 | Connection returns |
| F6.4 Back online | `PsIbC` | 1440×1024 | Sends several requests quickly |
| F6.5 Rate limited | `HmCpV` | 1440×1024 | Later: session grows very long |
| F6.6 Session too long | `M7v0g` | 1440×1024 | Clicks “Start new session” |
| F6.7 Fresh session with summary | `qdFc2` | 1440×1024 | Switches to Home Ops |
| F6.8 Agent offline while typing | `j5dD9g` | 1440×1024 | Draft kept; waits or switches |

### Flow 7 — Finding & organising

Search everything with ⌘K, look up session details, share and export a session, delete with undo, and browse archives and artifacts.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F7.1 Search with ⌘K | `wsLQm` | 1440×1024 | Opens a result |
| F7.2 Session info | `xCNWU` | 1440×1024 | Opens the row menu in the sidebar |
| F7.3 Session row menu | `QVH2g` | 1440×1024 | Chooses “Share…” |
| F7.4 Share session | `JFeoX` | 1440×1024 | Copies the link; then Export… |
| F7.5 Export session | `n8oFZ` | 1440×1024 | Exports; then Delete… |
| F7.6 Confirm delete | `Ba2LD` | 1440×1024 | Clicks “Delete session” |
| F7.7 Deleted with undo | `ZX9nG` | 1440×1024 | Opens Archived |
| F7.8 Archived sessions | `b0VrqQ` | 1440×1024 | Opens Artifacts |
| F7.9 Artifacts library | `JROuy` | 1440×1024 | Opens an artifact → Flow 3 |

### Flow 8 — Switching agents

Move between agents from anywhere. Switching always opens a fresh session; past sessions stay one click away in the sidebar.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F8.1 Mid-conversation | `oI49h` | 1440×1024 | Clicks the agent switcher |
| F8.2 Agent switcher | `ga0YM` | 1440×1024 | Picks Health Assistant |
| F8.3 Fresh session | `I09y2` | 1440×1024 | Opens a past session from the sidebar |
| F8.4 Past session reopened | `jrgPt` | 1440×1024 | Presses ⌘J to switch quickly |
| F8.5 Quick switch (⌘J) | `gihjG` | 1440×1024 | Picks Coding Agent → Flow 2 |

### Flow 9 — Settings & management

Change preferences, wipe data safely, learn shortcuts, and manage an agent's details and health.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F9.1 Settings | `jvbtl` | 1440×1024 | Clicks “Delete all…” |
| F9.2 Confirm delete all | `L6KfE` | 1440×1024 | Types DELETE, confirms |
| F9.3 Data deleted | `wbzk3` | 1440×1024 | Presses ⌘/ |
| F9.4 Keyboard shortcuts | `Iicud` | 1440×1024 | Opens an agent's page |
| F9.5 Agent detail | `yz8Mr` | 1440×1024 | Clicks “Edit agent” |
| F9.6 Edit agent | `gpyEo` | 1440×1024 | Saves changes |
| F9.7 Degraded agent in catalog | `H1yh2` | 1440×1024 | Opens Bank Agent anyway |
| F9.8 Degraded agent in chat | `s1omGy` | 1440×1024 | Status recovers automatically |

### Flow 10 — Mobile

The same product on a phone: browse agents, chat, open artifacts as full-screen sheets, reach past sessions from a drawer, and approve actions.

| Screen | ID | Size | Leads on when… |
|---|---|---|---|
| F10.1 Mobile catalog | `UK1JP` | 390×844 | Taps Research Analyst |
| F10.2 Chat with artifact | `j57Yaa` | 390×844 | Taps the artifact card |
| F10.3 Artifact sheet | `o3XCU` | 390×844 | Taps ⋯ |
| F10.4 Overflow menu | `oNbW3` | 390×844 | Downloads; taps back, opens menu |
| F10.5 Sessions drawer | `i46aRN` | 390×844 | Opens Bank Agent session |
| F10.6 Approve on mobile | `GCuQ2` | 390×844 | Taps “Approve transfer” |
