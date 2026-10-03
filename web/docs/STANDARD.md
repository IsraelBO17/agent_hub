# Web Development Standard

| | |
|---|---|
| Owner | Boluwatife Israel |
| Version | 1.1 (2026-10-03): monorepo setup (recipe 1, step 0; `CONTRACT` in the Makefile); mock response helpers outlive the example; tokens from several sources, with shadows and the radius and shadow scales owned by the design; `cn` told the design's size names; `make check` rejects font sizes outside the type scale; the axe helper skips endless animations. 1.0 (2026-10-03): first version |
| Applies to | Every web frontend I build, for any project |
| Default stack | **React 19, TypeScript, Vite, React Router, TanStack Query, shadcn/ui on Tailwind, npm** (§3). Anything else is a documented exception. |
| Structure | §1–25 are the standard. §26 explains **profiles**: one per project, kept in that project's repository. Appendices hold templates and reference code. |
| Home | [`web-standard`](https://github.com/IsraelBO17/web-standard), a template repository: every web app repository starts from it |
| Sibling | [API Development Standard](https://github.com/IsraelBO17/api-standard) (1.1) and [Agent Development Standard](https://github.com/IsraelBO17/agent-standard) (2.2). Where they cover the same topic (errors, streams, secrets, tags, versioning) they agree. |

**MUST** is required to ship. **SHOULD** is expected; skipping it needs a written reason in the repository's README. **MAY** is optional.

---

## 1. What this covers

A **web app** here is one deployable browser frontend: a single-page app built to static files, talking to one or more HTTP APIs described by a contract. It is built mostly by a coding agent (Claude Code) with the owner approving decisions (§6.1).

Build the simplest thing that works:

| If the project needs… | Build |
|---|---|
| a signed-in app (dashboard, tool, chat) | The default: a Vite SPA (§3) |
| public pages that search engines and link previews must read | Next.js, under the exception rules in Appendix D. Only those pages, if the rest can stay an SPA |
| a reply or result that arrives over time | A stream (§12) |
| changes made elsewhere to show up | Polling with TanStack Query (§11). A push channel only when the profile asks for one |
| a backend that isn't built yet | Mocks first (§11.5), then the real API behind the same client |
| a second frontend for the same API | A second repository from this template. Share the contract, not code |

## 2. Principles

1. **Default stack, documented exceptions** (§3), so every app is built, tested and run the same way.
2. **Built for coding agents.** Every repository tells a coding agent how to work in it (`CLAUDE.md`, recipes, skills) and how to check its own work (`make check`) (§6.1).
3. **Spec, then design and contract, then code.** What the app does is written in `SPEC.md`; how it looks comes from the design file; what goes over the wire comes from the API contract. Code implements all three (§4, §5).
4. **Tokens, not values.** Every colour, size, radius, shadow and font comes from a design token generated from the design tool. Never a hand-copied hex (§8).
5. **The contract is the types.** API types are generated from the OpenAPI contract. A field that isn't in the contract doesn't exist (§11).
6. **Server data lives in one place.** TanStack Query owns it. Never copied into component state, a store or context (§10).
7. **Every state is designed.** Loading, empty, error, permission-gated and success, for every view. No blank screens, no raw "no data" (§15).
8. **Accessible and responsive by default.** WCAG 2.2 AA, keyboard-first, usable from 360 px. Checked by tools, not by intention (§16, §17).
9. **Untrusted content stays untrusted.** Tokens never in browser storage; Markdown sanitised; untrusted HTML only in a sandboxed frame (§14, §19).
10. **Structure is enforced.** Layer rules, file names and sizes are lint errors, not advice (§23).

## 3. Default stack

| Concern | Default | Notes |
|---|---|---|
| Runtime and packages | **Node 24 LTS** (`.nvmrc`), **npm** (`package-lock.json` committed, `npm ci` in CI) | The profile MAY choose pnpm |
| Language | **TypeScript 6.0**, strict (§23) | TypeScript 7 (the native compiler) has no compiler API yet, so typescript-eslint and openapi-typescript can't use it. Move to 7 when both support it |
| UI | **React 19** | |
| Build | **Vite 8** with `@vitejs/plugin-react` and `@tailwindcss/vite` | `resolve.tsconfigPaths` for the `@/` alias |
| Routing | **React Router 8**, data mode (`createBrowserRouter`) (§9) | Route loaders are not used for data; TanStack Query owns it |
| Server state | **TanStack Query 5** (§11) | |
| URL state | **nuqs** with its React Router adapter (§10) | |
| Client state | **Zustand**, only when needed (§10) | |
| Components | **shadcn/ui on Base UI** (§8) | Vendored into `src/components/ui` |
| Styling | **Tailwind CSS 4**, themed by generated design tokens (§8) | |
| Icons | **lucide-react**, behind one `Icon` wrapper (§8) | |
| API client | **openapi-typescript** (types) + **openapi-fetch** (client) (§11) | Query hooks hand-written in `service/` |
| Streams | `fetch` + the standard's SSE reader (§12, Appendix C6) | Not `EventSource` |
| Forms | **React Hook Form** + **zod 4** (§13) | |
| Tables | TanStack Table through the shadcn data-table pattern | |
| Charts | **Recharts** behind wrappers in `components/charts` | |
| Markdown | **react-markdown** + **remark-gfm**, no raw HTML (§19) | |
| Toasts | **Sonner** through `components/ui/sonner` | |
| Mocks | **MSW 3** (§11.5) | |
| Unit and component tests | **Vitest 5** + Testing Library + jsdom + `msw/node` (§22) | |
| End-to-end, accessibility | **Playwright** + `@axe-core/playwright` (§22) | |
| Lint | **ESLint 10** flat config with typescript-eslint, react-hooks, jsx-a11y, boundaries, check-file (§23) | |
| Error reporting | **Sentry** (`@sentry/react`) behind one `reportError` function (§21) | |
| Hosting | Static files with an SPA rewrite to `index.html`; the host is set by the profile (§24) | |
| CI | GitHub Actions running `make check` and the end-to-end suite (§25) | |

- **One library per concern.** Never two (no zod and Yup, no two icon sets, no two toast libraries).
- **Pre-approved supporting packages** (no need to ask): everything in the table, plus `@tanstack/react-query-devtools`, `@testing-library/*`, `@vitest/coverage-v8`, `@sentry/vite-plugin`, `dompurify`, `@eslint/compat`, `eslint-import-resolver-typescript`, and whatever `npx shadcn add` installs. Any other dependency: ask first, and confirm it is maintained and widely used.
- **Read the installed version before using an API.** Check `package.json` and the library's current docs; follow the installed version, not memory.

**Exceptions.** Another framework (Next.js for public pages, Appendix D), component library (MUI) or state library is allowed when the README says why. The rest of the standard still applies: "token" means the theme value, "primitive" means that library's component.

## 4. Lifecycle and gates

| Stage | What happens | Exit gate |
|---|---|---|
| **0. Spec** | Intake with the owner: `SPEC.md` (Appendix A) | Users, screens and routes, states, data, auth model, non-functional needs and open questions written; owner approved |
| **1. Design and contract** | Tokens generated from the design tool; every screen in the spec mapped to a design frame (or marked "agent designs it"); the API contract located, or a mock contract written | `make tokens` produces the token file; `make api` generates the client; owner approved |
| **2. Build** | Features built in dependency order, mock-first, each with its states and tests | `make check` and `make e2e` green; screenshots at the profile's widths compared with the design |
| **3. Deployed** | Built and deployed by the host, with the SPA rewrite | Deep links load; the smoke test passes against the deployment; plan shown to the owner before any infrastructure change |
| **4. Live** | Real use | A week without an open blocker; errors reaching the error reporter |
| **5. Retired** | Traffic stopped | Domain and hosting removed; data held in the browser cleared on the next visit or documented |

## 5. The spec

Every repository MUST start with `SPEC.md` (Appendix A), written with the owner **before any code**. It captures what only the owner knows: who uses the app and on which devices, the screens and their routes, what each screen shows in every state, the data each screen needs and where it comes from, the auth model, the design source, non-functional needs (browsers, accessibility, budgets) and integrations. Anything the owner hasn't answered stays in **Open questions**; it is never silently defaulted.

Each screen gets a **screen block** in `SPEC.md` before its code: route, purpose, design frame, data (query and freshness), actions (mutation and what it invalidates), states, permissions, and open questions. When a screen changes, the block changes first, in the same commit as the code and tests.

## 6. Repository

- One repository per app, created from the **web-standard** template, named by the profile (for example `<project>-web`). When the app lives inside a product monorepo, the template's contents go in that repository's web folder, and what must sit at the repository root moves there (recipe 1, step 0): the CI workflow (run in the folder, filtered to its paths), the Dependabot entry, and any root shortcuts. The `Makefile`'s `CONTRACT` points at the contract wherever it lives.

```
<app>/
├── SPEC.md                 §5
├── CLAUDE.md               For coding agents: read order, commands, defaults, "never" list (§6.1)
├── Makefile                `make check` (the done gate), `make e2e`, `make dev`, `make tokens`, `make api`
├── README.md               What it does, how to run, test and deploy; owner; exceptions to this standard
├── CHANGELOG.md            One line per released version
├── docs/                   STANDARD.md (snapshot), RECIPES.md, PROFILE_TEMPLATE.md, decisions.md
├── .claude/skills/         Claude Code skills that run the recipes (§6.1)
├── .github/                workflows/ci.yml, dependabot.yml
├── design/                 The design tool's exported variables (tokens.json), when the design file isn't in this repository
├── contract/openapi.yaml   The API contract, unless the profile points elsewhere (`CONTRACT` in the Makefile)
├── scripts/                gen-tokens.ts (+ tokens/ adapter), check-tokens.ts, check-bundle.ts, check-audit.ts
├── e2e/                    Playwright specs
├── public/                 Static files served as is
├── index.html, vite.config.ts, tsconfig*.json, eslint.config.js, playwright.config.ts, components.json
├── package.json, package-lock.json, .nvmrc, .env.example
└── src/
    ├── main.tsx            Boot: monitoring, mocks (when enabled), providers, router. The only wiring.
    ├── app/                router.tsx (the route table) and routes/ (one thin file per route)
    ├── modules/<feature>/  Screens and domain logic, one folder per feature (§7)
    ├── components/         ui/ (shadcn + app composites), form/, layout/, charts/, data-table/
    ├── service/            client.ts, api-error.ts, describe-error.ts, sse.ts, one file per resource, generated/ (codegen output)
    ├── models/             Domain types and toDomain mappers
    ├── store/              Zustand stores (rare)
    ├── provider/           App-wide providers and the query client (auth wiring, toasts, tooltips)
    ├── lib/                Third-party setup (monitoring, `cn`), token-names.ts (generated)
    ├── utils/              Pure helpers (formatDate, formatMoney)
    ├── hooks/              Domain-free hooks
    ├── mocks/              MSW handlers/ (index.ts lists them), data/, scenarios/, responses.ts (problem, sse, event)
    ├── styles/             tokens.css (generated), theme.css (shadcn mapping), globals.css
    └── test/               Vitest setup and render helpers
```

### 6.1 Working with coding agents

Apps are built mostly by coding agents with the owner approving decisions. Every repository therefore carries:

| File | Purpose |
|---|---|
| `CLAUDE.md` | Read at the start of every session: what the app is, read order (`SPEC.md` → the contract → `docs/RECIPES.md` → `docs/STANDARD.md` → profile), commands, layout in one line, defaults to use without asking, a "never" list, and what "done" means |
| `docs/RECIPES.md` | Step-by-step playbooks: start a new app, sync tokens, add a page, add a component, add an API call, add a stream, add a form, add auth, deploy, pre-merge. Each ends with **Verify** |
| `.claude/skills/` | Claude Code skills that run the recipes: `/new-web-app`, `/sync-tokens`, `/add-page`, `/add-component`, `/add-api-call`, `/add-stream`, `/add-form`, `/add-auth`, `/deploy`, `/pre-merge` |
| `Makefile` | `make check`: types, lint, token check, unit tests, contract drift, build, bundle budget, audit. The gate a coding agent runs before saying anything is done. `make e2e` runs the browser suite |
| `docs/decisions.md` | The decision log: every assumption, deviation from the design and judgment call (date, screen or feature, decision, reason, alternative rejected). Append only. The profile MAY name another file |

Rules:
- **Spec before design and contract before code.** A coding agent writes `SPEC.md` and stops for the owner's approval; then maps screens to the design and the contract and stops again.
- **Recipes over improvisation.** When a recipe is missing or wrong, fix the recipe in the template (with a version bump) rather than working around it.
- **Defaults over questions.** Decide without asking: naming, spacing between two reasonable options, and the states a design omits (designed properly, and logged in the decision log). Ask only what the spec, profile and this standard don't settle; ask in one batch, each question with a recommendation.
- **Ask first** (stop and wait): token storage or any auth-model decision; security headers and CSP; payments, money handling, personal data; destructive actions (deleting data, rewriting history, removing tests); a contract detail that is missing or ambiguous (never invent an endpoint or field); a dependency outside §3's list; a new store or shared abstraction; a material deviation from the design; changing a stack choice.
- **Unattended runs** (headless, scheduled, or told not to wait): state the plan, do everything not on the ask-first list, then stop and list the decisions needed.
- **Scope.** Do what was asked. No unrelated refactors, extra features or abstractions for hypothetical reuse. Report worthwhile extras instead.
- **Self-check before done.** `make check` passes, `make e2e` passes when a screen changed, and the change was run in a browser, not just written.
- **Evidence.** Report only what was run: each check's command and result, screenshot paths for each state at each width, the tests added. If a check couldn't run, say so and name what is unverified. Never write "verified" without the evidence in the same report.
- **Keep them in sync.** A change to this standard updates the recipes, skills and `CLAUDE.md` in the same release.

### 6.2 Agent conduct: git, secrets, test data

- **Git.** Don't commit, push, open pull requests or tag unless asked. When asked: work on a branch, never on `main`; never force-push, skip hooks or rewrite pushed history; stage by path, not `git add -A`; one concern per commit, each leaving the repository green. Run artifacts (screenshots, traces, reports) go to the gitignored `artifacts/` folder.
- **Secrets.** Never read, print, copy or summarise `.env*` files (except `.env.example`), key files or token stores. Never put a secret in code, reports, commits, logs, screenshots, fixtures or the decision log. If a committed secret turns up, stop and report it; don't rewrite history to hide it.
- **Test data.** Synthetic data and test accounts only, in mocks, fixtures, screenshots and verification. Never real customer data or real credentials.

## 7. Architecture

**Placement question:** does this file know a specific business domain? Yes → `modules/<feature>/`. No → infrastructure (`components/`, `service/`, `lib/`, `utils/`, `hooks/`, …).

**Import rules** (a layer imports only what its row allows; checked by lint, §23):

| Layer | May import |
|---|---|
| `main.tsx` | `app`, `provider`, `lib`, `mocks` (dynamically, when mocks are on), `styles` |
| `app` | `modules` (barrels), `provider`, `components`, `lib` |
| `provider` | the `modules/auth` barrel, `service`, `store`, `components`, `lib`, `utils` |
| `modules/<feature>` | `components`, `service`, `models`, `store`, `hooks`, `utils`, `lib`, and the `modules/auth` barrel. Never another feature |
| `components` | `components`, `hooks`, `utils`, `lib` |
| `service` | `models`, `lib`, `utils` |
| `store` | `models`, `utils`, `lib` |
| `models` | `utils`, and types from `service/generated` |
| `hooks` | `utils`, `lib` |
| `lib`, `utils` | nothing internal (`lib` MAY import `utils`) |
| `mocks` | `models`, `utils`, types from `service/generated` |

- Nothing imports `app` or `main.tsx`. If an import is forbidden, the file is in the wrong layer.
- `service` never imports `store` or `modules`. The client reports a failed refresh through a handler that `provider/` registers.
- Two features need the same thing: if it is domain-free, promote it to the shared layer; if it is a shared domain concept, ask.

**Module skeleton** (subfolders only when they have content; group by kind past about five loose files):
```
modules/<feature>/
  components/        one component per file
  modals/            one dialog per file
  hooks/             use-*.ts (domain hooks, e.g. useNotes)
  utils/             feature-only pure helpers
  schemas.ts         form schemas (§13)
  <feature>-page.tsx the screen a route renders
  index.ts           the barrel: the only public entry point
```

**Placement order** (stop at the first match): wraps a URL → `app/routes/`; knows one domain → that module; generic → `components/`; a pure helper used across features → `utils/`; third-party wiring → `lib/`. Start every component inside its feature and promote it only when a second feature needs it and it knows no domain. Never create `components/shared/`.

**Hard rules**
- One component, hook or helper per file. Vendored shadcn files in `components/ui` keep their upstream multi-export shape; app composites there still follow the rule.
- Import a module only through its barrel (`@/modules/notes`). Use the `@/` alias; never `../`.
- Route files contain no logic: they import a screen from a module barrel and export it (Appendix C3). A route file over about 15 lines means logic leaked in.
- Files: split past about 250 lines; never over 400.
- Naming: kebab-case files and folders; PascalCase components; `use-*.ts` exporting `useXxx`; `<feature>-page.tsx`; wire types from codegen; domain types `<Noun>` in `models/`; mappers `toDomain<Noun>`; request types `<Verb><Noun>Request`.

## 8. Design system

### 8.1 Tokens
- The design tool is the source. Its variables are exported (or read directly from the design file) and **generated** into `src/styles/tokens.css` by `scripts/gen-tokens.ts` (`make tokens`). The generated file starts with a "generated, do not edit" header and is committed. Hand-copying a value from the design is never allowed.
- The generator writes Tailwind 4 `@theme static` variables (`--color-*`, `--font-*`, `--radius-*`, `--shadow-*`, `--text-*`; `static` keeps tokens that only `theme.css` uses) and `--layout-*` sizes, keeping the design's token names. It reads every source the adapter lists (the design tool's variables, and a profile-named file for what the tool has no variables for). Where the design has a dark mode, it writes the dark values under the dark selector; one style, and the scheme flips it.
- **Scales the design owns.** Tailwind's default type scale is always removed; its radius and shadow scales are removed when the design defines its own. `theme.css` aliases shadcn's names onto the design's, so vendored primitives keep working until restyled.
- **Type scale.** Tailwind's default font sizes are removed (`--text-*: initial`) and only the design's scale is defined, each size with its line height. Arbitrary sizes (`text-[17px]`) and sizes the scale doesn't define are rejected by `make check` (§23).
- **shadcn mapping.** shadcn components read their own variables (`--background`, `--primary`, `--accent`, `--ring`, `--sidebar-*`, …). `src/styles/theme.css` sets each one to a design token, `var(--…)` only, never a raw value. When a design token and a shadcn variable share a name but not a meaning, the design's meaning wins, the shadcn variable is pointed at the right token, and the profile records the clash.
- Include the status palette and the chart colours as tokens. Agent-authored or user-authored content (an uploaded document, a generated page) is not themed and isn't subject to this rule.

### 8.2 Styling
- **Precedence, in order:** (1) tokens and the shadcn variant (`cva`) for how a kind of component looks app-wide; (2) a composite component in `components/ui` for a reusable app-specific piece; (3) inline Tailwind classes for genuine one-offs. A repeated inline style is not a one-off; promote it.
- Never hardcode a hex, pixel size or font name in a component. If a token is missing, add it in the design and regenerate.
- Compose classes with `cn` (from `@/lib/utils`, never straight from the `cn` package). It is built with `createCn` and told the design's size names (`src/lib/token-names.ts`, generated), so a numeric size like 13 merges correctly next to a text colour.

### 8.3 Components
- Primitives come from shadcn (`npx shadcn@latest add <name>`), never written from memory. Vendored files stay close to upstream; customise through tokens, variants and `className`, and note each change at the top of the file (`// Customised: …`). Never keep a second copy of a primitive. If a primitive depends on a Next.js-only package (shadcn's Sonner wrapper reads `next-themes`), replace that dependency.
- Each design component maps to one code component: a shadcn primitive with a variant, or a composite in `components/ui` (or in its feature) built from primitives. The mapping is recorded in the component's file header (`// Design: <component name> (<node id>)`).
- Base UI primitives compose with the `render` prop (`<Dialog.Close render={<Button variant="outline" />} />`), not `asChild`.
- Status colours live in one status token set used by one `StatusPill`, which always carries text or an icon.
- Icons: only through `components/ui/icon.tsx`, sized by its `size` token (`xs | sm | md | lg | xl`). Importing `lucide-react` anywhere else is a lint error. Decorative icons are `aria-hidden` (lucide's default); icon-only buttons have an `aria-label`.

### 8.4 Layout
- The app shell (sidebar, header, scrolling content, optional footer) lives in `components/layout`, built on shadcn's `Sidebar`, which becomes a sheet below the mobile breakpoint. It is configured by props (`brand`, `sections`); screens are its children, and `modules/shell` wires the domain (navigation items, user menu). Never edit shell primitives to inject app content.
- The content region scrolls, not the page. Full-height screens (chat, editors) scroll their own panels. Heights use `dvh`.

### 8.5 Dialogs, confirmations and toasts
- One dialog per file, in the owning module's `modals/`. Dialogs are controlled by their opener's state.
- **Destructive actions use the shared `ConfirmDialog`** (an `AlertDialog`): a title naming the thing, one sentence of consequence, Cancel, and a confirm button in the destructive colour. It is controlled by its owner's mutation: it stays open with a spinner while `pending`, shows the error and stays open on failure, and the owner closes it on success.
- Toasts (Sonner) report the outcome of an action the user can't otherwise see, and every failed mutation. Not for validation errors (those go on the field).

### 8.6 Tables and charts
- Tables use the shared `data-table` (TanStack Table): pages pass columns and data. Pagination, sort and filters follow what the API supports and live in the URL.
- Charts use `components/charts` wrappers over Recharts, coloured by the chart tokens, with `accessibilityLayer` on and a text summary or table alternative. Charts are lazy-loaded (§18).

## 9. Routing

- One route table: `src/app/router.tsx`, made with `createBrowserRouter` once, outside React. `RouterProvider` is imported from `react-router/dom`; everything else from `react-router`.
- Every route below the root is **lazy** (`lazy: () => import('./routes/<name>')`, the route file exporting `Component`), so each screen is its own chunk.
- **Error boundaries:** a root `ErrorBoundary` and one per route group, using `useRouteError()` and `isRouteErrorResponse()`. A catch-all `*` route renders the not-found screen. No blank screens or stack traces.
- **Protected routes:** a layout route renders `RequireAuth`, which shows a skeleton while the session is restoring, redirects to the sign-in route with `?next=<path and search>` when signed out, and otherwise renders `<Outlet />` (Appendix C3). It reacts to the session ending on the current page, which router middleware alone does not. The sign-in screen keeps signed-in users out.
- `next` MUST be a relative internal path (starts with `/`, not `//`); anything else becomes `/`.
- Navigation uses `NavLink` (it sets `aria-current="page"`). Each screen renders a `<title>` (React hoists it into `<head>`): `<title>{`${page} · ${app}`}</title>`, one string.
- After a route change, focus moves to the new page's `h1`.
- Deep links need the host to rewrite every unknown path to `/index.html` with status 200 (§24). `vite preview` already does this, so it can't prove the host does.

## 10. State

| Kind | Lives in |
|---|---|
| Server data | TanStack Query only |
| Filters, pagination, sort, tab, the open item | URL search params, through nuqs (`useQueryState` with a parser) |
| Form state | React Hook Form |
| Local UI state | `useState` |
| App-wide client state (rare: a draft, the composer, a panel's width) | One Zustand store per concern in `store/` |

- Never copy server data into `useState`, a store or context; derive from the query.
- `NuqsAdapter` (from `nuqs/adapters/react-router/v8`) wraps the root layout's `<Outlet />`, inside the router.
- Browser storage holds only per-user conveniences (a collapsed panel, an unsent draft), never tokens or personal data, and is cleared on sign-out.

## 11. Data and the API client

### 11.1 Generated types
- `make api` runs `openapi-typescript <contract> -o src/service/generated/schema.d.ts --root-types --root-types-no-schema-prefix`. Generated files are never edited. `make check` runs the same command with `--check` and fails on drift.
- Don't use `--enum` (it emits runtime enums, which `erasableSyntaxOnly` forbids) or `--immutable` (its readonly arrays break openapi-fetch's error types).

### 11.2 The client
- One client, `src/service/client.ts`: `createClient<paths>({ baseUrl, credentials, fetch })` from openapi-fetch, with the base URL from `import.meta.env` and a `fetch` that looks up `globalThis.fetch` per request (so mocks apply whatever the import order) (Appendix C4). It owns the base URL, the auth header, the refresh (§14) and nothing else.
- `src/service/api-error.ts` normalises every failure into one `ApiError` (`status`, `code`, `message`, `requestId`, `retryable`, `fieldErrors`). The default reads RFC 9457 problem details, as the API standard emits; the profile says if the API differs.
- Components and screens never call `fetch` or the client directly, and never fetch in `useEffect`.

### 11.3 Queries and mutations
- One file per resource in `service/` (`notes.ts`): a query-key factory, `queryOptions` per read and a `mutationOptions` (or hook) per write. Each `queryFn` calls the client through `unwrap()`, which throws `ApiError`, and maps the wire shape to the domain shape with `toDomain<Noun>` from `models/`. That is the only place mapping happens; components never see wire shapes.
- Every query sets `staleTime` for its resource. Mutations invalidate exactly the keys they change (`invalidateQueries({ queryKey })`), or update the cache with `setQueryData` when the response carries the new state.
- The query client (`provider/query-client.ts`): queries retry once (never for `4xx` other than `408` and `429`), mutations never; `refetchOnWindowFocus: true`.
- Paged lists use `placeholderData: keepPreviousData` so a page change doesn't flash a skeleton.
- **Polling** uses `refetchInterval` (a number, or a function of the query that returns `false` to stop) with `refetchIntervalInBackground: false`, so a hidden tab doesn't poll. Intervals come from the spec or profile.
- Independent requests run in parallel (separate queries, or `useQueries`), never in a waterfall.

### 11.4 The service layer stays browser-only-safe
`service/` code doesn't touch `window` or the DOM, so the same functions run in tests (`msw/node`) and, under the Next.js exception, on a server.

### 11.5 Mock-first
- For endpoints the backend hasn't built: generate types from the contract (or write the contract first), add MSW handlers and synthetic fixtures in `mocks/`, build the full UI against them, and reconcile the mapper when the real API lands.
- Mocks run at the network layer (MSW), so the real client, error handling and stream reader run in mock mode too. There is no second "mock implementation" of the client.
- In the browser, mocks are on only when `VITE_API_MOCKS=true`, through MSW's Vite plugin (`msw/vite`), so a build with mocks off contains no worker and no handlers (Appendix C7).
- **Scenarios.** Named handler sets in `mocks/scenarios/` (`slow`, `error`, `empty`, `stalled-stream`, …) are chosen with `?scenario=<name>` in mock mode. They are the click-through prototype, the demo and the end-to-end test fixtures in one.

## 12. Streaming

- Streams use **Server-Sent Events read with `fetch`**, because `EventSource` can't send a body or an `Authorization` header. `EventSource` (and MSW's `sse()`) MAY be used only for an unauthenticated `GET`.
- The request goes through the client with `parseAs: 'stream'` (so auth and refresh apply before the stream starts), then the body goes to `readSse()` in `service/sse.ts` (Appendix C6). Its parser is a pure function with unit tests: `id`, `event` and `data` fields, multi-line `data`, comments (keep-alive pings), CR, LF and CRLF line endings, and chunks split anywhere.
- **Stall detection.** The reader aborts with `StreamStalledError` when no bytes (events or pings) arrive for the stall time set by the profile, usually three missed keep-alives. What happens next (poll the record, retry, resume with `Last-Event-ID`) is set by the profile.
- **Cancel.** Every stream has an `AbortController`. Leaving the screen aborts it. A user's Stop calls the API's stop operation (when it has one) and then aborts.
- **Where the stream's state goes.** Events update the TanStack Query cache for the record being streamed (`setQueryData`), batched to at most one update per animation frame. When the stream ends, the record is invalidated and refetched, so the cache matches the server.
- **Calm rendering.** Streamed content never moves what is above it; the view follows new content only when the user is already at the bottom, and otherwise shows "Jump to latest". Reserve space for known-size blocks (§18).
- An error event in the stream is parsed into `ApiError` like any other failure.

## 13. Forms

- The schema lives in the module's `schemas.ts` (zod 4). Form types come from it: `useForm({ resolver: zodResolver(schema) })` infers input and output types. Use `z.input` / `z.output` when they differ (coercion, transforms), `z.infer` only when they don't.
- Fields come from `components/form/` (`TextField`, `TextareaField`, `SelectField`, `CheckboxField`, `SwitchField`, …), each a shadcn `Field` wired through RHF's `Controller`, with the label, required mark, hint and an error shown after the field is touched. Never a raw input wired by hand.
- Submit maps the form's output to a request type, calls the mutation, disables the submit button while pending, maps `ApiError.fieldErrors` onto fields with `setError(name, { type: 'server', message }, { shouldFocus: true })`, puts anything else in a form-level error (`setError('root.server', …)`) or a toast.
- On a failed submit, focus moves to the first invalid field (RHF's default `shouldFocusError`).
- Where the contract defines a request schema, the zod schema matches its fields and limits; the contract wins when they differ.

## 14. Auth and sessions

- Everything auth-related lives in `modules/auth` (sign-in screens, `useSession`, `usePermission`, `<Can>`, sign-out and idle logic) and is wired in `provider/`. Other modules import it only through its barrel. The identity provider and the session endpoints are set by the profile.
- **Tokens.** The access token is held **in memory** (a module variable in `service/`), never in `localStorage`, `sessionStorage` or a non-`HttpOnly` cookie. The refresh token is an `HttpOnly; Secure; SameSite` cookie set by the API. On load, the app restores the session by calling refresh once; until that settles, protected routes show a skeleton, not the sign-in screen.
- If the API only returns tokens in a response body and nothing else is specified, ask.
- **Refresh.** On a `401` the client runs at most one refresh at a time (single-flight); concurrent `401`s wait for the same refresh, then each retries its request once (Appendix C4). A failed refresh clears the session once and sends the user to sign-in with `next`; it never loops.
- **403** shows a no-access view and keeps the session.
- **Sign-out** (user, expiry or idle timeout): call the API's sign-out, clear the query cache, stores and per-user storage, and broadcast it to other tabs (`BroadcastChannel`, no secrets in the message) so they clear and redirect too.
- **Idle timeout**, if the profile sets one: warn about a minute before, then sign out as above. Real user activity resets the timer.
- **Permissions.** The current user comes from a query (`useSession`), not a duplicated store. Gate by role through one `usePermission` hook and one `<Can>` component, never scattered role checks. Gated actions are hidden, or disabled with the reason shown.
- When app and API are on different origins, confirm cookie domain, `SameSite`, CORS credentials and CSRF handling with the backend before building sign-in (ask first).
- Frontend checks are experience only; the API is the authority.
- Design and handle every auth state the product has: signed out, signing in, failed, not allowed, session expired (keep the user's unsaved input), signed out elsewhere.

## 15. UI states and errors

- Every data view implements: **loading** (a skeleton with the layout's shape, not a spinner), **empty** (what it is and the next action), **error** (a readable message, the request id when there is one, and Retry), **permission-gated** (hidden or disabled with a reason), **pagination** where lists grow, and **success**.
- One `EmptyState` composite serves empty, error, not-found and no-access views with consistent layout and copy. It knows no domain: screens pass `{...describeError(error)}`.
- **Errors by type:** validation → on the fields; `401` → the auth flow; `403` → no-access; `404` → not-found; `409` and other business codes → the code's copy in `describeError()` (`service/describe-error.ts`), which every screen passes to `EmptyState`, `ConfirmDialog` or a toast; `5xx`, network and stalls → a friendly message with Retry when `retryable`. Failed mutations toast. No silent `catch`.
- Errors are shown in words; never a status code or stack trace alone.

## 16. Accessibility

- Target **WCAG 2.2 AA**.
- Every input has a visible label; errors are linked with `aria-describedby`; after a failed submit focus moves to the first invalid field.
- Dialogs trap focus, close on Escape and return focus to their trigger (the primitives do this; don't break it when restyling).
- After a route change, focus moves to the page's `h1`. A skip-to-content link is the first focusable element.
- Everything works with the keyboard alone, with no traps, and every interactive element has a visible focus indicator (`focus-visible` ring from the `--ring` token).
- Contrast at least 4.5:1 for text and 3:1 for UI parts. One `h1` per screen and headings in order. Meaning never by colour alone. `prefers-reduced-motion` respected. Live regions (`role="status"`, `aria-live="polite"`) announce streaming progress and async results without stealing focus.
- **Checked by tools:** `jsx-a11y` (strict) in lint, and axe (`@axe-core/playwright`, tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`) on every route and key state with **zero serious or critical** violations. Before a screen is done, tab through it and report the result.

## 17. Responsive and mobile

- Mobile-first: base styles target the smallest width, then `sm`/`md`/`lg` up. Every screen works from 360 px and is checked at the widths the profile sets (default 375, 768 and 1280).
- No horizontal page scroll. Wide tables scroll inside their container or become cards. Touch targets at least 44 × 44 px (the template's `Button` and sidebar items add `pointer-coarse:min-h-11`). Full-height layouts use `dvh`. The on-screen keyboard must not hide the focused input.
- If the design shows only desktop, adapt it and log the decision.
- Support the current and previous major versions of Chrome, Safari (macOS and iOS), Firefox and Edge.

## 18. Performance

- **Targets** (75th percentile, real users): LCP under 2.5 s, INP under 200 ms, CLS under 0.1, measured in the field by the monitoring tool (Sentry's browser tracing records them, §21).
- **Bundle budget.** `make check` builds and runs `scripts/check-bundle.ts`, which measures the gzipped JavaScript the entry needs (from Vite's manifest) and fails above the budget in `package.json` (`"budget": { "initialJsKb": … }`). The profile sets it; the default is 200 KB, and raising it needs a reason in the decision log.
- Every route is lazy (§9). Heavy pieces (charts, editors, syntax highlighting, maps) are `React.lazy` with a sized fallback. Import narrowly.
- Lists over about 100 rows paginate or virtualise.
- No layout shift: images and embeds have dimensions; skeletons match the final layout; fonts are self-hosted (`@fontsource-variable/*`) with `font-display: swap` and a metric-compatible fallback.
- Streamed text updates are batched per frame (§12).
- `useMemo`, `useCallback` and `memo` only for a measured problem.
- Before a release, look at the bundle (`vite build --mode analyze`, or the rolldown visualiser) and run Lighthouse on the main screens (SHOULD).

## 19. Security

- **Build-time config.** Only non-secret values go in `VITE_*` variables (they ship to every browser). `.env` is never committed; `.env.example` lists every variable with a safe value.
- **Headers** are set by the host (§24), and the profile shows them: a Content Security Policy (at least `default-src 'self'`; `script-src 'self'`; `connect-src` the API origins; `img-src 'self' data:` plus named origins; `frame-src` only the sandbox origin; `frame-ancestors 'none'`; `base-uri 'none'`; `object-src 'none'`), `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin` and a `Permissions-Policy`. No inline scripts or styles that need `'unsafe-inline'` for scripts.
- **Untrusted content.** Markdown from users, APIs or models renders through react-markdown with no raw HTML (`skipHtml`), its default URL filter, and links that open with `rel="noopener noreferrer nofollow"` (Appendix C9). Never add `rehype-raw`; if a rehype plugin is added, add `rehype-sanitize` after it.
- **Untrusted HTML** (a generated page, an email body) renders only in an `<iframe sandbox>` **without `allow-same-origin`**, served from a separate origin, with its own strict CSP. `dangerouslySetInnerHTML` only when unavoidable, through DOMPurify, with a comment saying why.
- Validate external input (forms, search params, `postMessage` data, user-supplied URLs) with zod.
- External links use `rel="noopener noreferrer"`. Uploads are checked for type and size before sending (the API enforces too).
- CSRF: cookie-authenticated, state-changing requests rely on `SameSite` plus whatever the API requires.
- Dependencies: the lockfile is committed; `scripts/check-audit.ts` (in `make check`) fails on high or critical advisories in production dependencies; Dependabot opens weekly updates. Build-only tools (the `shadcn` package, whose CSS is resolved at build time) are dev dependencies. An accepted advisory goes in `docs/security-exceptions.md` (advisory id, reason, owner, expiry); an expired entry fails. Never add an exception without asking.
- Anything security-relevant is also enforced by the API.

## 20. Money, dates and sensitive data

- **Money.** Amounts stay as integer minor units or decimal strings, exactly as the API sends them; never floats or float arithmetic (ask before adding a decimal library). Display only through one `formatMoney` (`Intl.NumberFormat` with the currency code from the data). Show the currency wherever more than one is possible.
- **Dates.** Exchange RFC 3339 UTC timestamps. Display in the profile's time zone and locale through one `formatDate` / `formatRelative` (`Intl.DateTimeFormat`, `Intl.RelativeTimeFormat`). Date-only values are never shifted through time zones.
- **Sensitive data** (credentials, tokens, national ids, account and card numbers, balances, personal contact details): masked by default and revealed only by an explicit action where permitted; never in URLs, query keys, browser storage, logs, analytics, error reports, fixtures (use synthetic values), screenshots or the decision log. Correct input attributes (`type="password"`, `autoComplete`, `inputMode`). Card entry only through a payment provider's hosted fields; ask first for any payment work.

## 21. Observability

- **One `reportError(error, context)`** in `lib/monitoring.ts` is the only way code reports an error. It sends to Sentry when `VITE_SENTRY_DSN` is set, and otherwise does nothing (no `console.error` in production code).
- Sentry is a MUST before a production release and a SHOULD before that. Set up in `lib/monitoring.ts` (Appendix C11): loaded with a dynamic import only when `VITE_SENTRY_DSN` is set (so it costs nothing when off; errors reported before it loads are buffered); `environment` and `release` (the git SHA) from build config; browser tracing; React 19's root error hooks (`onUncaughtError`, `onCaughtError`) sent through `reportError`; and **`dataCollection` set explicitly** (no user info, cookies, request or response bodies, query strings or auth headers). `beforeSend` removes anything personal that remains.
- What is reported: unhandled errors, error-boundary errors, failed API calls with status `5xx` or network failures (with the route, feature and `requestId`), and stream stalls. Not expected `4xx` outcomes.
- Source maps are built `hidden`, uploaded by `@sentry/vite-plugin` in the release build, and deleted from `dist/` after upload; they are never served.
- Web vitals (§18) are recorded by the same tool's browser tracing. Product analytics, if the spec wants it, goes through one `track(event, props)` with no personal data.

## 22. Testing

| Layer | What | Tool | When |
|---|---|---|---|
| Unit | Pure utils, mappers, schemas, the SSE parser, the `scripts/` checks | Vitest | Every change |
| Component | Components and screens with logic: states, forms, gating, dialogs | Vitest + Testing Library + `msw/node` | Every change |
| End-to-end | Each screen's main path and most important failure path, in mock mode, at desktop and mobile widths | Playwright | Every pull request |
| Accessibility | axe on every route and key state | `@axe-core/playwright` | With end-to-end |
| Visual | `toHaveScreenshot` for a few key screens (SHOULD), baselines made in the Playwright Docker image | Playwright | With end-to-end |
| Smoke | The app loads, a deep link works, the API answers | Playwright against the deployment | After each deploy |

- Tests sit next to their source (`notes-page.test.tsx`), except end-to-end specs in `e2e/`.
- Use the `mocks/` handlers; override per test with `server.use(...)`; unhandled requests fail the test (`onUnhandledFrame: 'error'`). Never hand-mock `fetch`.
- Query by role, label and text. Render through the shared helper (a fresh `QueryClient` with retries off, and a memory router).
- Each feature ships a happy-path test and its most important failure-path test. A bug is reproduced by a failing test first. No chasing coverage numbers.
- **Fake timers** (stall timers, polling): turn them on before the timer starts, fake only `setTimeout` and `clearTimeout` (faking the rest breaks Node's `fetch`), use `shouldAdvanceTime: true` and `userEvent.setup({ advanceTimers: vi.advanceTimersByTime })`; the setup file exposes a `jest` global so Testing Library advances them (Appendix C10). Restore real timers after each test. In the browser, use Playwright's `page.clock`.
- Never delete, skip or weaken a test to get green. If a test is wrong, say so and fix it deliberately.

## 23. Enforcement

**TypeScript.** `strict`, plus `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`, `erasableSyntaxOnly`, `verbatimModuleSyntax`, `noUncheckedSideEffectImports`; `moduleResolution: "bundler"`; `paths: { "@/*": ["./src/*"] }` without `baseUrl`. No `any` (use `unknown` and narrow). No `@ts-ignore`; `@ts-expect-error` only with a description.

**ESLint** (`eslint . --max-warnings 0`; the template's `eslint.config.js` has all of these):
- typescript-eslint `strictTypeChecked` with the project service, including `no-explicit-any`, `no-floating-promises`, `ban-ts-comment` (`@ts-expect-error` with a description) and `consistent-type-imports`
- `react-hooks` recommended (with the React Compiler rules) and `react-refresh`
- `jsx-a11y` strict
- `react/no-multi-comp` (off in `components/ui`)
- `boundaries/dependencies`: the import table in §7, and other modules only through `index.ts`
- `no-restricted-imports`: no `../`, no deep imports into `@/modules/*/*`, no `lucide-react` outside `components/ui`
- `check-file`: kebab-case file and folder names
- `max-lines`: warn at 250, error at 400 (off for `components/ui`, `service/generated`, `models`, `mocks`, `styles`)
- `import-x/no-cycle`, `no-console` (error)

**Vendored files.** The files `npx shadcn add` writes are listed in `eslint.config.js` (`vendored`) and `scripts/check-tokens.ts` (`skip`): they keep their upstream shape and skip the stylistic type-aware rules. App composites beside them in `components/ui` are held to every rule.

**Token check.** `scripts/check-tokens.ts` fails on hex colours, `rgb(`/`oklch(` literals, arbitrary font sizes (`text-[…]`) and arbitrary pixel values (`-[…px]`) in `src/`, outside generated files, mocks, tests and vendored files; and on a font-size class the type scale doesn't define, vendored files included. `scripts/gen-tokens.ts --check` fails when `tokens.css` or `token-names.ts` is stale.

**Compatibility notes** (2026-10): `eslint-plugin-react` and `eslint-plugin-jsx-a11y` don't yet declare ESLint 10; the template installs them with `overrides` (`"eslint": "$eslint"`) and wraps `eslint-plugin-react` in `fixupPluginRules` from `@eslint/compat`. `openapi-typescript` declares TypeScript 5 only; the template overrides its peer to the installed TypeScript. MSW 3's Node interceptor trips an undici assertion when a test cancels a mocked response body mid-read; `vite.config.ts` ignores exactly that error (`test.onUnhandledError`), and every other unhandled error still fails the run. Remove each workaround when the package catches up.

## 24. Build, deployment and environments

- `npm run build` runs `tsc -b` and `vite build` into `dist/`. The build is the same for every environment except `VITE_*` values.
- **Hosting** serves `dist/` as static files, with: a rewrite of every path that isn't a file to `/index.html` (status 200); long-lived caching for hashed assets (`/assets/*`, `immutable`) and `no-cache` for `index.html`; the security headers in §19. The host, its configuration (in infrastructure as code when the host supports it), names and tags are set by the profile.
- **Environments** are set by the profile (for example a preview per pull request, dev, prod), each with its own `VITE_*` values and monitoring environment. Builds that run against a real API never have mocks on.
- **Deploys are reversible:** roll back by redeploying the previous build. Never couple a frontend release to an unreleased API change; if it can't be avoided, ask first and say so in the report.
- Infrastructure changes are planned and shown to the owner before they are applied.

## 25. CI, versioning and release

- CI (GitHub Actions) runs on every pull request and on `main` (in a monorepo: in the app's folder, on changes to it or the contract): `npm ci`, then `make check` (types, lint, token check, unit and component tests, contract drift, build, bundle budget, audit), then `make e2e` (Playwright with axe, in mock mode). Third-party actions are pinned by commit SHA with the version in a comment; `permissions: contents: read`. Playwright reports and traces are uploaded on failure.
- Dependabot opens weekly updates for npm and GitHub Actions.
- The app's version (semver) is in `package.json`; `CHANGELOG.md` gets one line per release. The build stamps the git SHA as the release (`VITE_RELEASE`).

### Definition of done for a change
- [ ] `SPEC.md` screen blocks updated first, in the same pull request
- [ ] `make check` passes; `make e2e` passes when a screen changed
- [ ] Every state of each touched view implemented (§15), with a happy-path and a failure-path test
- [ ] Matches the design at the profile's widths, with screenshots of each state in the report
- [ ] axe: no serious or critical violations; keyboard pass done and reported
- [ ] No hardcoded values (`make check` token check), no `console`, no dead code
- [ ] Assumptions and deviations in the decision log
- [ ] The change was run in a browser, not just tested

### Definition of done for a release
- [ ] The above, for every change in it
- [ ] Version bumped in `package.json`; `CHANGELOG.md` updated
- [ ] Release build with source maps uploaded and removed from `dist/`; monitoring receives a test error from the deployed environment
- [ ] Deployed; deep links load; the smoke test passes against the deployment
- [ ] Security headers present on the deployment (checked with `curl -I`)
- [ ] Bundle and Lighthouse checked on the main screens
- [ ] Infrastructure changes shown to the owner and approved before apply

---

## 26. Profiles

A profile adds one project's specifics on top of this standard: the design source and token pipeline, the type scale and layout sizes, the contract location and error format, the identity provider and session endpoints, stream and polling rules, widths to check, budgets, locale and time zone, the host, environments, names, tags and domain, and any choice this standard leaves to the profile. It MUST NOT weaken sections 1–25.

Profiles live in the **project's** repository, not here. Template: [`PROFILE_TEMPLATE.md`](PROFILE_TEMPLATE.md).

Each project's README links its profile; this standard lists none.

---

## Appendix A: Spec template

The intake template is the repository's [`SPEC.md`](../SPEC.md). A coding agent fills it with the owner before any code (recipe 1). It ends with the **order of work**: spec → tokens and screen map → contract and client → shell → features in dependency order (each: models, service, mocks, components, screen, route, tests) → deploy.

## Appendix B: Profile template

[`PROFILE_TEMPLATE.md`](PROFILE_TEMPLATE.md): one table of topic and rule for this project. Anything not listed uses this standard's default.

## Appendix C: Reference code

The template's `src/` is the reference implementation, and its golden-path feature (`modules/notes`, `service/notes.ts`) uses every pattern once; the files below are copied from it (the auth snippets in C3 and C4 are what recipe 8 adds).

Checked on 2026-10-03 against React 19.3.0, Vite 8.3.2, @vitejs/plugin-react 6.1.1, React Router 8.4.0, TanStack Query 5.104.1, nuqs 2.10.1, openapi-typescript 7.13.0, openapi-fetch 0.17.0, MSW 3.0.2, Vitest 5.0.3, Testing Library React 16.3.3, user-event 14.6.7, jest-dom 7.0.1, Playwright 1.63.0, @axe-core/playwright 4.13.0, Tailwind 4.3.3, shadcn 4.21.1 (Base UI 1.8.0), React Hook Form 7.89.0, zod 4.6.5, react-markdown 10.1.0, @sentry/react 11.4.0, TypeScript 6.0 and ESLint 10.12.0. In the template they pass `make check` (strict types, lint with the layer rules, unit and component tests, build, budget, audit) and `make e2e` (Playwright with axe at desktop and mobile widths).

### C1. Vite config (§3, §11.5, §22)
```ts
// vite.config.ts
/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { msw } from 'msw/vite'
import { defineConfig } from 'vite'

// Standard §3, Appendix C1.
export default defineConfig({
  plugins: [react(), tailwindcss(), msw()],
  resolve: { tsconfigPaths: true },
  build: { sourcemap: 'hidden', manifest: true },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    env: { VITE_API_URL: 'http://localhost:4173' }, // the mocks answer on any origin; tests need an absolute URL
    include: ['src/**/*.test.{ts,tsx}', 'scripts/**/*.test.ts'],
    // MSW 3's Node interceptor trips an undici assertion when a test cancels a mocked response body
    // while a read is pending (a stream stall test does exactly that). Node's own fetch against a real
    // server doesn't. Ignore only that error; every other unhandled error still fails the run.
    onUnhandledError: (error) => !(error.message.includes('assert(!this.aborted)') && (error.stack ?? '').includes('undici')),
  },
})
```

### C2. Tokens (§8.1)
`scripts/gen-tokens.ts` reads the design's variables through an adapter (`scripts/tokens/read-design.ts`, DTCG JSON by default; it lists its `sources` and builds the token set in `readSources`) and writes `src/styles/tokens.css` and `src/lib/token-names.ts`:
```css
/* Generated by scripts/gen-tokens.ts from design/tokens.json. Do not edit: change the design and run `make tokens`. */
@theme static {
  --text-*: initial;
  --text-xs: 0.75rem;
  --text-xs--line-height: 1rem;
  --text-sm: 0.875rem;
  …
  --color-brand: #2f54d1;
  …
  --radius-*: initial;
  --radius-base: 0.625rem;
}

.dark {
  --color-brand: #7c96f2;
  …
}
```
`src/styles/theme.css` (hand-kept, `var()` only) points shadcn's variables at them:
```css
:root {
  --background: var(--color-surface);
  --primary: var(--color-brand);
  --accent: var(--color-hover);
  --radius: var(--radius-base);
  …
}
```
```ts
// src/lib/utils.ts
import { createCn } from 'cn/config'
import { fontSizes, radii, shadows } from '@/lib/token-names'

export const cn = createCn({ extend: { theme: { text: [...fontSizes], radius: [...radii], shadow: [...shadows] } } })
```

### C3. Route table, and the auth guard recipe 8 adds (§9, §14)
```ts
// src/app/router.tsx
// The one route table (standard §9). Every screen is lazy; route files only re-export a screen.
import { createBrowserRouter } from 'react-router'
import { RootError, RootLayout } from '@/modules/shell'

export const router = createBrowserRouter([
  {
    Component: RootLayout,
    ErrorBoundary: RootError,
    children: [
      { index: true, lazy: () => import('@/app/routes/notes') },
      { path: 'notes/new', lazy: () => import('@/app/routes/new-note') },
      { path: 'notes/:noteId', lazy: () => import('@/app/routes/note') },
      { path: '*', lazy: () => import('@/app/routes/not-found') },
    ],
  },
])
```
```ts
// src/app/routes/notes.tsx
export { NotesPage as Component } from '@/modules/notes'
```
```tsx
// src/modules/auth/components/require-auth.tsx
import { Navigate, Outlet, useLocation } from 'react-router'
import { useSession } from '@/modules/auth/hooks/use-session'
import { AppShellSkeleton } from '@/components/layout/app-shell-skeleton'

export function RequireAuth() {
  const { status } = useSession()
  const { pathname, search } = useLocation()
  if (status === 'restoring') return <AppShellSkeleton />
  if (status === 'signed-out') return <Navigate replace to={`/sign-in?next=${encodeURIComponent(pathname + search)}`} />
  return <Outlet />
}

// src/modules/auth/utils/safe-next.ts
export const safeNext = (next: string | null) => (next?.startsWith('/') && !next.startsWith('//') ? next : '/')
```

### C4. The client, `ApiError` and the auth middleware (§11.2, §14)
```ts
// src/service/client.ts
// The one API client (standard §11.2). `/add-auth` adds the auth middleware from standard Appendix C4.
import createClient from 'openapi-fetch'
import { apiUrl } from '@/service/config'
import type { paths } from '@/service/generated/schema'

// Look fetch up per request, so MSW and test interceptors apply whatever the import order.
const fetch = (request: Request) => globalThis.fetch(request)

export const api = createClient<paths>({ baseUrl: apiUrl, credentials: 'include', fetch })
```
```ts
// src/service/api-error.ts
// One error type for every failed call (standard §11.2). Reads RFC 9457 problem details when the body
// has them, and falls back to the HTTP status otherwise.
export class ApiError extends Error {
  override name = 'ApiError'
  readonly status: number
  readonly code: string
  readonly requestId: string | undefined
  readonly retryable: boolean
  /** Field errors keyed by field name (the last segment of the problem's JSON pointer). */
  readonly fieldErrors: Readonly<Record<string, string>>

  constructor(init: {
    status: number
    code: string
    message: string
    requestId?: string | undefined
    retryable?: boolean
    fieldErrors?: Record<string, string>
  }) {
    super(init.message)
    this.status = init.status
    this.code = init.code
    this.requestId = init.requestId
    this.retryable = init.retryable ?? init.status >= 500
    this.fieldErrors = init.fieldErrors ?? {}
  }
}

const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null

/** What toApiError needs from a response. A stream's error event passes its problem's own status. */
export interface ResponseLike {
  status: number
  statusText?: string
  headers?: Headers
}

export function toApiError(body: unknown, response: ResponseLike): ApiError {
  const p = isRecord(body) ? body : {}
  const fieldErrors: Record<string, string> = {}
  if (Array.isArray(p.errors)) {
    for (const e of p.errors) {
      if (isRecord(e) && typeof e.path === 'string' && typeof e.message === 'string') {
        fieldErrors[e.path.split('/').pop() ?? e.path] = e.message
      }
    }
  }
  return new ApiError({
    status: response.status,
    code: typeof p.code === 'string' ? p.code : `http_${String(response.status)}`,
    message: typeof p.title === 'string' ? p.title : response.statusText || 'Request failed',
    requestId: typeof p.requestId === 'string' ? p.requestId : (response.headers?.get('x-request-id') ?? undefined),
    ...(typeof p.retryable === 'boolean' ? { retryable: p.retryable } : {}),
    fieldErrors,
  })
}

/** Turns an openapi-fetch result into its data, or throws ApiError (so TanStack Query sees a failure). */
export async function unwrap<T>(call: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await call
  if (error !== undefined || !response.ok) throw toApiError(error, response)
  return data as T
}
```
With auth (recipe 8), the client gains an in-memory access token, a single-flight refresh and one retry:
```ts
// src/service/client.ts, after /add-auth (recipe 8)
import createClient, { type Middleware } from 'openapi-fetch'
import { apiUrl as baseUrl } from '@/service/config'
import type { paths } from '@/service/generated/schema'

let accessToken: string | null = null
let refreshing: Promise<string | null> | null = null
let onSessionEnded: () => void = () => undefined

export const setAccessToken = (token: string | null) => { accessToken = token }
export const onSessionEnd = (handler: () => void) => { onSessionEnded = handler } // registered by provider/

// Look fetch up per request, so MSW and test interceptors apply whatever the import order.
const fetch = (request: Request) => globalThis.fetch(request)

// The refresh call uses its own client, so it never runs through the auth middleware.
const authClient = createClient<paths>({ baseUrl, credentials: 'include', fetch })

export function refreshSession(): Promise<string | null> {
  refreshing ??= authClient
    .POST('/v1/auth/refresh')
    .then(({ data }) => (accessToken = data?.accessToken ?? null))
    .catch(() => (accessToken = null))
    .finally(() => { refreshing = null })
  return refreshing
}

const copies = new Map<string, Request>()

const auth: Middleware = {
  onRequest({ request, id }) {
    if (accessToken) request.headers.set('Authorization', `Bearer ${accessToken}`)
    copies.set(id, request.clone()) // fetch consumes the body; keep a copy for one retry
    return request
  },
  async onResponse({ response, id, options }) {
    const copy = copies.get(id)
    copies.delete(id)
    if (response.status !== 401 || !copy) return undefined
    const token = await refreshSession()
    if (!token) { onSessionEnded(); return undefined } // the caller sees the 401
    copy.headers.set('Authorization', `Bearer ${token}`)
    return options.fetch(copy) // one retry; its response replaces the 401
  },
  onError({ id }) { copies.delete(id) },
}

export const api = createClient<paths>({ baseUrl, credentials: 'include', fetch })
api.use(auth)
```

### C5. A resource, a stream and a screen with its states (§11.3, §12, §15)
```ts
// src/service/notes.ts
// The notes resource (standard §11.3): keys, reads, writes and the summary stream. The golden path:
// copy this file's shape for a new resource.
import { mutationOptions, queryOptions, type QueryClient } from '@tanstack/react-query'
import { toDomainNote, type CreateNoteRequest, type NotePage } from '@/models/note'
import { toApiError, unwrap, type ApiError } from '@/service/api-error'
import { api } from '@/service/client'
import { streamStallMs } from '@/service/config'
import { readSse } from '@/service/sse'

export const noteKeys = {
  all: ['notes'] as const,
  lists: () => [...noteKeys.all, 'list'] as const,
  list: (page: number) => [...noteKeys.lists(), { page }] as const,
  detail: (id: string) => [...noteKeys.all, 'detail', id] as const,
  summary: (id: string) => [...noteKeys.all, 'summary', id] as const,
}

export const noteListQuery = (page: number) =>
  queryOptions({
    queryKey: noteKeys.list(page),
    queryFn: async ({ signal }): Promise<NotePage> => {
      const res = await unwrap(api.GET('/v1/notes', { params: { query: { page } }, signal }))
      return { items: res.items.map(toDomainNote), nextPage: res.nextPage }
    },
    staleTime: 30_000,
  })

export const noteQuery = (id: string) =>
  queryOptions({
    queryKey: noteKeys.detail(id),
    queryFn: ({ signal }) => unwrap(api.GET('/v1/notes/{noteId}', { params: { path: { noteId: id } }, signal })).then(toDomainNote),
    staleTime: 60_000,
  })

export const createNoteMutation = (qc: QueryClient) =>
  mutationOptions({
    mutationFn: (body: CreateNoteRequest) => unwrap(api.POST('/v1/notes', { body })).then(toDomainNote),
    onSuccess: async (note) => {
      qc.setQueryData(noteKeys.detail(note.id), note)
      await qc.invalidateQueries({ queryKey: noteKeys.lists() })
    },
  })

export const deleteNoteMutation = (qc: QueryClient) =>
  mutationOptions({
    mutationFn: (id: string) => unwrap(api.DELETE('/v1/notes/{noteId}', { params: { path: { noteId: id } } })),
    onSuccess: async (_data, id) => {
      qc.removeQueries({ queryKey: noteKeys.detail(id) })
      qc.removeQueries({ queryKey: noteKeys.summary(id) })
      await qc.invalidateQueries({ queryKey: noteKeys.lists() })
    },
  })

/**
 * Streams a note's summary (standard §12). Resolves when the server sends `summary.done`; rejects with
 * ApiError (a failed request or a `summary.failed` event), StreamStalledError, or the abort reason.
 */
export async function streamNoteSummary(id: string, { signal, onDelta }: { signal: AbortSignal; onDelta: (text: string) => void }) {
  const { data: body, error, response } = await api.POST('/v1/notes/{noteId}/summary', {
    params: { path: { noteId: id } },
    headers: { Accept: 'text/event-stream' },
    parseAs: 'stream',
    signal,
  })
  if (error !== undefined || !body) throw toApiError(error, response)
  const outcome: { failure: ApiError | null } = { failure: null } // an object, so the check below sees the callback's write
  await readSse(body, {
    stallMs: streamStallMs,
    signal,
    onEvent: (e) => {
      if (e.event === 'summary.delta') onDelta((JSON.parse(e.data) as { text: string }).text)
      if (e.event === 'summary.failed') {
        const problem = JSON.parse(e.data) as { status?: number }
        outcome.failure = toApiError(problem, { status: problem.status ?? 500 })
      }
    },
  })
  if (outcome.failure) throw outcome.failure
}
```
```tsx
// src/modules/notes/notes-page.tsx
// The list screen: loading, empty, error, pagination and success (standard §15). Page lives in the URL.
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { parseAsInteger, useQueryState } from 'nuqs'
import { Link } from 'react-router'
import { buttonVariants } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Icon, Plus } from '@/components/ui/icon'
import { PageHeader } from '@/components/ui/page-header'
import { NoteList } from '@/modules/notes/components/note-list'
import { NoteListSkeleton } from '@/modules/notes/components/note-list-skeleton'
import { describeError } from '@/service/describe-error'
import { noteListQuery } from '@/service/notes'

export function NotesPage() {
  const [page, setPage] = useQueryState('page', parseAsInteger.withDefault(1))
  const notes = useQuery({ ...noteListQuery(page), placeholderData: keepPreviousData })
  const newNote = (
    <Link to="/notes/new" className={buttonVariants()}>
      <Icon icon={Plus} /> New note
    </Link>
  )

  return (
    <>
      <title>Notes · App</title>
      <PageHeader title="Notes" actions={newNote} />
      {notes.isPending ? (
        <NoteListSkeleton />
      ) : notes.isError ? (
        <EmptyState kind="error" {...describeError(notes.error)} onRetry={() => void notes.refetch()} />
      ) : notes.data.items.length === 0 ? (
        <EmptyState kind="empty" title="No notes yet" description="Notes you write appear here." action={newNote} />
      ) : (
        <NoteList notes={notes.data.items} page={page} hasNext={notes.data.nextPage !== null} isFetching={notes.isPlaceholderData}
          onPage={(p) => void setPage(p)} />
      )}
    </>
  )
}
```

### C6. The SSE reader (§12)
```ts
// src/service/sse.ts
// Server-Sent Events over fetch (standard §12, Appendix C6). EventSource can't send a body or an
// Authorization header, so streams are read here.
export interface SseEvent {
  id: string | undefined // the last id seen; it carries over to later events
  event: string          // "message" when the server sent no event field
  data: string           // data lines joined with "\n"
}

/** Incremental text/event-stream parser. Feed it decoded text split anywhere. */
export function createSseParser(onEvent: (event: SseEvent) => void) {
  let buffer = ''
  let data: string[] = []
  let type = ''
  let lastId: string | undefined

  function dispatch() {
    if (data.length > 0) onEvent({ id: lastId, event: type || 'message', data: data.join('\n') })
    data = []
    type = ''
  }

  function line(text: string) {
    if (text === '') {
      dispatch()
      return
    }
    if (text.startsWith(':')) return // a comment, e.g. a keep-alive ping
    const colon = text.indexOf(':')
    const field = colon === -1 ? text : text.slice(0, colon)
    let value = colon === -1 ? '' : text.slice(colon + 1)
    if (value.startsWith(' ')) value = value.slice(1)
    if (field === 'event') type = value
    else if (field === 'data') data.push(value)
    else if (field === 'id' && !value.includes('\0')) lastId = value
    // `retry` and unknown fields are ignored.
  }

  return {
    feed(chunk: string) {
      buffer += chunk
      let start = 0
      for (let i = 0; i < buffer.length; i++) {
        const c = buffer[i]
        if (c !== '\n' && c !== '\r') continue
        if (c === '\r' && i === buffer.length - 1) break // may be the first half of "\r\n"
        line(buffer.slice(start, i))
        if (c === '\r' && buffer[i + 1] === '\n') i++
        start = i + 1
      }
      buffer = buffer.slice(start)
    },
  }
}

export class StreamStalledError extends Error {
  override name = 'StreamStalledError'
}

/** Reads an SSE body to its end. Rejects with StreamStalledError after `stallMs` without bytes,
 *  or with the signal's reason when aborted. */
export async function readSse(body: ReadableStream<Uint8Array>,
  { stallMs, signal, onEvent }: { stallMs: number; signal?: AbortSignal | undefined; onEvent: (e: SseEvent) => void }) {
  signal?.throwIfAborted()
  const reader = body.getReader()
  const decoder = new TextDecoder()
  const parser = createSseParser(onEvent)
  const stall = { hit: false } // an object, so the read loop sees the timer's write
  let timer: ReturnType<typeof setTimeout> | undefined
  const arm = () => {
    clearTimeout(timer)
    timer = setTimeout(() => { stall.hit = true; cancel() }, stallMs)
  }
  // cancel() rejects if the body already errored; the read loop reports what happened, so ignore it.
  const cancel = () => { reader.cancel().catch(() => undefined) }
  const abort = cancel
  signal?.addEventListener('abort', abort, { once: true })
  try {
    arm()
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      arm()
      parser.feed(decoder.decode(value, { stream: true }))
    }
    if (stall.hit) throw new StreamStalledError(`No data for ${String(stallMs)} ms`)
    signal?.throwIfAborted()
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', abort)
  }
}
```

### C7. Mocks and boot (§11.5)
```ts
// src/mocks/responses.ts
// Response helpers every handler uses (standard §11.5): problem details on errors, and SSE streams.
import { HttpResponse } from 'msw/http'
import { delay } from 'msw/utils/delay'
import type { Problem } from '@/service/generated/schema'

export const problem = (status: number, code: Problem['code'], title: string, extra: Partial<Problem> = {}) =>
  HttpResponse.json<Problem>({ type: 'about:blank', status, code, title, requestId: `req_${code}`, retryable: status >= 500, ...extra },
    { status, headers: { 'content-type': 'application/problem+json' } })

const enc = new TextEncoder()
export const sse = (frames: string[], gapMs = 60) =>
  new HttpResponse(
    new ReadableStream<Uint8Array>({
      async start(c) {
        for (const frame of frames) {
          await delay(gapMs)
          c.enqueue(enc.encode(frame))
        }
        c.close()
      },
    }),
    { headers: { 'content-type': 'text/event-stream', 'cache-control': 'no-cache' } },
  )
export const event = (id: number, type: string, data: unknown) => `id: ${String(id)}\nevent: ${type}\ndata: ${JSON.stringify(data)}\n\n`
```
```ts
// src/mocks/handlers/notes.ts (excerpt)
import { http, HttpResponse } from 'msw/http'
import { seedNotes } from '@/mocks/data/notes'
import { event, problem, sse } from '@/mocks/responses'
import type { Note, NoteInput, NotePage } from '@/service/generated/schema'

let notes = seedNotes()
export const resetNotes = (next: Note[] = seedNotes()) => { notes = next }

export const noteHandlers = [
  http.get('*/v1/notes/:noteId', ({ params }) => {
    const note = notes.find((n) => n.id === params.noteId)
    return note ? HttpResponse.json(note) : problem(404, 'not_found', 'Note not found')
  }),
  …
]
```
```ts
// src/mocks/handlers/index.ts
import type { RequestHandler } from 'msw'
import { noteHandlers } from '@/mocks/handlers/notes'

export const handlers: RequestHandler[] = [...noteHandlers]
```
```tsx
// src/main.tsx
// Boot (standard §6): monitoring, mocks when enabled, providers, router. The only wiring.
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router/dom'
import { router } from '@/app/router'
import { initMonitoring, reactErrorHandlers } from '@/lib/monitoring'
import { AppProviders } from '@/provider/app-providers'
import '@/styles/globals.css'

void initMonitoring()

if (import.meta.env.VITE_API_MOCKS === 'true') {
  const { network } = await import('virtual:msw')
  const { handlersFor } = await import('@/mocks/scenarios')
  network.configure({ handlers: handlersFor(new URLSearchParams(location.search).get('scenario')), onUnhandledFrame: 'bypass' })
  await network.enable()
}

const root = document.getElementById('root')
if (!root) throw new Error('index.html has no #root element')

createRoot(root, reactErrorHandlers).render(
  <AppProviders>
    <RouterProvider router={router} />
  </AppProviders>,
)
```

### C8. A form (§13)
```ts
// src/modules/notes/schemas.ts
import { z } from 'zod'

// Matches NoteInput in the contract (standard §13): the contract wins if they differ.
export const noteFormSchema = z.object({
  title: z.string().trim().min(1, 'Give the note a title').max(120, 'Keep the title under 120 characters'),
  body: z.string().max(10_000, 'Keep the note under 10,000 characters'),
})

export type NoteFormValues = z.input<typeof noteFormSchema>
```
```tsx
// src/modules/notes/components/note-form.tsx
// A form (standard §13): zod schema, field kit, pending state, server field errors mapped onto fields.
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { TextareaField } from '@/components/form/textarea-field'
import { TextField } from '@/components/form/text-field'
import { Button } from '@/components/ui/button'
import { FieldGroup } from '@/components/ui/field'
import { noteFormSchema } from '@/modules/notes/schemas'
import { ApiError } from '@/service/api-error'
import { describeError } from '@/service/describe-error'
import { createNoteMutation } from '@/service/notes'

export function NoteForm() {
  const navigate = useNavigate()
  const form = useForm({ resolver: zodResolver(noteFormSchema), defaultValues: { title: '', body: '' } })
  const create = useMutation(createNoteMutation(useQueryClient()))

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const note = await create.mutateAsync(values)
      await navigate(`/notes/${note.id}`)
    } catch (e) {
      const fields = e instanceof ApiError ? Object.entries(e.fieldErrors).filter(([name]) => name in values) : []
      fields.forEach(([name, message], i) => {
        form.setError(name as keyof typeof values, { type: 'server', message }, { shouldFocus: i === 0 })
      })
      if (fields.length === 0) toast.error(describeError(e).message)
    }
  })

  return (
    <form noValidate onSubmit={(e) => void onSubmit(e)} className="space-y-6">
      <FieldGroup>
        <TextField control={form.control} name="title" label="Title" required autoComplete="off" />
        <TextareaField control={form.control} name="body" label="Note" hint="Markdown is supported." rows={10} />
      </FieldGroup>
      <Button type="submit" disabled={create.isPending} aria-busy={create.isPending}>
        {create.isPending ? 'Saving…' : 'Save note'}
      </Button>
    </form>
  )
}
```

### C9. Markdown from untrusted sources (§19)
```tsx
// src/components/ui/safe-markdown.tsx
// Markdown from users, APIs or models (standard §19): no raw HTML, react-markdown's URL filter, safe links.
import Markdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

const components: Components = {
  a: ({ node: _node, href, children, ...rest }) => (
    <a {...rest} href={href} target="_blank" rel="noopener noreferrer nofollow" className="text-primary underline underline-offset-4">
      {children}
    </a>
  ),
}

export function SafeMarkdown({ children }: { children: string }) {
  return (
    <div className="space-y-3 text-base leading-relaxed [&_ol]:list-decimal [&_ol]:pl-6 [&_ul]:list-disc [&_ul]:pl-6">
      <Markdown remarkPlugins={[remarkGfm]} components={components} skipHtml>
        {children}
      </Markdown>
    </div>
  )
}
```

### C10. Tests: setup, render helper, axe (§22)
```ts
// src/test/setup.ts
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'
import { resetNotes } from '@/mocks/handlers/notes'
import { server } from '@/mocks/node'

// Testing Library only detects fake timers through a global `jest`; this lets it advance Vitest's.
Object.assign(globalThis, { jest: { advanceTimersByTime: (ms: number) => vi.advanceTimersByTime(ms) } })

beforeAll(() => { server.listen({ onUnhandledFrame: 'error' }) })
afterEach(() => {
  server.resetHandlers()
  resetNotes()
  cleanup()
  vi.useRealTimers()
})
afterAll(() => { server.close() })
```
```tsx
// src/test/render-route.tsx
// Renders a screen as the app does: a fresh query client (no retries), the URL-state adapter and a
// memory router (standard §22).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NuqsAdapter } from 'nuqs/adapters/react-router/v8'
import type { ReactElement } from 'react'
import { createMemoryRouter, type RouteObject } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { Toaster } from '@/components/ui/sonner'

interface Options {
  path?: string
  url?: string
  /** Other routes the screen navigates to, e.g. `{ path: '/', element: <p>List</p> }`. */
  routes?: RouteObject[]
  user?: Parameters<typeof userEvent.setup>[0]
}

export function renderRoute(element: ReactElement, { path = '/', url, routes = [], user }: Options = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  const router = createMemoryRouter([{ path, element: <NuqsAdapter>{element}</NuqsAdapter> }, ...routes], { initialEntries: [url ?? path] })
  return {
    user: userEvent.setup(user),
    router,
    queryClient,
    ...render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster />
      </QueryClientProvider>,
    ),
  }
}
```
```ts
// e2e/axe.ts
import { AxeBuilder } from '@axe-core/playwright'
import { expect, type Page } from '@playwright/test'

/** WCAG 2.2 AA through axe: no serious or critical violations (standard §16). */
export async function expectAccessible(page: Page) {
  // Let open/close animations finish, or contrast is measured on half-faded text.
  await page.evaluate(() => Promise.all(document.getAnimations().map((a) => a.finished.catch(() => undefined))))
  const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
  const blocking = violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
  expect(blocking.map((v) => ({ id: v.id, help: v.help, targets: v.nodes.map((n) => n.target.join(' ')) }))).toEqual([])
}
```

### C11. Monitoring (§21)
```ts
// src/lib/monitoring.ts
// Error reporting (standard §21, Appendix C11). Sentry loads only when VITE_SENTRY_DSN is set, so it
// costs nothing when off. Its browser tracing also records LCP, INP and CLS from real users (§18).
import type * as SentryModule from '@sentry/react'

type Sentry = typeof SentryModule
type Context = Record<string, string | number | undefined>

const dsn = import.meta.env.VITE_SENTRY_DSN
let sentry: Sentry | null = null
const early: [unknown, Context][] = [] // reported before Sentry finished loading

export async function initMonitoring() {
  if (!dsn) return
  const S = await import('@sentry/react')
  S.init({
    dsn,
    environment: import.meta.env.VITE_ENVIRONMENT,
    release: import.meta.env.VITE_RELEASE,
    integrations: [S.browserTracingIntegration()],
    tracesSampleRate: 0.1,
    // Sentry 11 collects everything unless told otherwise.
    dataCollection: {
      userInfo: false,
      cookies: false,
      httpBodies: [],
      urlQueryParams: false,
      httpHeaders: { request: { deny: ['authorization', 'cookie'] }, response: { deny: ['set-cookie'] } },
    },
    beforeSend(event) {
      if (event.user) event.user = event.user.id === undefined ? {} : { id: event.user.id } // keep only the id
      return event
    },
  })
  sentry = S
  early.splice(0).forEach(([error, context]) => { S.captureException(error, { extra: context }) })
}

/** The only way code reports an error (standard §21). */
export function reportError(error: unknown, context: Context = {}) {
  if (!dsn) return
  if (sentry) sentry.captureException(error, { extra: context })
  else if (early.length < 20) early.push([error, context])
}

/** React 19's root error hooks: errors no boundary handled, and errors a boundary caught. */
export const reactErrorHandlers = {
  onUncaughtError: (error: unknown, info: { componentStack?: string | undefined }) => { reportError(error, { componentStack: info.componentStack }) },
  onCaughtError: (error: unknown, info: { componentStack?: string | undefined }) => { reportError(error, { componentStack: info.componentStack }) },
}
```

## Appendix D: The Next.js exception

Use Next.js (App Router) only when the spec has pages that must be indexed or previewed by link unfurlers, or that need server rendering for a measured reason. Everything in §1–25 still applies, with these changes:

- **Routing.** `app/` holds the routes, in route groups `(public)`, `(auth)` and `(app)`; each group has `error.tsx`, plus `global-error.tsx`, `not-found.tsx` and `loading.tsx`. Route files stay thin (§7). Protection: middleware (or `proxy.ts`, per the installed version) checks only that the session cookie is present and redirects with `next`; the `(app)` layout also verifies the session on the server.
- **Server and client data.** For every screen, the spec records where its data is fetched (server-prefetched, client-only, static or revalidated), how fresh it must be and what invalidates it. Signed-in pages fetch on the client by default; prefetch on the server only for a post-sign-in landing page, LCP-critical data, or a measured waterfall, then `dehydrate` into TanStack Query and hydrate with `HydrationBoundary`, with `staleTime` above 0. Set caching explicitly on every server fetch; never put per-user responses in a shared cache. Modules using server-only credentials import `server-only`.
- **Components.** Server components by default; `"use client"` only on the smallest interactive leaf. `next/image` for content images and `next/font` for fonts. `next/dynamic` for heavy client pieces.
- **Public pages.** Each exports `metadata` or `generateMetadata` (unique title from a template, description, canonical, Open Graph and Twitter tags, image), with `metadataBase` from env; `sitemap.ts` and `robots.ts`; JSON-LD where relevant. `(auth)` and `(app)` set `robots: { index: false }`. Lighthouse CI asserts LCP, CLS and Total Blocking Time on public pages.
- **Security and monitoring.** Headers (including a nonce-based CSP) in `next.config` or middleware; `@sentry/nextjs`; `NEXT_PUBLIC_*` replaces `VITE_*`.
- **Mutations** that change content shown on public pages revalidate the affected tags or paths.

## Appendix E: Opt-in modules

Added by a recipe when the spec needs them, never by default.

| Module | Use when | What it adds |
|---|---|---|
| Dark mode | The design has dark values | Dark token values from the generator, a theme toggle storing the choice in `localStorage` (a convenience), `@custom-variant dark` |
| Idle timeout | The profile sets one | The warning dialog and timer in `modules/auth` (§14) |
| Internationalisation | More than one language | One message catalogue per locale; `Intl` formatting by locale |
| Push updates | Polling is too slow or too costly | An authenticated stream (§12) that invalidates queries |
| Offline / PWA | The app must work without a connection | A service worker for the shell; queued mutations |
| Payments | Anything takes money | The provider's hosted fields only; ask first |
