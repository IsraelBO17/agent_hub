---
name: add-component
description: "Add a shadcn primitive or a composite component that a design calls for, styled only through tokens and variants. Use when a screen needs a UI piece that doesn't exist yet."
argument-hint: "[component name or design component]"
---

Add a component by following **recipe 4** in `docs/RECIPES.md` exactly. The component: $ARGUMENTS

1. Read recipe 4 and standard §8.
2. Check for a shadcn primitive first (`npx shadcn@latest add <name>`); register any file it creates in `eslint.config.js` (`vendored`) and `scripts/check-tokens.ts` (`skip`).
3. Otherwise build a composite from primitives in the feature (or `components/ui` if domain-free), one component per file, with its design link comment, states and 44 px touch targets.
4. Run `make check` and report what was added or customised, and where it's used.
