// Whether the session ran out while the user was signed in (a refresh failed mid-use). The page stays, with the
// "Session expired" dialog over it, so a draft isn't lost (SPEC: the session).
import { useSyncExternalStore } from 'react'

let expired = false
const listeners = new Set<() => void>()
const set = (value: boolean) => { expired = value; listeners.forEach((l) => { l() }) }

export const markExpired = () => { set(true) }
export const clearExpired = () => { set(false) }
export const useExpired = () => useSyncExternalStore((l) => { listeners.add(l); return () => listeners.delete(l) }, () => expired)
