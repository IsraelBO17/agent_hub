I want a personal **Web (frontend) standard**, the same way I have one for agents, and then I want Agent Hub's web app built to it. Two phases, in order. Stop for my approval at every step marked ⏸.

# Purpose: why this standard exists
The standard is how I build **any** frontend project, Agent Hub or something entirely different, **quickly and consistently with AI coding agents like Claude Code**. When someone asks me for a web application, I start a repo from the template, and a coding agent builds it by following the standard, with me approving decisions. So the standard's main reader is a coding agent. It MUST give the agent:
- **Rules it can't miss:** a `CLAUDE.md` in the template (so every generated repo carries its conventions, commands and "never do" list), pointing to `docs/STANDARD.md`.
- **Recipes, not just rules:** step-by-step playbooks in `docs/RECIPES.md` for the common tasks (start a new app from a spec and a design, generate tokens from the design tool, add a page with its states, add a component, add an API call with its types and mocks, add auth, add a form, deploy), each ending with how to verify it.
- **Defaults for every decision,** so the agent asks only what's genuinely specific to the project.
- **An intake spec** (`SPEC.md` template, like the agent standard's): what to capture with me before any code, and the order of work from spec to deployed.
- **A golden path:** one fully working example feature in the template that shows every pattern once, for the agent to copy.
- **One self-check command** (`make check`: lint, types, tests, contract checks) the agent runs before saying it's done.
- **Claude Code skills** for the recipes (e.g. `/new-web-app`, `/add-page`, `/add-component`, `/add-api-call`), in the template's `.claude/skills/`, so they're one command away in every generated repo.
Keep `STANDARD.md` short and unambiguous (rules and defaults), put the how-to in the recipes, and write both so a coding agent can follow them literally.

# Context you must know
- I already have an **Agent Development Standard**: `../agent-standard` (a GitHub template repo, `IsraelBO17/agent-standard`). Read `../agent-standard/docs/STANDARD.md` and `README.md` first. The web standard must follow the **same shape**: a project-neutral `docs/STANDARD.md` with MUST/SHOULD/MAY, numbered sections, a default stack with documented exceptions, a lifecycle and Definition of Done, profiles kept in each project's repo, appendices with templates and reference code; plus a **template repository** whose skeleton actually runs (lint, type-check and tests green, CI) and a README block explaining how to start a new repo from it.
- The project it will first be used for: **Agent Hub** (this repo, `agent_hub`). A signed-in single-page app: one chat interface for many agents, streaming replies over SSE, rich message blocks, desktop and mobile web. Decisions: `docs/ARCHITECTURE.md` (especially D13 Amplify, D16 Vite SPA with React Router and TanStack Query and one API client module, D22 polling, D23, D24 `web/` with npm, D25 domain). Contract: `api/openapi.yaml`. Product and screens: `docs/PRODUCT_PLAN.md` §5 and §9, `design/README.md`, `design/INDEX.md`, the design file `design/fleet_dev.pen` (Pencil; plain JSON), `docs/CHART_SPEC.md`. Design rules and Pencil quirks: `CLAUDE.md`. Build order and issues: `docs/DELIVERY_PLAN.md`, GitHub issue IsraelBO17/agent_hub#4.

# REFERENCE REPOS (my existing web apps, to learn from)
<!-- Fill in: path or GitHub URL, and what it's a good (or bad) example of. -->
- …
- …
If this list is empty or unclear, ask me before anything else.

# Phase 1: Determine the web standard

**Keep the standard project-neutral.** Agent Hub is the *first project* the standard will be used on and a useful test case, not the source of its rules. The standard and its template MUST NOT contain Agent Hub specifics: no AWS account or profile, domain, resource names, tag keys or values, issue numbers, or decision numbers. Where the standard needs such a value, it says "set by the project profile" (as `agent-standard` §18 does), and the Agent Hub values go only into the profile in step 7. Generic practices that Agent Hub also uses (IaC, required tags, a naming convention, a secrets manager) belong in the standard as rules without the values.
1. **Study the references.** Read each reference repo and extract how it handles: project layout (feature-based or type-based); design tokens and styling (CSS variables, CSS Modules, Tailwind, a component library); the design-to-code workflow; components and their states (loading, empty, error, disabled); routing; state management; data fetching, caching and the typed API client (OpenAPI codegen); streaming (SSE over fetch); forms and validation; auth handling (tokens in memory, refresh); accessibility (WCAG 2.2 AA, keyboard, axe); responsive and mobile; performance budgets (Core Web Vitals, bundle size, streaming without layout shift); security (XSS, sanitised Markdown, CSP, sandboxed iframes); error reporting and analytics; testing (Vitest, Testing Library, MSW, Playwright, visual checks); build, deployment and preview environments; CI; release; documentation. Report a short table per topic: what each repo does, what's worth keeping, what to drop, and where they conflict. Also say where Agent Hub's decisions already settle a topic. ⏸
2. **Ask me the open decisions in one batch,** each with 2–3 options and your recommendation. At least: the default stack (I expect React, TypeScript strict, Vite, React Router, TanStack Query, npm; confirm or challenge it from the references), the styling approach, the component strategy (own components from the design system, or a headless library), the mocking approach (the AgentApi mock and scenario player from PRODUCT_PLAN F14), and E2E and visual testing. ⏸
3. **Write `docs/STANDARD.md`** in a new sibling repo `../web-standard` (v1.0, owner Boluwatife Israel). Principles, default stack, lifecycle and gates, layout, the topics above as numbered sections, Definition of Done (including accessibility and performance checks), profiles section, appendices (templates and reference code). Every code example checked against current library docs. ⏸
4. **Build the template skeleton** in `../web-standard`: a runnable app shell (router, query client, a token-driven theme, a layout with a sidebar that collapses on mobile, one example page with loading, empty and error states), a typed API client generated from an OpenAPI file with an SSE reader and a unit-tested parser, MSW mocks, Vitest and one Playwright smoke test, ESLint and strict TypeScript, a CI workflow, a README "start a new web app" checklist, and the agent-facing pieces from Purpose (`CLAUDE.md`, `docs/RECIPES.md`, the `SPEC.md` intake template, `.claude/skills/`, `make check`). Everything green. ⏸
5. **Prove it's reusable:** in a scratch folder, start a small unrelated web app (for example a notes or inventory app: a list page, a detail page, a form, against a mocked API) from the template and build it by following only `CLAUDE.md`, the recipes and the skills, as a fresh coding agent would. Report every question you had to ask, every guess, and every place the standard was silent or Agent Hub-shaped, then fix the standard and template. Throw the sample away. ⏸
6. **Publish it:** create `IsraelBO17/web-standard` as a **private template repository** (`gh repo create … --private`, then `gh repo edit --template`), commit and push. ⏸
7. **Agent Hub profile:** write `agent_hub/docs/WEB_PROFILE.md` (the project-specific rules on top of the standard: the Pencil token pipeline and design rules from `CLAUDE.md`, the type scale 12/13/14/15/20/28/40, lucide icons, the layout sizes, the block renderers and the closed content types, `CHART_SPEC.md`, the SSE and polling rules from `docs/SEND_MESSAGE.md`, Amplify and the domain). Point `CLAUDE.md` and `docs/ARCHITECTURE.md` at it. ⏸

# Phase 2: Build Agent Hub's web layer with the standard (issue #4)
Work on a branch `web-shell` in `agent_hub`; finish with a pull request.
Build it **the way any future project would be built**: from the template, following `CLAUDE.md`, the recipes and the skills. Where they fall short, fix the standard (in its repo, with a version bump) rather than working around it here.
1. **Scaffold `web/` from the template** and apply the Agent Hub profile. ⏸
2. **Build issue #4's scope to the standard** (read `gh issue view 4 --repo IsraelBO17/agent_hub`):
   - CSS variables generated from the design file's variables by a script (never hand-copied colours).
   - The typed client and SSE reader for `api/openapi.yaml`, parsing `id`/`event`/`data` and detecting a 45 s stall.
   - The routes from PRODUCT_PLAN §5 as placeholder pages.
   - The desktop shell (sidebar 284 px, app header, chat column about 760 px), matching the design's Sidebar, App Header and Chat Header components, and usable at 390 px. Use the Pencil MCP if the design file is open; otherwise use `design/INDEX.md` and the file's JSON.
   ⏸
3. **Deploy with Amplify:** the Amplify app `fleet-dev-web-amplify-us-east-1` already exists (monorepo build spec for `web/`, SPA rewrite, `VITE_API_URL`, `VITE_GOOGLE_CLIENT_ID`). Connect it to this repo's `main` branch, and attach `fleet.qucoon.com`, in Terraform where possible. The GitHub connection needs me (a token or the Amplify GitHub App): propose the simplest option and ask. Show me the plan and apply only on my yes. ⏸
4. **Close out:** the shell builds, lints, type-checks and passes tests; it's deployed by Amplify (on `fleet.qucoon.com` once DNS is delegated); deep links work; tick issue #4's items; comment with results and screenshots at desktop and 390 px; open the PR.

Out of scope for #4: sign-in (#6), catalog data (#7), chat and streaming UI (#8), Stop (#9), and the full mock scenarios (M2).

# Rules

## General (both phases)
- Check current docs (React, Vite, React Router, TanStack Query, openapi-typescript, MSW, Playwright, Amplify) before relying on an API. When a reference repo and current best practice disagree, say so and recommend.
- Never commit secrets. Never create billable cloud resources without showing me the plan and getting a yes.
- The new standard repo (`../web-standard`) may use `main`. Don't commit to agent_hub's `main`: use the branch named in Phase 2.
- Nothing below this line belongs in the standard or its template.

## Agent Hub only (Phase 1 step 7, the profile, and Phase 2)
- AWS profile `ml_account` (account 992382810653, us-east-1), **shared with other projects** (D27). Names `fleet-dev-<component>-<type>-us-east-1`; tag values live in the gitignored `infra/envs/dev/terraform.tfvars` and are never committed (agent_hub is public).
- **Dependency:** the custom domain `fleet.qucoon.com` validates only once the `fleet` NS record exists in the qucoon.com zone. Check `dig +short NS fleet.qucoon.com`. If it's empty, deploy to the Amplify default domain, show me the domain plan, and stop there.
- Agent Hub's Terraform is in `infra/` (`make infra-validate`, `make infra-plan`); apply only after I've seen the plan. A GitHub token for the Amplify connection is a secret: never commit it.
