// The one API client (standard §11.2, Appendix C4), with Agent Hub's session (D8, WEB_PROFILE Identity): the
// access token lives in this module's memory only; the refresh token is an HttpOnly cookie on the API's host.
// On a 401 the client refreshes once (concurrent requests share that refresh), then repeats the request once.
import createClient, { type Middleware } from 'openapi-fetch'
import { apiUrl as baseUrl } from '@/service/config'
import type { paths } from '@/service/generated/schema'

let accessToken: string | null = null
let refreshing: Promise<string | null> | null = null
let onSessionEnded: () => void = () => undefined

export const setAccessToken = (token: string | null) => { accessToken = token }
export const hasAccessToken = () => accessToken !== null
/** Registered by the session provider: called once when a refresh fails mid-session. */
export const onSessionEnd = (handler: () => void) => { onSessionEnded = handler }

// Look fetch up per request, so MSW and test interceptors apply whatever the import order.
const fetch = (request: Request) => globalThis.fetch(request)

/** The auth endpoints' client: no bearer token and no refresh-and-retry, so a refresh never loops. */
export const authClient = createClient<paths>({ baseUrl, credentials: 'include', fetch })

/** Exchanges the refresh cookie for a new access token, or null when there's no session. Single-flight. */
export function refreshSession(): Promise<string | null> {
  refreshing ??= authClient
    .POST('/v1/auth/refresh')
    .then(({ data }) => (accessToken = data?.accessToken ?? null))
    .catch(() => (accessToken = null))
    .finally(() => { refreshing = null })
  return refreshing
}

const copies = new Map<string, Request>()

const auth: Middleware = {
  onRequest({ request, id }) {
    if (accessToken) request.headers.set('Authorization', `Bearer ${accessToken}`)
    copies.set(id, request.clone()) // fetch consumes the body; keep a copy for one retry
    return request
  },
  async onResponse({ response, id, options }) {
    const copy = copies.get(id)
    copies.delete(id)
    if (response.status !== 401 || !copy) return undefined
    const token = await refreshSession()
    if (!token) {
      onSessionEnded()
      return undefined // the caller sees the 401
    }
    copy.headers.set('Authorization', `Bearer ${token}`)
    return options.fetch(copy) // one retry; its response replaces the 401
  },
  onError({ id }) { copies.delete(id) },
}

export const api = createClient<paths>({ baseUrl, credentials: 'include', fetch })
api.use(auth)
