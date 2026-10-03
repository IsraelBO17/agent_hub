---
name: add-stream
description: "Add a Server-Sent Events endpoint. Use when a response arrives over time (progress, tokens, long work)."
argument-hint: "[what the stream sends]"
---

Add the stream described in $ARGUMENTS, following **recipe 6** in `docs/RECIPES.md` and standard §14.

1. Spec and contract first: events, terminal events, time limit, disconnect and cancel behaviour.
2. Put every refusal in a dependency (as `streamable_note` does); the generator only yields events and checks `shutting_down` and the deadline.
3. If its output must survive, checkpoint it with a heartbeat and add the stale-heartbeat sweep.
4. Write the tests, run `make check`, then `curl -N` it against `make run` and send SIGTERM mid-stream to see it end cleanly.
