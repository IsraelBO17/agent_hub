---
name: add-auth
description: "Add sign-in, session restore, single-flight token refresh, protected routes, permissions and cross-tab sign-out. Use when users of the app sign in."
argument-hint: "[identity provider]"
---

Add auth by following **recipe 8** in `docs/RECIPES.md` exactly. Identity provider: $ARGUMENTS

1. Read recipe 8, standard §14 and Appendix C3–C4. **Ask the owner first** about anything the profile doesn't settle: provider, session endpoints, refresh-token storage, roles, idle timeout, cross-origin cookie and CSRF handling.
2. Add the session endpoints to the contract and `make api`; add the auth middleware to `service/client.ts`.
3. Build `modules/auth` (session hook, `RequireAuth`, sign-in with `safeNext`, permissions, sign-out with `BroadcastChannel`), wire it in `provider/` and `app/router.tsx`.
4. Add mocks and the tests the recipe lists (redirect with `next`, one refresh for concurrent 401s, failed refresh, sign-out in another tab).
5. Run `make check` and `make e2e` and report, including what the backend must enforce.
