// The signed-in user (contract `Me`), as the UI shows it.
import type { Me } from '@/service/generated/schema'

export interface User {
  id: string
  email: string
  /** The Google name, or the email when there's none. */
  displayName: string
  /** One or two letters for the avatar tile (the CSP serves no Google photos). */
  initials: string
  defaultAgentSlug: string | null
}

export function initialsOf(name: string): string {
  const words = name.replace(/@.*/, '').split(/[\s._-]+/).filter(Boolean)
  const letters = words.length > 1 ? `${words[0]?.[0] ?? ''}${words[words.length - 1]?.[0] ?? ''}` : (words[0] ?? '?').slice(0, 1)
  return letters.toUpperCase()
}

export function toDomainUser(me: Me): User {
  const displayName = me.name?.trim() || me.email
  return { id: me.id, email: me.email, displayName, initials: initialsOf(displayName), defaultAgentSlug: me.preferences.defaultAgentSlug }
}
