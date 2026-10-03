---
name: add-job
description: "Add a background job or a periodic sweep on the Postgres job table. Use for work after commit, retries, calls to other systems, or anything periodic."
argument-hint: "[what the job does and what triggers it]"
---

Add the job or sweep described in $ARGUMENTS, following **recipe 5** in `docs/RECIPES.md` and standard §13.

1. Write its block in `SPEC.md` (trigger, payload, idempotency, retries, what dead means; or interval, bound and retention for a sweep).
2. Put the handler in the owning feature's `jobs.py`, as `features/notes/jobs.py` does; enqueue it inside the producing service's transaction.
3. Make it idempotent and prove it: the tests run it twice, roll back a producer, and force a failure.
4. Run `make check`, then trigger it for real with `make run` + `make worker` and show its log line.
