---
name: deploy
description: "Deploy the web app to an environment: host settings, SPA rewrite, headers, build config, release bump and checks against the deployment. Use for the first deploy or a release."
argument-hint: "[environment]"
disable-model-invocation: true
---

Deploy by following **recipe 9** in `docs/RECIPES.md` exactly. Environment: $ARGUMENTS

1. Read recipe 9, standard §19, §24 and §25, and the profile's Hosting, Environments and Names rows.
2. Prepare the plan (host settings, rewrite, headers, `VITE_*` values, any infrastructure change). **Show the owner the plan and apply only on a yes.** Never commit a token.
3. Bump the version and the changelog for a release.
4. After the deploy, check deep links and headers with `curl -I`, run the smoke test against the deployment, and confirm a test error reaches the error reporter.
5. Report against the release checklist in standard §25, with each command and its result.
