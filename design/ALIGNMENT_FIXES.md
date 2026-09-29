# Design session prompt: alignment fixes

Paste everything below the line into a new Claude Code session opened in this repo, with `design/fleet_dev.pen` open in Pencil. It is self-contained.

Why these changes: `docs/ALIGNMENT_REVIEW.md` (finding numbers in brackets). Decisions they follow: `docs/ARCHITECTURE.md` D19–D23.

---

You are updating the Agent Hub design in Pencil. Read `CLAUDE.md` first (design rules and Pencil MCP quirks), then `design/README.md` and `design/INDEX.md`. The source of truth is `design/fleet_dev.pen` in this repo. Use tokens only, the 12/13/14/15/20/28/40 type scale, and lucide icons. Pencil has no variants: a new state is its own component named `Component / State`. Don't copy a reusable component to fix a blank frame (it becomes an instance).

Make these changes, then save, run `python3 design/tools/pen_index.py`, and commit `fleet_dev.pen` and `INDEX.md` together with a message naming this file. Report anything you couldn't do.

**1. Approvals (D19).**
- Add an **Approval Card / Cancelled** state: "Cancelled · you sent a new message · nothing was sent". Show it on the Edge States board `OFj2k`.
- On Deny (F4.4 `oTQRM`, mobile F11.13 `s9qGv`, board `Lwlwe` §4): add an optional one-line "Reason (optional)" field shown after pressing Deny, with "Deny" and "Cancel". The Denied card then shows the reason under "Denied by you".
- `Lwlwe` §4 Approved note says "Confirmed with device auth": change to "Approved by you; reference number shown".
- Keep the composer enabled under a pending card (it already is); add a step note on F4.1: "Sending a new message cancels this approval."

**2. Errors and timing (B5).**
- `sx5f0` §6 "Agent timed out" and `D21ObU` "Stream closed after 60s without a done event": replace both with a soft, non-error note under the streaming reply: "Still working · 1:05" (timer icon, `text-tertiary`), no Retry, no danger styling. Board label: "No events for 60 s: the agent may still be working. Not an error."
- Keep Retry on Stopped (already designed).
- Toasts: undo toasts read "undo in 10s" (not 8s) on `ABwYF`, F7.7 `ZX9nG`, `D21ObU`, F11.18 `XRu2z`; on `yzVIz` change the rule to "auto-dismiss after 5 s; undo toasts stay 10 s; errors stay".

**3. Plan card and progress (#9, #12).**
- Plan cards (F4.5 `l7fEn`, F4.7, F11.6 `DuSPU`, `sx5f0` §3–4, `r5Gru`): remove "about 1 min left" / "about 2 min left"; keep "Step 3 of 5" and the elapsed timer. Rename "Cancel task" to "Stop".
- Remove "Notify me" from the "still working" banner (F4.5, `r5Gru`, `sx5f0` §4); keep "You can leave this page. You'll see a toast when it's done."
- Artifact generating states (F3.2 `iFd2Z`, `ZQvzZ`, `F9oiRc` card "42%", Edge States "v3 · 62%"): replace percentages with an indeterminate bar plus the section label ("Writing 'Key results'…").

**4. Agents (#7).**
- Remove the "Deploying" status from the agent switcher on `uBRCZ` and F8.2 `ga0YM` (statuses are Online, Degraded, Offline only; use Degraded or Online).
- Remove "Beta since Sep 20" from catalog cards (`PBQLh`, F2.1, F4.6, F9.7); show "3 sessions · 2d ago" plus the Beta tag.
- Hide "Edit agent" on agent detail (`x05s4W`, F2.2 `PHIgn`, F9.5): it is P2. Leave F9.6 as a parked P2 screen and add "(P2, parked)" to its name.

**5. Artifacts (#12).**
- F4.7 `z5d9eA` "September reconciliation report · PDF": replace the Artifact Card with a `File Card` (PDF). PDFs, images, ZIPs are files, not artifacts, in v1.
- Mobile overflow menu (`SZqQD`, F10.4 `oNbW3`): replace "Download PDF / DOCX / Markdown" with a single "Download (.md)".
- Version menu on `oQYrz` and F3.5 `uQV6q`: v1 lists agent versions only. Remove the "You" version and the Restore buttons; keep "Compare versions" only on the parked P2 screens.
- Remove "6 sources" from the artifact subtitle ("Research brief · Updated 2 min ago").
- Artifacts library (`g2nGvw`, F7.9 `JROuy`, mobile `GSi1C`): add a board note "P1: v1 artifact types are Document, Code, HTML app, Table; Image, Diagram, PDF and ZIP tiles appear with F22."

**6. Attachments (#13).**
- Drop overlay and attach sheet copy (`Q6kwA2` §1, F11.4 `BXfKu`): "PDF, images, CSV or TXT · up to 20 MB each · 10 files" is fine; add a board note that this text comes from the agent's descriptor.
- Remove page and row counts from attachment cards ("PDF · 4 pages · 248 KB" → "PDF · 248 KB", "CSV · 214 rows · 12 KB" → "CSV · 12 KB") on `Q6kwA2` §4, F5.4–F5.7.

**7. Out of v1: hide or label (#15).** In v1 screens, hide: suggested follow-up pills (F2.8 `jX0Iq`, F8.1 `oI49h`, F8.2), the mic / Dictate button in the composer, "Connect tool · Soon" in the "+" menu, Read aloud, and the More menu items Share reply, Copy link, View raw JSON and Report. Keep 👍 / 👎 (now v1) and Copy. Keep Regenerate but label its board state "P1". On `Lwlwe`, label §5 "Tool permission prompt (P2)" and §6 "Suggested follow-ups & 'Was this helpful?' (P1)". In Flow 6, add "(P2)" to F6.5 Rate limited, F6.6 and F6.7; in the rate-limited state on `sx5f0` §6, replace the countdown button with a plain "Try again" (v1 shows the error with `retryAfter` only).

**8. IDs and URLs (#17).** Session info (`E3lQz`, F7.2): show the session id as the first 8 characters of a UUID, e.g. "7f3a91c2  ⧉". Share dialog (`vBr4V`, F7.4 `JFeoX`): link reads "app.agenthub.dev/s/Kq2x9TmV4pLr7Wn3Yb8sHd" (placeholder domain until it's chosen; slug 22+ characters).

**9. Missing P0 states (#18).** Add one reference screen or board section each:
- Sidebar failed to load: sessions list replaced by "Couldn't load sessions · Try again".
- Artifact panel failed to load a version: "Couldn't open v3 · Try again".
- Approval decision failed: pending card stays, with an inline error "Couldn't send your decision · Try again"; buttons stay enabled.
- Sign-in failed: `MMxdZ` with "Sign-in didn't finish. Try again." under the Google button (popup closed or network error).
- Public shared page, link revoked: "This link was turned off by its owner" (desktop and mobile).

**10. Names (#24, optional; do it only if time allows).** Rename sample agents in visible copy: Bank Agent → Ledger. In `IVLvU` §7 diagram, "Next.js" → "Vite + React" and "LangGraph · Lambda" → "LangGraph · HTTP adapter". F1.8 `h9bFF`: Travel Planner shows "LangGraph · HTTP adapter".

Afterwards, update `docs/PRODUCT_PLAN.md` §5 screen inventory for the new states, and tell the owner which items are done.
