// MSW handlers for sign-in and the session (contract Auth and Me; D8). The refresh cookie is simulated by
// `mockSession.signedIn`; the access token is checked on `/v1/me` like the API does.
import type { PathParams } from 'msw'
import { http, HttpResponse } from 'msw/http'
import { invitedEmail, mockSession, owner, resetMockSession } from '@/mocks/data/session'
import { problem } from '@/mocks/responses'
import type { AccessToken, Me, Problem, SignInResponse } from '@/service/generated/schema'

const expiresAt = () => new Date(Date.now() + 15 * 60_000).toISOString()

/** The mock Google credential is `mock-google-id-token:<email>` (the mock sign-in button sends it). */
const emailIn = (idToken: string) => (idToken.startsWith('mock-google-id-token:') ? idToken.slice('mock-google-id-token:'.length) : null)

export const authHandlers = [
  http.post<PathParams, { idToken: string }, SignInResponse | Problem>('*/v1/auth/google', async ({ request }) => {
    const { idToken } = await request.json()
    const email = emailIn(idToken)
    if (!email) return problem(401, 'invalid_google_token', "The Google sign-in couldn't be verified")
    if (email !== invitedEmail) return problem(403, 'not_invited', "This Google account doesn't have access to Agent Hub", { email })
    resetMockSession(true)
    return HttpResponse.json<SignInResponse>({ accessToken: mockSession.accessToken, expiresAt: expiresAt(), user: owner })
  }),
  http.post<PathParams, never, AccessToken | Problem>('*/v1/auth/refresh', () => {
    if (!mockSession.signedIn) return problem(401, 'session_expired', 'Sign in again')
    resetMockSession(true)
    return HttpResponse.json<AccessToken>({ accessToken: mockSession.accessToken, expiresAt: expiresAt() })
  }),
  http.post('*/v1/auth/logout', () => {
    mockSession.signedIn = false
    return new HttpResponse(null, { status: 204 })
  }),
  http.get<PathParams, never, Me | Problem>('*/v1/me', ({ request }) => {
    if (request.headers.get('authorization') !== `Bearer ${mockSession.accessToken}`) return problem(401, 'token_expired', 'Access token expired')
    return HttpResponse.json(owner)
  }),
]
