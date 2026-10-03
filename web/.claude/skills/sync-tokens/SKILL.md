---
name: sync-tokens
description: "Regenerate the design tokens from the design tool and map shadcn's variables onto them. Use when the design's variables changed or tokens are being set up."
argument-hint: "[what changed in the design, if known]"
---

Sync the design tokens by following **recipe 2** in `docs/RECIPES.md` exactly. Context: $ARGUMENTS

1. Read recipe 2, standard §8 and the profile's Design source and Tokens rows.
2. Export or read the design's variables into `design/tokens.json` (or through the profile's adapter), then `make tokens`.
3. Update `src/styles/theme.css` only through `var()`; record any name clash in the profile.
4. Run `make check`, open `make dev`, and report which tokens changed and any screen that now differs from the design.
