# Agent Hub

One web app that is a single chat interface for many AI agents (AWS Strands Agents on Amazon Bedrock AgentCore Runtime, LangGraph later). Agents are data from `GET /agents`; adding one must never need UI changes.

**Current stage: planning and foundations.** The only code is the database schema and migrations in `api/` (step 4). Do not scaffold the rest of the app unless asked.

## Read first
- `docs/BUILD_PLAN.md`: the ordered build steps, their status, how we work, and open questions. Start here.
- `docs/ARCHITECTURE.md`: technical decision log (single source of truth; wins over the stack notes in PRODUCT_PLAN).
- `docs/SEND_MESSAGE.md`: the send/stream flow, message statuses, timers and error codes (diagrams in `docs/diagrams/`).
- `docs/DATA_MODEL.md`: Postgres tables, enforced rules and indexes (models in `api/app/db/models.py`, migrations with Alembic in `api/migrations/`).
- `api/openapi.yaml`: the API contract (OpenAPI 3.1): every endpoint, error code, SSE event and message block, plus the API → agent payload. Lint with `npx @redocly/cli lint api/openapi.yaml`.
- `docs/PRODUCT_PLAN.md`: scope (P0/P1/P2), acceptance criteria, screen inventory, roadmap, design critique (§9).
- `design/README.md`: how the design file is organised.
- `design/INDEX.md`: generated map of every component, screen and flow, with node IDs.

## Design file
- The source of truth is `design/fleet_dev.pen` **in this repo**. Open this copy in Pencil, not an older one elsewhere on disk.
- After any design change: save in Pencil, run `python3 design/tools/pen_index.py`, and commit `fleet_dev.pen` and `INDEX.md` together.
- Tokens are Pencil variables (`$accent`, `$text-tertiary`, …). Use tokens, not raw hex, in anything new. Agent colours (`$agent-*`) are only for agent identity (avatars, tiles).
- Type scale: 12 / 13 / 14 / 15 / 20 / 28 / 40. No other font sizes.
- Pencil has no variants: a variant is its own component named `Component / Variant` (e.g. `Callout / Warning`). Instances override content, not colours.
- Charts: follow `docs/CHART_SPEC.md`; the drawn charts in the file are illustrations.
- Layout conventions: desktop 1440×1024, sidebar 284 wide, chat column about 760, artifact panel about 50/50; mobile 390×844. Icons are lucide.
- Flow screens are named `F<flow>.<step> Title`, and each flow row has a "Flow N · Step notes" strip underneath.

## Pencil MCP quirks (learned the hard way)
- **Blank newly inserted frames.** Inserted frames sometimes lay out with a stale +50 y offset and render blank. Fix: Copy the affected top-level frame, then Delete the original. **Never do this to a reusable component**: copying a component creates an instance, not a component.
- **Blank screenshots.** Screenshots taken right after creation, or of nodes inside instances, can come back blank. Retake later, or screenshot the parent.
- **Lost overrides.** Moving component children that instances override can drop those overrides.
- **Slots.** Fill a slot with `Replace(instanceId + "/" + slotId, frameData)`, then Insert or Move content into the returned frame.
- **Script engine:**
  - Functions don't persist between `execute` calls.
  - Prefer `forEach` over `for (const [a, b] of …)` with a single-statement body.
  - Put a `;` before a line that starts with `[` when the previous line ends in `)`.
- **Whole-document traversal.** `Get(document, visitor)` can throw on some refs. Use `c.skipChildren()` on refs, or try / catch.
- **Missing lucide icons.** `clock` and `fingerprint` aren't available; use `timer`, `history` or `shield-check`.

## Git
- Work on `main` unless told otherwise.
