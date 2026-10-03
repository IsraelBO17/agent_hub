# Agent Hub web app

One signed-in chat interface for many AI agents: pick an agent, talk to it, follow its tools, approvals and artifacts as they stream in (ARCHITECTURE D16). Built to the owner's [Web Development Standard](docs/STANDARD.md) with Agent Hub's values in [`../docs/WEB_PROFILE.md`](../docs/WEB_PROFILE.md). Repo layout: root [`README.md`](../README.md).

| | |
|---|---|
| Owner | Israel B. |
| Stage | Build (M1) |
| Version | 0.1.0 |
| Stack | React · TypeScript · Vite · React Router · TanStack Query · shadcn/ui on Base UI · Tailwind (exceptions below) |
| Profile | [`../docs/WEB_PROFILE.md`](../docs/WEB_PROFILE.md) |
| API contract | [`../api/openapi.yaml`](../api/openapi.yaml) (D23) |
| Spec | [`SPEC.md`](SPEC.md), which indexes the planning documents |

## Run and test
Needs Node 24 (`.nvmrc`). Copy `.env.example` to `.env.local` (mocks are on by default). From this folder:

```bash
npm ci
```

```bash
make dev
```

```bash
make check
```

```bash
make e2e
```

From the repository root the same commands are `make web-install`, `make web-dev`, `make web-check` and `make web-e2e`. `make help` lists every command. CI runs `make check` and `make e2e` in `.github/workflows/web.yml`.

## Deploy
AWS Amplify Hosting builds `web/` from `main` (D13; app `fleet-dev-web-amplify-us-east-1`, managed in `../infra/`). See recipe 9 in [`docs/RECIPES.md`](docs/RECIPES.md) and the profile's Hosting row.

## Exceptions to the standard
From the profile (Exceptions):
- **Toasts** use the Base UI `toast` component, not Sonner (D28). It is added by the first issue that needs a toast.
- **Mobile sheets** that slide up use the Base UI `drawer` (D28).
- **Deleting a session uses undo, not a confirmation** (owner, 2026-10-03): it disappears at once with a 10-second Undo toast, because the API keeps it restorable for that window. Everything irreversible confirms first.
