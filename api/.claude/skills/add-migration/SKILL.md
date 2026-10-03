---
name: add-migration
description: "Create and review an Alembic migration after a model change. Use when tables, columns, constraints or indexes change."
argument-hint: "[what changed]"
---

Create the migration for: $ARGUMENTS, following **recipe 3** in `docs/RECIPES.md`.

1. Make sure the models already describe the change.
2. `make migration m="..."`, then review the generated file by hand as the recipe says (names, defaults, partial indexes, nothing dropped by accident).
3. After launch, split destructive changes into expand and contract releases.
4. `make migrate`, `make downgrade`, `make migrate`, then `make check` (includes `alembic check`). Report the migration id and anything you changed by hand.
