# Agent Hub web app

One signed-in chat interface for many AI agents ([`../docs/PRODUCT_PLAN.md`](../docs/PRODUCT_PLAN.md)). Built to the **Web Development Standard** ([`docs/STANDARD.md`](docs/STANDARD.md)) from the `web-standard` template. Project profile: [`../docs/WEB_PROFILE.md`](../docs/WEB_PROFILE.md). Spec: [`SPEC.md`](SPEC.md). The repository-wide rules in [`../CLAUDE.md`](../CLAUDE.md) apply too (design file, Pencil rules, git).

## Read first
1. `SPEC.md`. The spec comes before code; if a change isn't in it, update it first.
2. The API contract, `../api/openapi.yaml` (D23). Never invent an endpoint or field; a contract change is made in `api/` first.
3. `docs/RECIPES.md`. Follow the recipe; don't improvise a different structure.
4. `docs/STANDARD.md`, then the profile `../docs/WEB_PROFILE.md` (Agent Hub's values) and `../docs/UI_COMPONENTS.md` (Pencil → shadcn map). Decisions: `../docs/ARCHITECTURE.md`.

## Commands
| Command | What it does |
|---|---|
| `make check` | Types, lint, token check, unit and component tests, contract drift, no Radix, build, bundle budget, audit. **Must pass before you say anything is done.** |
| `make e2e` | Playwright with axe, in mock mode, at 1440, 768 and 390 px. Must pass when a screen changed |
| `make dev` | The app on :5173 (copy `.env.example` to `.env.local`; mocks on by default) |
| `make tokens` | Regenerate `src/styles/tokens.css` from the design (still the template's example `design/tokens.json`; issue #4 switches it to `../design/fleet_dev.pen`) |
| `make api` | Regenerate `src/service/generated/` from the contract (`../api/openapi.yaml`) |
| `make fmt` | Fix what ESLint can fix |

Skills: `/new-web-app`, `/sync-tokens`, `/add-page`, `/add-component`, `/add-api-call`, `/add-stream`, `/add-form`, `/add-auth`, `/deploy`, `/pre-merge` (each runs a recipe).

## Layout
`main.tsx` (boot, the only wiring) → `app/router.tsx` (the route table; route files only re-export a screen) → `modules/<feature>/` (screens and domain logic; imported only through `index.ts`) → `components/` (shadcn in `ui/`, plus `form/`, `layout/`) and `service/` (the client, one file per resource, `generated/` types) → `models/` (domain types, `toDomain` mappers). `mocks/` answers every call in mock mode. The golden path (`modules/notes`, `service/notes.ts`) has been removed here; copy its shape from the `web-standard` repository (`../../web-standard` locally, or `IsraelBO17/web-standard`). Lint enforces the import rules (standard §7).

## Defaults (don't ask; use these unless the spec or profile says otherwise)
TanStack Query for server data, with `queryOptions` in `service/` and `staleTime` per resource; URL state through nuqs; forms with React Hook Form, zod and `components/form`; shadcn primitives added with `npx shadcn@latest add`; icons through `components/ui/icon`; every view with loading, empty, error and success states; `ConfirmDialog` for irreversible actions (session delete uses undo instead, a profile exception); mocks first with MSW; Markdown through `SafeMarkdown`; dates through `utils/format-date`; tests next to the code; decisions appended to `docs/decisions.md`. Ask the owner only what's genuinely specific to this app, in one batch, each question with your recommendation.

Agent Hub's exceptions and extra rules (profile): toasts from Base UI `toast`, not Sonner; mobile sheets from Base UI `drawer`; nothing from `@radix-ui` (`make check` fails); type scale `text-12`…`text-40` only; agent colours only for agent identity; light theme only.

## Never
- Write code before `SPEC.md` is approved, or change a screen without updating its screen block.
- Hand-copy a colour, size or font from the design (`make tokens`), or hardcode one in a component.
- Put tokens or personal data in `localStorage`, `sessionStorage`, a URL or a query key; put a secret in a `VITE_*` variable.
- Call `fetch` or the client from a component, fetch in `useEffect`, or copy server data into state or a store.
- Import a module other than through its `index.ts`, use `../`, or import `lucide-react` outside `components/ui`.
- Render HTML from outside the app without sanitising it, or add `rehype-raw`.
- Edit `src/service/generated/` or `src/styles/tokens.css` by hand.
- Delete, skip or weaken a test to get green.
- Read or print `.env*` files (except `.env.example`), or use real customer data.
- Commit, push or deploy without being asked; apply infrastructure without showing the owner the plan and getting a yes.

## Done means
`make check` passes; `make e2e` passes when a screen changed; the change was run in a browser at the profile's widths with screenshots of each state; `SPEC.md`, `README.md` and `CHANGELOG.md` agree; and the standard's definition of done (§25) holds.
