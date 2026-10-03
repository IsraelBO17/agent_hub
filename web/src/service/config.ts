// Build-time settings the service layer needs (standard §19: only non-secret values in VITE_*).
export const apiUrl = import.meta.env.VITE_API_URL

/** Abort a stream after this long without bytes: three missed 15 s keep-alives. The profile sets it. */
export const streamStallMs = 45_000
