# Agent Hub web app: spec

| | |
|---|---|
| Owner | Israel B. |
| Status | Approved through the planning documents below |
| Version | 0.1.0 |
| Stage | Build (M1) |
| Project profile | [`../docs/WEB_PROFILE.md`](../docs/WEB_PROFILE.md) |
| Standard | Web Development Standard 1.0 |

Agent Hub's web app was specified before this template existed, so the spec lives in the planning documents rather than in this file. This file indexes them, maps the routes to their design frames, and holds the screen blocks for screens as they are built (standard §5, Appendix A).

## 1. Product
- Job, users, principles, scope (P0/P1/P2) and acceptance criteria: [`../docs/PRODUCT_PLAN.md`](../docs/PRODUCT_PLAN.md).
- Milestones and the order of issues: [`../docs/DELIVERY_PLAN.md`](../docs/DELIVERY_PLAN.md).
- Decisions: [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) (D16 front end, D28 components, D29 this standard).

## 2. Screens and routes
From PRODUCT_PLAN §5. Frames are from [`../design/INDEX.md`](../design/INDEX.md) (desktop 1440 × 1024, mobile 390 × 844).

| Route | Screen | Design frame (desktop · mobile) | Signed in? | Priority | Built in |
|---|---|---|---|---|---|
| `/` | Catalog | `PBQLh` · F10.1 `UK1JP` | Yes | P0 | #7 |
| `/agents/:agentId` | New session | `uBRCZ` · F11.2 `HgtnP` | Yes | P0 | #8 |
| `/agents/:agentId/:sessionId` | Session (chat; artifact panel `?artifact=:id&v=:n`) | `wtDYF` · F11.5 `DNypg` | Yes | P0 | #8 |
| `/agents/:agentId/about` | Agent detail | `x05s4W` · `mN9zj` | Yes | P1 | later |
| `/artifacts` | Artifacts library | `g2nGvw` · `GSi1C` | Yes | P1 | later |
| `/archived` | Archived sessions | `HbIFz` · `grrlx` | Yes | P1 | later |
| `/settings` | Settings | `RHrDH` · `RT72e` | Yes | P1 | later |
| `/s/:shareId` | Shared session (read-only) | `q1bvDq` · `W2aSQ` | No | P1 | later |
| `/sign-in` | Sign in | `MMxdZ` · `U0HaRi` | No | P0 | #6 |
| `*` | Page not found | Session not found `H7ZqtC` · F11.19 `HfWCC` (adapted) | No | P0 | #4 |

`about` is a reserved session id: `/agents/:agentId/about` wins over `/agents/:agentId/:sessionId`. ⌘K is an overlay, not a route.

Navigation (PRODUCT_PLAN §5, design `Sidebar` `hj5RV`): brand and collapse; Agent Switcher; New session (⌘⇧O); Search (⌘K); Pinned (P1); the current agent's sessions grouped Today / Yesterday / Previous 7 days / Earlier; footer with the user, Artifacts, Archived and Settings. On mobile the sidebar is the sessions drawer (F10.5 `i46aRN`). The header is `App Header` `fqLch` on the catalog and other pages, and `Chat Header` `H0YWK` in a session.

## 3. Screen blocks
One per screen. The code follows the block; when a screen changes, its block changes first. Issue #4 builds every route above as a placeholder inside the shell; the issue in the table's last column replaces the placeholder with the real screen and rewrites its block.

### screen: Catalog (`/`)
- **purpose:** see every agent and continue where you left off.
- **design:** `PBQLh`; mobile F10.1 `UK1JP`.
- **data:** none yet (#7: `GET /v1/agents`).
- **states:** placeholder: the page title and the shell. #7 adds loading, empty (`j8NhJ`), error (`Jchi9`) and success.
- **open questions:** none.

### screen: New session (`/agents/:agentId`), Session (`/agents/:agentId/:sessionId`)
- **purpose:** start a session with an agent; chat in a session.
- **design:** `uBRCZ`, `wtDYF`; mobile F11.2 `HgtnP`, F11.5 `DNypg`. Header: `Chat Header` `H0YWK`.
- **data:** none yet (#7 agents, #8 sessions, messages and the stream).
- **states:** placeholder: the page title, the ids from the URL, and the chat column (about 760 px).
- **open questions:** none.

### screen: Agent detail, Artifacts library, Archived sessions, Settings, Shared session (P1)
- **purpose:** PRODUCT_PLAN §5.
- **design:** see §2.
- **data:** none until each is built.
- **states:** placeholder: the page title and "Coming later".
- **open questions:** none.

### screen: Page not found (`*`)
- **purpose:** an unknown address, with a way back.
- **design:** adapted from Session not found `H7ZqtC` / F11.19 `HfWCC`.
- **states:** one: the message and "Back to agents".
- **open questions:** none.

## 4. Data and contract
- **Contract:** [`../api/openapi.yaml`](../api/openapi.yaml) (D23), owned in this repository. `make api` reads it; `make check` fails on drift.
- **Error format:** RFC 9457 problem details with `code`, `requestId`, `retryable`, `retryAfter`; field errors are `422 invalid_request` (profile: Contract).
- **Endpoints still mocked:** all, in mock mode (MSW, D29).
- **Streams and polling:** profile (Streams, Polling) and [`../docs/SEND_MESSAGE.md`](../docs/SEND_MESSAGE.md): keep-alive every 15 s, stall after 45 s, then poll the message every 2 s; sessions list every 20 s.

## 5. Auth
Profile (Identity) and D8: Google sign-in, access token in memory, refresh cookie set by the API, one user in v1 (D9), no idle timeout. Built in #6.

## 6. Design
- **Source:** [`../design/fleet_dev.pen`](../design/fleet_dev.pen) (Pencil). Colours and fonts from its variables, sizes from `design/scale.json` (profile: Token pipeline).
- **Type scale:** 12, 13, 14, 15, 20, 28, 40. **Layout:** sidebar 284, chat column about 760, artifact panel about 50/50. **Icons:** lucide.
- **Widths to check:** 390, 768, 1440 (and nothing breaks at 360).
- **Dark mode:** not in v1.

## 7. Non-functional
Profile: browsers and WCAG 2.2 AA per the standard; initial JS 200 KB gzip; the browser's locale and time zone; Sentry from M4; no personal data beyond the signed-in user's name, email and picture.

## 8. Hosting and environments
Profile (Hosting, Environments, Domain): AWS Amplify, one `dev` environment from `main`, `https://fleet.qucoon.com`.

## 9. Open questions
Tracked in ARCHITECTURE §4 and §5, and in UI_COMPONENTS §5 (design gaps).

## Order of work
Issues in `../docs/DELIVERY_PLAN.md`: #4 shell, tokens and client → #6 sign-in → #7 catalog → #8 chat and streaming → #9 Stop → later issues.
