---
name: add-resource
description: "Add a resource or feature end to end: spec, contract, model, migration, repository, service, router, tests. Use when the user wants a new resource, table or set of endpoints."
argument-hint: "[resource name and what it is]"
---

Add the resource described in $ARGUMENTS by following **recipe 2** in `docs/RECIPES.md`, copying each file's shape from `src/<package>/features/notes/` (if it has been removed, from a feature already built, or from the `api-standard` template repository).

1. Write the capability blocks in `SPEC.md` first. Any rule the owner hasn't settled is a question: ask them (one batch) before writing code.
2. Add the operations, schemas and error codes to `openapi.yaml`.
3. Then model → migration (recipe 3) → exceptions → schemas → repository → service → door (only if another feature needs it) → router → tests, as the recipe lists.
4. Run `make check`, call the new endpoints once against `make run`, and report which blocks are implemented and tested.
