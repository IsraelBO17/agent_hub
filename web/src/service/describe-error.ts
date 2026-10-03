import { ApiError } from '@/service/api-error'
import { StreamStalledError } from '@/service/sse'

// User-facing copy for error codes (standard §15). Add a line per code the contract documents.
const byCode: Record<string, string> = {
  not_found: 'This item no longer exists.',
  invalid_request: 'Check the highlighted fields.',
}

export interface ErrorDescription {
  message: string
  requestId?: string
  retryable: boolean
}

/** One readable sentence for any failure, plus what the UI needs to offer Retry and a reference. */
export function describeError(error: unknown): ErrorDescription {
  if (error instanceof StreamStalledError) return { message: 'The connection went quiet, so we stopped waiting.', retryable: true }
  if (!(error instanceof ApiError)) return { message: 'Something went wrong. Check your connection and try again.', retryable: true }
  const message = byCode[error.code] ?? (error.status >= 500 ? 'The server had a problem. Try again in a moment.' : error.message)
  return { message, retryable: error.retryable, ...(error.requestId ? { requestId: error.requestId } : {}) }
}
