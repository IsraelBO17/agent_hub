---
name: deploy
description: "Release and deploy a version: bump, build the arm64 image, push, plan, and apply only with the owner's approval. Use when a version is ready for an environment."
argument-hint: "[environment]"
disable-model-invocation: true
---

Deploy to $ARGUMENTS by following **recipe 8** in `docs/RECIPES.md` and the project profile.

1. Bump the version and changelog; `make check` on the release commit.
2. `make image`, tag with the git SHA, push to the profile's registry.
3. Run `terraform plan` and **show the plan to the owner. Do not apply until they say yes.**
4. Migrations as a one-off task with the direct URL, then roll out.
5. Check `/v1/health` through the load balancer and one authenticated request; report the results against standard §20's release checklist.
