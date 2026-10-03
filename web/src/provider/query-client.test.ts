import { describe, expect, it } from 'vitest'
import { shouldRetry } from '@/provider/query-client'
import { ApiError } from '@/service/api-error'

const err = (status: number) => new ApiError({ status, code: 'x', message: 'x' })

describe('shouldRetry', () => {
  it('retries server and network errors once', () => {
    expect(shouldRetry(0, err(503))).toBe(true)
    expect(shouldRetry(0, new TypeError('fetch failed'))).toBe(true)
    expect(shouldRetry(1, err(503))).toBe(false)
  })
  it('does not retry client errors, except timeouts and rate limits', () => {
    expect(shouldRetry(0, err(404))).toBe(false)
    expect(shouldRetry(0, err(429))).toBe(true)
    expect(shouldRetry(0, err(408))).toBe(true)
  })
})
