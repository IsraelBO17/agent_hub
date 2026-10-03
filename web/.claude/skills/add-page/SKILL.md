---
name: add-page
description: "Add a screen and its route with every state (loading, empty, error, permission-gated, success), tests and screenshots. Use when the spec has a screen that isn't built."
argument-hint: "[route and screen name]"
---

Add a page by following **recipe 3** in `docs/RECIPES.md` exactly. The screen: $ARGUMENTS

1. Read recipe 3, standard §9, §15 and §16, and the screen's block in `SPEC.md` (write or update the block first if it's missing).
2. Make sure its data exists (`/add-api-call` for each endpoint), then build the screen in its module, copying `modules/notes/notes-page.tsx`, with a skeleton, `EmptyState` for empty and error, and a `<title>`.
3. Export it from the module's `index.ts`, add the thin route file and the lazy route, and the navigation item if it belongs in the sidebar.
4. Add the component test, the smoke route and any e2e flow.
5. Run `make check` and `make e2e`, look at each state at each width (`?scenario=` for empty, error, slow), tab through it, and report with screenshot paths and any deviation logged in `docs/decisions.md`.
