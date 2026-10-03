---
name: add-stream
description: "Add a Server-Sent Events stream read with fetch: service function, cache state, hook with abort and stall handling, live-region UI, mocks and tests. Use when a reply or result arrives over time."
argument-hint: "[operation that streams]"
---

Add a stream by following **recipe 6** in `docs/RECIPES.md` exactly. The stream: $ARGUMENTS

1. Read recipe 6, standard §12, and the profile's Streams and polling row (stall time, what happens after a stall).
2. Write the service function with `parseAs: 'stream'` and `readSse`, copying `streamNoteSummary`; the cache state; and the hook, copying `use-note-summary.ts`.
3. Build the UI with a polite live region, Stop, and the stalled and failed messages.
4. Add mocks for the stream, a failure event and a stall; a component test for the stall (fake `setTimeout` only); an e2e with `page.clock`.
5. Run `make check` and `make e2e` and report the events handled and how each end state looks.
