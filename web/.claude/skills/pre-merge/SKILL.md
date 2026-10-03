---
name: pre-merge
description: "Check a branch against the standard before merge: spec, checks, states, data rules, tokens, accessibility, security, decisions, screenshots. Use before asking for a merge or a review."
argument-hint: "[branch or pull request, optional]"
---

Run **recipe 10** in `docs/RECIPES.md` against the current changes. Target: $ARGUMENTS

1. Read recipe 10 and look at the diff (`git diff main...HEAD`).
2. Run `make check`, and `make e2e` if a screen changed.
3. Go through every item and report PASS, FAIL (with file and line) or N/A.
4. End with "ready to merge", or the list of blocking items.
