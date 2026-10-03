---
name: pre-merge
description: "Review the current change against the API standard before merging. Use before opening or merging a pull request."
---

Review the current diff (`git diff` against the base branch) with **recipe 9** in `docs/RECIPES.md`.

1. Run `make check` and report its result.
2. Go through every item in recipe 9 and report PASS / FAIL / N/A with the file and line for each FAIL.
3. End with one line: ready to merge, or the blocking items.
