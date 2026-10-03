---
name: add-integration
description: "Add a client for another system (HTTP API, email, payments). Use when the service must call something outside itself."
argument-hint: "[system and what we call]"
---

Add an integration with $ARGUMENTS, following **recipe 7** in `docs/RECIPES.md`.

1. Write what we call and what happens on failure in `SPEC.md`.
2. One client per process with explicit timeouts, typed errors and validated responses; secrets as settings.
3. Call it from a job handler, never inside a request's transaction.
4. Test with `httpx.MockTransport` (success, errors, timeout); `make check` must not call the real system.
