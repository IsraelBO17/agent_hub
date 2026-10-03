// Whether this tab's user chose to sign out, so the guard shows "You've signed out" instead of sending them
// back to the page they were on. A session that ended any other way (expiry, another tab) keeps `next`.
let chose = false

export const noteSignOut = () => { chose = true }
export const signedOutHere = () => chose
export const forgetSignOut = () => { chose = false }
