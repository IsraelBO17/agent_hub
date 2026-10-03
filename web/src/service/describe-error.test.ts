import { describe, expect, it } from 'vitest'
import { ApiError } from '@/service/api-error'
import { describeError } from '@/service/describe-error'
import { StreamStalledError } from '@/service/sse'

describe('describeError', () => {
  it('uses the copy for a known code and keeps the reference', () => {
    expect(describeError(new ApiError({ status: 404, code: 'not_found', message: 'Not Found', requestId: 'req_9' })))
      .toEqual({ message: 'This item no longer exists.', retryable: false, requestId: 'req_9' })
  })
  it('never shows a raw server error', () => {
    expect(describeError(new ApiError({ status: 500, code: 'internal', message: 'NullPointerException' })).message).not.toMatch(/Null/)
  })
  it('describes network failures and stalls as retryable', () => {
    expect(describeError(new TypeError('fetch failed')).retryable).toBe(true)
    expect(describeError(new StreamStalledError('quiet')).retryable).toBe(true)
  })
})
