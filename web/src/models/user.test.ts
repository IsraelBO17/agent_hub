import { describe, expect, it } from 'vitest'
import { initialsOf, toDomainUser } from '@/models/user'

describe('user', () => {
  it('takes initials from the first and last words, or the email', () => {
    expect(initialsOf('Israel B.')).toBe('IB')
    expect(initialsOf('Ada Lovelace Byron')).toBe('AB')
    expect(initialsOf('ada.okafor@example.com')).toBe('AO')
    expect(initialsOf('owner@example.com')).toBe('O')
  })

  it('falls back to the email when Google sent no name', () => {
    const user = toDomainUser({ id: 'u1', email: 'owner@example.com', name: null, avatarUrl: null, preferences: { defaultAgentSlug: null, reopenLastSession: false } })
    expect(user).toMatchObject({ displayName: 'owner@example.com', initials: 'O' })
  })
})
