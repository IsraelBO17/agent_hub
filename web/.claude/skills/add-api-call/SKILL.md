---
name: add-api-call
description: "Wire an API operation end to end: contract check, generated types, domain model and mapper, query or mutation options, error copy, MSW mocks and tests. Use when a screen needs data from an endpoint."
argument-hint: "[operation, e.g. GET /v1/notes]"
---

Add an API call by following **recipe 5** in `docs/RECIPES.md` exactly. The operation: $ARGUMENTS

1. Read recipe 5 and standard §11. Find the operation in the contract; if it isn't there, **stop and ask** (never invent an endpoint or field).
2. `make api`, then the model and `toDomain` mapper, then the `queryOptions` / `mutationOptions` in the resource's service file, copying `service/notes.ts`.
3. Add error copy for the codes the screen must explain, MSW handlers with synthetic data and problem-detail errors, and scenarios for the states worth demoing.
4. Test the mapper, and the success and failure through MSW.
5. Run `make check` and report the operation, the keys it uses, what it invalidates and the scenarios added.
