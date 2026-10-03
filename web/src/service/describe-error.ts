import { ApiError } from '@/service/api-error'
import { StreamStalledError } from '@/service/sse'

// User-facing copy for error codes (standard §15). Add a line per code the contract documents.
const byCode: Record<string, string> = {
  not_found: 'This item no longer exists.',
  invalid_request: 'Check the highlighted fields.',
  invalid_google_token: "Sign-in didn't finish. Try again.",
  session_expired: 'Your session ended. Sign in again.',
  origin_not_allowed: "Sign-in isn't available from this address.",
  identity_provider_unavailable: "Google sign-in isn't answering right now. Try again in a moment.",
  not_invited: "This Google account doesn't have access to Agent Hub.",
  account_disabled: 'This account has been turned off.',
  agent_not_found: "This agent doesn't exist.",
  session_not_found: "This session doesn't exist, or it was deleted.",
  run_in_progress: 'A reply is still running in this session. Wait for it, or stop it, then send.',
  too_many_runs: 'Three replies are already running. Send again when one finishes.',
  agent_unavailable: "The agent isn't available right now. Your message wasn't sent; try again in a moment.",
  message_too_long: 'This message is too long. Keep it under 32,000 characters.',
  empty_message: 'Type a message first.',
  agent_error: 'The agent returned an error.',
  run_time_limit: 'The reply took longer than 15 minutes, so it was stopped.',
  run_interrupted: "The reply didn't finish.",
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
