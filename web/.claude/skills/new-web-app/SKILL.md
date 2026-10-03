---
name: new-web-app
description: "Turn a repository freshly created from the web-standard template into a real web app. Use when package.json is still named web-name or the user asks to start a new web app."
argument-hint: "[one-sentence job of the app]"
disable-model-invocation: true
---

Start a new web app from this template by following **recipe 1** in `docs/RECIPES.md` exactly. The job the user described: $ARGUMENTS

1. Read `CLAUDE.md`, `docs/RECIPES.md` (recipe 1) and `docs/STANDARD.md` §1–8, and the project profile if there is one.
2. Ask the owner the recipe's questions in **one** batch, each with your recommendation; use the standard's defaults for everything else and list them.
3. Write `SPEC.md`. **Stop and get the owner's approval of the spec before writing any code.**
4. Rename, apply or create the profile, generate tokens (recipe 2), map screens to the design, and set up the contract (`make api`). **Stop and get the owner's approval of the design map and the contract.**
5. Build the first screen with recipes 5 and 3 while `notes` is there to copy, then remove the golden path (recipe 1, step 9), fill in the headers of `README.md` and `CLAUDE.md`, and delete the README's template block.
6. Run `make check` and `make e2e` and report: what was done, what was removed, every question you answered with a default, and what's next (usually the remaining screens via `/add-api-call` and `/add-page`).
