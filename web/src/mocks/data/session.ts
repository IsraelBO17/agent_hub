// The mock API's session (synthetic data only): whether the refresh cookie is "set", and the one invited user.
import type { Me } from '@/service/generated/schema'

export const invitedEmail = 'owner@example.com'

export const owner: Me = {
  id: '6f1d2c3b-4a5e-4f60-8a7b-9c0d1e2f3a4b',
  email: invitedEmail,
  name: 'Ada Owner',
  avatarUrl: null,
  preferences: { defaultAgentSlug: null, reopenLastSession: false },
}

export const mockSession = { signedIn: true, accessToken: 'mock-access-1', issued: 1 }

/** Back to signed in with a fresh token (tests call it after each test). */
export function resetMockSession(signedIn = true) {
  mockSession.signedIn = signedIn
  mockSession.issued += 1
  mockSession.accessToken = `mock-access-${String(mockSession.issued)}`
}
