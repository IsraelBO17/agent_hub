// Unsent drafts (standard §10: browser storage holds only per-user conveniences like an unsent draft). Kept per
// tab in sessionStorage, so a draft survives signing in again after the session expired; cleared on sign-out.
const prefix = 'agent-hub:draft:'

function storage(): Storage | null {
  try { return window.sessionStorage } catch { return null }
}

export const readDraft = (key: string) => storage()?.getItem(prefix + key) ?? ''

export function writeDraft(key: string, text: string) {
  const s = storage()
  if (!s) return
  try {
    if (text) s.setItem(prefix + key, text)
    else s.removeItem(prefix + key)
  } catch { /* storage full or blocked: the draft lives only in the page */ }
}

export function clearDrafts() {
  const s = storage()
  if (!s) return
  for (const key of Object.keys(s)) if (key.startsWith(prefix)) s.removeItem(key)
}
