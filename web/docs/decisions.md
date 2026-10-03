# Decisions

Every assumption, deviation from the design and judgment call (standard §6.1). Append only; never rewrite an entry.

| Date | Screen or feature | Decision | Reason | Alternative rejected |
|---|---|---|---|---|
| 2026-10-03 | Setup (#4) | The template's `notes` golden path was removed before the first screen was built, not after (recipe 1, step 9). | `notes` type-checks only against the template's example contract; with `../api/openapi.yaml` it breaks `make check`. Patterns are copied from the `web-standard` repository instead. | Keeping the example contract until the first screen works (two contracts at once). |
| 2026-10-03 | Setup (#4) | Sonner removed with `notes`; no toast library until the first issue that needs a toast adds the Base UI `toast` (profile: Exceptions). | #4 has no mutations, so nothing toasts yet; one library per concern (standard §3). | Adding the Base UI toast now, unused. |
| 2026-10-03 | Setup (#4) | Playwright runs at 1440 × 1024, 768 × 1024 and 390 × 844. | The profile's widths are the design's frames plus a tablet. | The template's 1280 and Pixel 7 (412). |
| 2026-10-03 | Setup (#4) | `/` shows a placeholder "All agents" page until the shell and the catalog are built. | The index route needs a screen once `notes` is gone. | Keeping a `notes` route as the index. |
