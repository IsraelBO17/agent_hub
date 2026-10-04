# M1 screenshots in mock mode

The web app at `main` commit `251a14a` (M1 closed), run locally in mock mode (`VITE_API_MOCKS=true`, MSW scenarios chosen with `?scenario=`), taken with Playwright at 1440 × 1024 (`desktop-*`) and 390 × 844 (`mobile-*`) on 2026-10-03 for the design gallery (`design/renders/index.html`). They fill the gaps in `issue-4/` (the early shell) and `issue-8/` (chat states): the real catalog and its empty, error and loading states, sign-in and its failure states, not-found pages, the agent switcher and Settings.

`*-catalog-loading.png` is taken 0.4 s after `GET /v1/agents` starts in the `slow` scenario (every API call delayed 2 s), so the catalog skeleton shows. Before that, while the session is restored, a sidebar-shaped skeleton shows even on the catalog, which has no sidebar.
