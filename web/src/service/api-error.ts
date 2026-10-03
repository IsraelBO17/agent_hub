// One error type for every failed call (standard §11.2). Reads RFC 9457 problem details when the body
// has them, and falls back to the HTTP status otherwise.
export class ApiError extends Error {
  override name = 'ApiError'
  readonly status: number
  readonly code: string
  readonly requestId: string | undefined
  readonly retryable: boolean
  /** Field errors keyed by field name (the last segment of the problem's JSON pointer). */
  readonly fieldErrors: Readonly<Record<string, string>>

  constructor(init: {
    status: number
    code: string
    message: string
    requestId?: string | undefined
    retryable?: boolean
    fieldErrors?: Record<string, string>
  }) {
    super(init.message)
    this.status = init.status
    this.code = init.code
    this.requestId = init.requestId
    this.retryable = init.retryable ?? init.status >= 500
    this.fieldErrors = init.fieldErrors ?? {}
  }
}

const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null

/** What toApiError needs from a response. A stream's error event passes its problem's own status. */
export interface ResponseLike {
  status: number
  statusText?: string
  headers?: Headers
}

export function toApiError(body: unknown, response: ResponseLike): ApiError {
  const p = isRecord(body) ? body : {}
  const fieldErrors: Record<string, string> = {}
  if (Array.isArray(p.errors)) {
    for (const e of p.errors) {
      if (isRecord(e) && typeof e.path === 'string' && typeof e.message === 'string') {
        fieldErrors[e.path.split('/').pop() ?? e.path] = e.message
      }
    }
  }
  return new ApiError({
    status: response.status,
    code: typeof p.code === 'string' ? p.code : `http_${String(response.status)}`,
    message: typeof p.title === 'string' ? p.title : response.statusText || 'Request failed',
    requestId: typeof p.requestId === 'string' ? p.requestId : (response.headers?.get('x-request-id') ?? undefined),
    ...(typeof p.retryable === 'boolean' ? { retryable: p.retryable } : {}),
    fieldErrors,
  })
}

/** Turns an openapi-fetch result into its data, or throws ApiError (so TanStack Query sees a failure). */
export async function unwrap<T>(call: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await call
  if (error !== undefined || !response.ok) throw toApiError(error, response)
  return data as T
}
