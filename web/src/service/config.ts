// Build-time settings the service layer needs (standard §19: only non-secret values in VITE_*).
export const apiUrl = import.meta.env.VITE_API_URL

/** Abort a stream after this long without bytes: three missed 15 s keep-alives. The profile sets it. */
export const streamStallMs = 45_000

/** The Google OAuth client the sign-in button uses (public, D15). */
export const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''

/** Mock mode (standard §11.5): MSW answers the API, and sign-in uses a stand-in for Google's button. */
export const mocksOn = import.meta.env.VITE_API_MOCKS === 'true'
