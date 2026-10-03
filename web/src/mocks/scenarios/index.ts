// Named handler sets chosen with ?scenario=<name> in mock mode (standard §11.5). The first matching
// handler wins, so a scenario lists its overrides before the defaults.
import type { RequestHandler } from 'msw'
import { http, HttpResponse } from 'msw/http'
import { delay } from 'msw/utils/delay'
import { resetMockSession } from '@/mocks/data/session'
import { handlers } from '@/mocks/handlers'
import { problem } from '@/mocks/responses'

const scenarios: Record<string, RequestHandler[]> = {
  slow: [http.all('*/v1/*', async () => { await delay(2_000) })],
  // Sign-in (issue #6). `signed-out` starts without a session; the others change what sign-in answers.
  'signed-out': [],
  'not-invited': [http.post('*/v1/auth/google', () => problem(403, 'not_invited', "This Google account doesn't have access to Agent Hub", { email: 'ada.okafor@example.com' }))],
  'account-disabled': [http.post('*/v1/auth/google', () => problem(403, 'account_disabled', 'This account has been turned off'))],
  'google-down': [http.post('*/v1/auth/google', () => problem(503, 'identity_provider_unavailable', "Google's signing keys couldn't be fetched", { retryAfter: 5 }))],
  // The catalog (issue #7).
  'no-agents': [http.get('*/v1/agents', () => HttpResponse.json({ items: [] }))],
  'agents-down': [http.get('*/v1/agents', () => problem(503, 'internal_error', "The registry didn't answer"))],
  // The first /v1/me answers token_expired, so the client refreshes and repeats it.
  expired: [http.get('*/v1/me', () => problem(401, 'token_expired', 'Access token expired'), { once: true })],
}

const startSignedOut = new Set(['signed-out', 'not-invited', 'account-disabled', 'google-down'])

export const scenarioNames = Object.keys(scenarios)

export function handlersFor(name: string | null): RequestHandler[] {
  resetMockSession(!(name && startSignedOut.has(name)))
  return [...(name ? (scenarios[name] ?? []) : []), ...handlers]
}
