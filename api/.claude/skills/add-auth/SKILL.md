---
name: add-auth
description: "Add sign-in and sessions: an identity provider, the service's own access tokens and rotating refresh tokens. Use when clients need to sign in."
argument-hint: "[identity provider, e.g. Google]"
---

Add authentication with $ARGUMENTS as the identity provider, following **recipe 4** in `docs/RECIPES.md` and standard §12.

1. Read the project profile for the provider, client id setting and cookie rules; ask the owner only what it doesn't settle.
2. Spec blocks and contract first (the recipe lists the defaults), then the dependencies, tables, a non-blocking token verifier tests can replace, sign-in, refresh with rotation and reuse detection, logout and the Origin check.
3. Never log tokens or cookies; store refresh tokens only as hashes; keep the JWT algorithm pinned in `core/auth.py`.
4. Write the recipe's tests, run `make check`, and exercise sign-in, refresh and logout against `make run`.
