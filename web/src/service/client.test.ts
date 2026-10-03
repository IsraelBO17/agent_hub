import { http } from 'msw/http'
import { describe, expect, it, vi } from 'vitest'
import { mockSession, resetMockSession } from '@/mocks/data/session'
import { server } from '@/mocks/node'
import { api, onSessionEnd, setAccessToken } from '@/service/client'

/** Counts refresh calls, then lets the default handler answer. */
function countRefreshes() {
  const calls = { count: 0 }
  server.use(http.post('*/v1/auth/refresh', () => { calls.count += 1 }))
  return calls
}

describe('the client\'s session', () => {
  it('refreshes once for concurrent 401s, then repeats each request with the new token', async () => {
    setAccessToken('stale-token')
    const refreshes = countRefreshes()
    const [a, b] = await Promise.all([api.GET('/v1/me'), api.GET('/v1/me')])
    expect(refreshes.count).toBe(1)
    expect(a.response.status).toBe(200)
    expect(b.data?.email).toBe('owner@example.com')
  })

  it('ends the session when the refresh fails, and the caller sees the 401', async () => {
    setAccessToken('stale-token')
    resetMockSession(false)
    const ended = vi.fn()
    onSessionEnd(ended)
    const { response, error } = await api.GET('/v1/me')
    expect(response.status).toBe(401)
    expect(error).toMatchObject({ code: 'token_expired' })
    expect(ended).toHaveBeenCalledTimes(1)
  })

  it('sends the access token it holds', async () => {
    setAccessToken(mockSession.accessToken)
    const refreshes = countRefreshes()
    const { response } = await api.GET('/v1/me')
    expect(response.status).toBe(200)
    expect(refreshes.count).toBe(0)
  })
})
