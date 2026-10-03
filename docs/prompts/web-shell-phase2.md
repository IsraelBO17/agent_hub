Continue the web-standard work from `docs/prompts/web-standard.md`. Phase 1 is done; start **Phase 2, step 1**. Stop for my approval at every ⏸, as that prompt says.

## First: check Pencil
Call the Pencil MCP's `get_app_state`. It must report `fleet_dev.pen` as the open file. If it doesn't answer, or no file is open, tell me before anything else (Claude's Pencil server should run the Pen app's binary with `--app desktop`).
- If Pen has **this worktree's copy** open (`agent_hub-web-shell/design/fleet_dev.pen`), you may edit the design when a step needs it, following the root `CLAUDE.md` rules (save, `python3 design/tools/pen_index.py`, commit `fleet_dev.pen` and `INDEX.md` together).
- If Pen has **the main checkout's copy** open (`agent_hub/design/fleet_dev.pen`), treat the design as **read-only**: that copy belongs to my `auth` branch. Ask me to make any design change myself.

## Where things are
- **Work in this folder:** `agent_hub-web-shell`, a git worktree of `agent_hub` on branch `web-shell` (pushed; 1 commit ahead of `main`: `a6f5ce2`, the web profile). Do not touch `../agent_hub`: it is on branch `auth` with my uncommitted API work.
- **The standard and template:** `../web-standard` (GitHub `IsraelBO17/web-standard`, private template repo, standard 1.0, CI green). Read its `README.md`, `CLAUDE.md`, `docs/STANDARD.md` and `docs/RECIPES.md` before anything else.
- **Agent Hub's profile:** `docs/WEB_PROFILE.md` (read it fully), plus `docs/UI_COMPONENTS.md` (Pencil → shadcn map) and ARCHITECTURE D16, D24, D25, D28, D29.

## Decisions already made (don't re-ask)
- Stack: Vite 8, React 19, React Router 8 (data mode), TanStack Query 5, shadcn/ui on **Base UI** (no Radix, D28), Tailwind 4, openapi-typescript + openapi-fetch, MSW 3, Vitest 5, Playwright + axe, ESLint 10, **TypeScript 6.0** (not 7: typescript-eslint and openapi-typescript can't use it yet), npm, Node 24.
- Agent Hub exceptions in the profile: Base UI `toast` instead of Sonner; Base UI `drawer` for mobile sheets; **session delete keeps its 10-second undo** (my decision, kept as an Agent Hub exception, not a standard change); numeric class names `text-12…text-40` and `rounded-4…16` with `cn` configured via `createCn`; the browser's locale and time zone; Sentry switched on at M4.
- MSW replaces F14's `AgentApi` interface (D29). The API is `https://api-fleet.qucoon.com` (D25, amended): use that, not `api.fleet`.

## Known gaps to fix in `../web-standard` (standard 1.1, with a version bump and a CHANGELOG line, pushed after my yes) when you hit them
- The token generator has no shadows, and takes only one input file (Agent Hub needs the Pencil file's variables plus `web/design/scale.json`).
- `cn` doesn't know numeric size names.
- Monorepo use: the template assumes it is the repo root (CI workflow, contract path, `.github/`); `web/` needs `.github/workflows/web.yml` with `working-directory: web` and path filters, the contract at `../api/openapi.yaml`, and root `make web-*` shortcuts. Make the template's monorepo instructions explicit.
- Amplify's build spec in `infra/modules/amplify` must select Node 24 before `npm ci`.
- The prompt's DNS check is out of date: D25 now uses CNAMEs in the `qucoon.com` zone, not a delegated `fleet` zone. Check `dig +short CNAME fleet.qucoon.com` (and Terraform's `dns_records_for_qucoon` output) instead of the NS record.

## Things that bit us in Phase 1 (the template already handles them; keep them in mind)
shadcn's CLI needs `paths` in the root `tsconfig.json`; the `shadcn` package is a dev dependency; shadcn's Sonner wrapper pulls in `next-themes` (replace it); Sentry is lazy-loaded; openapi-fetch needs a `fetch` that reads `globalThis.fetch` per request for MSW to apply; fake only `setTimeout`/`clearTimeout` in stream tests; one known MSW/undici test error is filtered in `vite.config.ts`.

## Phase 2 as written (issue #4; `gh issue view 4 --repo IsraelBO17/agent_hub`)
1. Scaffold `web/` from the template and apply the profile. ⏸
2. Build #4's scope: CSS variables generated from the Pencil file by a script; the typed client and SSE reader for `api/openapi.yaml` (45 s stall); the routes from PRODUCT_PLAN §5 as placeholder pages; the desktop shell (sidebar 284 px, app header, chat column about 760 px) matching the Pencil Sidebar, App Header and Chat Header, usable at 390 px. Use the Pencil MCP for the design, otherwise `design/INDEX.md` and the file's JSON. ⏸
3. Deploy with Amplify (`fleet-dev-web-amplify-us-east-1` exists): connect `main`, attach `fleet.qucoon.com` in Terraform where possible; propose the simplest GitHub connection option and ask; show me the plan and apply only on my yes. ⏸
4. Close out: green checks, deployed, deep links work, tick #4's items, comment with screenshots at 1440 and 390 px, open the PR from `web-shell`.

Out of scope: sign-in (#6), catalog data (#7), chat and streaming UI (#8), Stop (#9), the full mock scenarios (M2).

Start by checking Pencil, then read the files above and `docs/prompts/web-standard.md`, then tell me your plan for step 1 before writing code.
