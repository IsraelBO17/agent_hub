# Recipes

Step-by-step playbooks for the common tasks, written so a coding agent can follow them literally (standard §6.1). Each ends with **Verify**: nothing is done until `make check` passes, and `make e2e` too when a screen changed. When a recipe is missing or wrong, fix it in the `web-standard` template (with a version bump) rather than working around it.

The golden path is the template's `notes` feature. When a recipe says "copy the shape of", open that file. Once a project has removed `notes` (recipe 1, step 9), copy from the `web-standard` repository instead.

| Recipe | Skill | Use when |
|---|---|---|
| [1. Start a new web app](#1-start-a-new-web-app) | `/new-web-app` | The repository is fresh from the template |
| [2. Sync design tokens](#2-sync-design-tokens) | `/sync-tokens` | The design's variables changed, or first setup |
| [3. Add a page](#3-add-a-page) | `/add-page` | A new screen and route |
| [4. Add a component](#4-add-a-component) | `/add-component` | A primitive or composite the design needs |
| [5. Add an API call](#5-add-an-api-call) | `/add-api-call` | A screen needs an endpoint |
| [6. Add a stream](#6-add-a-stream) | `/add-stream` | A reply arrives over time (SSE) |
| [7. Add a form](#7-add-a-form) | `/add-form` | Users enter data |
| [8. Add auth](#8-add-auth) | `/add-auth` | Users sign in |
| [9. Deploy](#9-deploy) | `/deploy` | First deploy, or a release |
| [10. Pre-merge check](#10-pre-merge-check) | `/pre-merge` | Before asking for a merge |

## 1. Start a new web app

1. **Read** `CLAUDE.md`, this file and `docs/STANDARD.md` §1–8, and the project profile if one exists.
2. **Ask the owner** (one batch, each question with your recommendation): the app's job and users; devices; the screens and routes; the design source and how its variables are exported; the API contract (where, or mock-first); the auth model; locale and time zone; the host and environments. Use the standard's defaults for everything else, and list each default you chose.
3. **Write `SPEC.md`**: sections 1–9 from the answers, a screen block per screen (copy the shape of the `notes` blocks). **Stop and get the owner's approval before any code.**
4. **Rename:** `name` in `package.json` (and `npm install` to update the lock file), the `<title>` in `index.html`, the brand in `modules/shell/root-layout.tsx`, the `· App` suffix in each screen's `<title>`. Fill in the headers of `README.md` and `CLAUDE.md` and delete the README's template block.
5. **Profile:** if the project has no profile, create `docs/PROFILE.md` from `docs/PROFILE_TEMPLATE.md` with the owner's answers; link it from `README.md` and `CLAUDE.md`.
6. **Design:** recipe 2 (tokens). Map each screen in `SPEC.md` to its design frame.
7. **Contract:** put the contract at `contract/openapi.yaml` (or point `make api` and `make api-check` at it, per the profile) and run `make api`. Mock-first: write the contract for the first screens with the owner. **Stop and get the owner's approval of the design map and the contract.**
8. **Build the first screen** with recipes 5 and 3, while `notes` is still there to copy from. Set the navigation in `modules/shell/nav.ts` and the index route in `app/router.tsx`.
9. **Remove the golden path:** delete `src/modules/notes/`, `src/service/notes.ts`, `src/models/note.ts` and `note.test.ts`, `src/mocks/data/notes.ts`, `src/mocks/handlers/notes.ts`, the `notes` routes in `src/app/routes/` and `app/router.tsx`, the notes scenarios in `src/mocks/scenarios/index.ts`, `e2e/notes.spec.ts`, the notes routes in `e2e/smoke.spec.ts`, the notes paths in the example contract, and the example screen blocks in `SPEC.md`. Point `src/mocks/node.ts` and the scenarios at your handlers. Replace `design/tokens.json` if it is still the example.
10. **Record** the start in `CHANGELOG.md` (`- 0.1.0: from the web-standard template (standard <version>).`) and any judgment calls in `docs/decisions.md`.

**Verify:** `make check` and `make e2e`; `git grep -n -i -e web-name -e notes -e "· App" -- src e2e index.html` finds nothing unexpected; `make dev` shows your first screen.

## 2. Sync design tokens

1. **Export** the design tool's variables (colours with their dark values, font families, the type scale with line heights, radii, layout sizes) to `design/tokens.json`, or read them straight from the design file if the profile says so.
2. **Adapter:** the template reads W3C Design Tokens (DTCG) JSON in `scripts/tokens/read-design.ts`. For another format, rewrite only that file so it returns the same `TokenSet` (`scripts/tokens/token-set.ts`), and add a test beside `tokens.test.ts`.
3. **Generate:** `make tokens` writes `src/styles/tokens.css`. Never edit it by hand.
4. **Map shadcn:** in `src/styles/theme.css`, point each shadcn variable at a design token (`var()` only). When a design token and a shadcn variable share a name but not a meaning, the design wins: point the shadcn variable at the right token and record the clash in the profile.
5. **Check the type scale** matches the design's sizes only (the generator removes Tailwind's defaults). Layout sizes become `--layout-*` and are used as `w-(--layout-sidebar-width)` and similar.

**Verify:** `make check` (it fails if `tokens.css` is stale or a component has a hand-written value); `make dev` and compare a screen with the design at each width.

## 3. Add a page

1. **Screen block first:** add or update it in `SPEC.md` (route, design frame, data, actions, states, permissions).
2. **Data:** for each endpoint, recipe 5.
3. **Screen:** `src/modules/<feature>/<name>-page.tsx`, copying the shape of `notes-page.tsx`: a `<title>`, one `PageHeader` (the page's `h1`), and every state: a skeleton with the layout's shape (its own file in `components/`), `EmptyState` for empty, error (`{...describeError(error)}` plus `onRetry`) and not-found, and success. URL state (page, filters, tab) through `useQueryState`.
4. **Export** the screen from the module's `index.ts`.
5. **Route:** `src/app/routes/<name>.tsx` containing only `export { <Name>Page as Component } from '@/modules/<feature>'`, and a lazy entry in `app/router.tsx`. Signed-in routes go under the `RequireAuth` layout route (recipe 8).
6. **Navigation:** add it to `modules/shell/nav.ts` if it belongs in the sidebar.
7. **Tests:** `<name>-page.test.tsx` beside it, rendered with `renderRoute`: the happy path and the most important failure (copy `notes-page.test.tsx`). Add the route to `e2e/smoke.spec.ts`, and a flow in `e2e/<feature>.spec.ts` if the screen has one.
8. **Look at it:** `make dev`, then each state at each width the profile sets (use `?scenario=` for empty, error and slow). Tab through it. Save screenshots to `artifacts/` and log any deviation from the design in `docs/decisions.md`.

**Verify:** `make check` and `make e2e`; screenshots of each state at each width in your report; keyboard pass reported.

## 4. Add a component

1. **Look first:** is there a shadcn primitive for it? `npx shadcn@latest add <name>`, never written from memory. Add each file it creates to `vendored` in `eslint.config.js` and to `skip` in `scripts/check-tokens.ts`. If it imports `next-themes`, replace that as `components/ui/sonner.tsx` does.
2. **Customise** a primitive only through tokens, its `cva` variants and `className`. Note any change at the top of the file (`// Customised: …`).
3. **Composite:** a reusable app piece goes in `components/ui/<name>.tsx` (domain-free) or the feature's `components/` (knows the domain), built from primitives, reading tokens, one component per file. Start in the feature; promote it only when a second feature needs it and it knows no domain.
4. **Design link:** the file starts with `// Design: <component name> (<node id>)` when it maps to a design component.
5. **States:** disabled, focus-visible, hover, pressed, invalid and loading as the design (or the primitive) defines; 44 px touch targets on coarse pointers.
6. **Icons** through `components/ui/icon.tsx`; add the glyph to its re-export list.
7. **Test** components with logic (gating, dialogs, keyboard behaviour) with Testing Library, querying by role and label.

**Verify:** `make check`; the component in a screen at each width, by keyboard; axe clean in `make e2e`.

## 5. Add an API call

1. **Contract:** the operation exists in the contract (request, response, error codes). If it doesn't, stop: agree it with the owner (and the API team), update the contract, then `make api`. Never invent a field.
2. **Model:** in `src/models/<noun>.ts`, the domain type and `toDomain<Noun>` (dates become `Date`, names become what the UI needs). Add a mapper test.
3. **Service:** in `src/service/<resource>.ts`, copying the shape of `service/notes.ts`: keys in the resource's key factory; a `queryOptions` per read (with `signal`, `unwrap`, the mapper and a `staleTime`); a `mutationOptions` per write that invalidates exactly the keys it changes, or sets the returned record with `setQueryData`.
4. **Error copy:** add a line to `byCode` in `service/describe-error.ts` for each error code the screen must explain.
5. **Mocks:** a handler per operation in `src/mocks/handlers/<resource>.ts` returning synthetic data from `src/mocks/data/`, problem details for errors (the `problem()` helper), and the field errors the API returns. Add it to `mocks/node.ts` and `mocks/scenarios/index.ts`; add a scenario for each state worth demoing (`empty`, `error`, `slow`).
6. **Use it** from a screen or hook with `useQuery(…Query(args))` / `useMutation(…Mutation(qc))`. Never `fetch` in a component.
7. **Test** the mapper, and the screen's success and failure through MSW (`server.use(...)` for the failure).

**Verify:** `make check` (the contract drift check passes); the screen works in `make dev` with mocks, and with `?scenario=error`.

## 6. Add a stream

1. **Contract:** the operation's events, their payloads, the keep-alive interval, and what ends the stream (done, failed). The profile sets the stall time and what happens after a stall.
2. **Service:** a `stream<Thing>()` function in the resource's service file, copying `streamNoteSummary`: `api.POST(…, { parseAs: 'stream', signal, headers: { Accept: 'text/event-stream' } })`, `toApiError` when the request fails, then `readSse(body, { stallMs, signal, onEvent })`. Parse each event's `data` with its schema type; turn a failure event into `ApiError`.
3. **Cache:** a key for the streamed record and its state type in `models/` (`idle`, `streaming`, `done`, `stalled`, `failed`).
4. **Hook:** `modules/<feature>/hooks/use-<thing>.ts`, copying `use-note-summary.ts`: an `AbortController` per run, aborted on unmount and on restart; events into the cache through `batchPerFrame`; a final state for done, stalled and failed; `reportError` for stalls. If the record lives on the server, invalidate it when the stream ends.
5. **UI:** a `role="status"` region with `aria-live="polite"` for the streamed content, a minimum height so nothing jumps, Stop while streaming, and the stalled and failed messages from `describeError`. Auto-scroll only when the user is at the bottom.
6. **Mocks:** a handler that streams events with gaps (the `sse()` and `event()` helpers), and scenarios for a failure event and a stall.
7. **Tests:** the stream renders; a stall shows its message (fake `setTimeout` only, before the stream starts: copy the stall test in `note-page.test.tsx`); an e2e for the stall with `page.clock`.

**Verify:** `make check` and `make e2e`; in `make dev`, the stream with `?scenario=` for the stall and the failure.

## 7. Add a form

1. **Schema:** in the module's `schemas.ts` (zod), matching the contract's request schema and limits. Use `z.input` / `z.output` when coercion or transforms make them differ.
2. **Form:** a component in the feature's `components/`, copying `note-form.tsx`: `useForm({ resolver: zodResolver(schema), defaultValues })`, fields from `components/form/` (add a field type there, on the `FormField` shell, if one is missing), `noValidate` on the form, the submit button disabled while pending.
3. **Submit:** call the mutation with `mutateAsync`; map `ApiError.fieldErrors` onto fields with `setError(name, { type: 'server', message }, { shouldFocus })`; put anything else in a toast or a form-level error.
4. **Inputs:** correct `type`, `autoComplete` and `inputMode`; a visible label on every field; hints for format rules.
5. **Tests:** blocked submit with focus on the first invalid field; a server field error on its field; success (copy `note-form.test.tsx`).

**Verify:** `make check` and `make e2e`; submit by keyboard only.

## 8. Add auth

1. **Ask first:** the identity provider, the session endpoints, where the refresh token lives (an `HttpOnly` cookie set by the API is the default), roles, and any idle timeout. Record them in the profile. If app and API are on different origins, confirm cookie domain, `SameSite`, CORS credentials and CSRF with the backend.
2. **Contract:** the session endpoints (sign-in, refresh, sign-out, current user) in the contract; `make api`.
3. **Client:** add the auth middleware to `service/client.ts` from standard Appendix C4: the in-memory access token, single-flight `refreshSession()`, one retry after a refresh, and `onSessionEnd` for a failed refresh.
4. **Module:** `src/modules/auth/` with `useSession` (a query on the current user; status `restoring`, `signed-in`, `signed-out`), `RequireAuth` (Appendix C3), the sign-in screen (with `safeNext`), `usePermission` and `<Can>`, and sign-out (API call, `queryClient.clear()`, stores and per-user storage cleared, a `BroadcastChannel` message so other tabs follow). Export them from `index.ts`.
5. **Wire it:** in `provider/`, a session provider that calls `refreshSession()` once on load and registers `onSessionEnd`; in `app/router.tsx`, the signed-in routes under a `RequireAuth` layout route and a public `sign-in` route.
6. **Idle timeout** (if set): the warning dialog a minute before, then sign-out; reset on real activity.
7. **Mocks and tests:** handlers for the session endpoints and a `signed-out` scenario; tests for the redirect with `next`, the refresh retry (two concurrent 401s, one refresh), a failed refresh, and sign-out in another tab.

**Verify:** `make check` and `make e2e`; in `make dev`, a deep link while signed out returns to it after sign-in.

## 9. Deploy

1. **Plan:** the host, environment, `VITE_*` values, domain and security headers from the profile. Any infrastructure change (in the project's infrastructure as code) is planned and **shown to the owner; apply only on a yes**.
2. **Host settings:** build `npm ci && npm run build`, publish `dist/`; rewrite every path that isn't a file to `/index.html` with status 200; `Cache-Control: public, max-age=31536000, immutable` on `/assets/*` and `no-cache` on `/index.html`; the security headers in standard §19 (the CSP's `connect-src` lists the API origins).
3. **Build config:** `VITE_API_MOCKS` unset or `false`; `VITE_RELEASE` set to the git SHA; `VITE_SENTRY_DSN` and `VITE_ENVIRONMENT` per environment. With Sentry, upload source maps with `@sentry/vite-plugin` (token from the CI secret store, never committed) and delete them from `dist/` after upload.
4. **Release:** bump `version` in `package.json`, add the `CHANGELOG.md` line.
5. **Check the deployment:** the app loads; deep links load (`curl -I https://<host>/<deep/route>` returns 200 with `text/html`); the headers are present (`curl -I`); the smoke test passes against it (`PLAYWRIGHT_BASE_URL=https://<host> npx playwright test e2e/smoke.spec.ts`, once the smoke spec can run against a real API); a test error reaches the error reporter.

**Verify:** the standard's definition of done for a release (§25) is all ticked.

## 10. Pre-merge check

Go through each item and report PASS, FAIL (with file and line) or N/A:

1. `SPEC.md` screen blocks match what was built.
2. `make check` passes; `make e2e` passes if a screen changed.
3. Every touched view has its loading, empty, error, permission-gated and success states, and a happy-path and a failure-path test.
4. No server data copied into state or a store; no `fetch` in components; queries set `staleTime`; mutations invalidate precisely.
5. No hand-written design values; icons through the wrapper; shadcn primitives unmodified except through variants and tokens (customisations noted at the top of the file).
6. Accessibility: labels, focus after navigation and failed submits, dialogs, keyboard pass, axe clean.
7. Security: nothing secret in `VITE_*`, no tokens in storage, untrusted Markdown through `SafeMarkdown`, no `dangerouslySetInnerHTML` without DOMPurify and a comment.
8. Decisions and deviations logged in `docs/decisions.md`; `CHANGELOG.md` updated for a release.
9. Screenshots of each changed state at each width in the report.

**Verify:** the report ends with "ready to merge", or lists the blocking items.
