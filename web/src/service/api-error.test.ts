import { describe, expect, it } from 'vitest'
import { ApiError, toApiError, unwrap } from '@/service/api-error'

const json = (body: unknown, status: number, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/problem+json', ...headers } })

describe('toApiError', () => {
  it('reads problem details and maps field errors by field name', () => {
    const body = { type: 'about:blank', title: 'Check the highlighted fields', status: 400, code: 'invalid_request', requestId: 'req_1',
      errors: [{ path: '/title', message: 'Already used' }] }
    const e = toApiError(body, json(body, 400))
    expect(e).toBeInstanceOf(ApiError)
    expect(e).toMatchObject({ status: 400, code: 'invalid_request', message: 'Check the highlighted fields', requestId: 'req_1', retryable: false })
    expect(e.fieldErrors).toEqual({ title: 'Already used' })
  })

  it('falls back to the status when the body is not a problem', () => {
    const e = toApiError('<html>bad gateway</html>', new Response('', { status: 502, statusText: 'Bad Gateway', headers: { 'x-request-id': 'req_2' } }))
    expect(e).toMatchObject({ status: 502, code: 'http_502', message: 'Bad Gateway', requestId: 'req_2', retryable: true })
  })

  it('honours the retryable flag from the problem', () => {
    expect(toApiError({ code: 'busy', retryable: true }, { status: 409 }).retryable).toBe(true)
  })

  it('keeps the problem\'s extension members', () => {
    const error = toApiError({ code: 'not_invited', title: 'No access', email: 'ada@example.com', retryAfter: 5 }, { status: 403 })
    expect(error.extras).toEqual({ email: 'ada@example.com', retryAfter: 5 })
  })
})

describe('unwrap', () => {
  it('returns data on success and throws ApiError on failure', async () => {
    await expect(unwrap(Promise.resolve({ data: 1, response: new Response(null, { status: 200 }) }))).resolves.toBe(1)
    await expect(unwrap(Promise.resolve({ error: { code: 'not_found', title: 'Not found' }, response: json({}, 404) })))
      .rejects.toMatchObject({ name: 'ApiError', status: 404, code: 'not_found' })
  })
})
