// Error reporting (standard §21, Appendix C11). Sentry loads only when VITE_SENTRY_DSN is set, so it
// costs nothing when off. Its browser tracing also records LCP, INP and CLS from real users (§18).
import type * as SentryModule from '@sentry/react'

type Sentry = typeof SentryModule
type Context = Record<string, string | number | undefined>

const dsn = import.meta.env.VITE_SENTRY_DSN
let sentry: Sentry | null = null
const early: [unknown, Context][] = [] // reported before Sentry finished loading

export async function initMonitoring() {
  if (!dsn) return
  const S = await import('@sentry/react')
  S.init({
    dsn,
    environment: import.meta.env.VITE_ENVIRONMENT,
    release: import.meta.env.VITE_RELEASE,
    integrations: [S.browserTracingIntegration()],
    tracesSampleRate: 0.1,
    // Sentry 11 collects everything unless told otherwise.
    dataCollection: {
      userInfo: false,
      cookies: false,
      httpBodies: [],
      urlQueryParams: false,
      httpHeaders: { request: { deny: ['authorization', 'cookie'] }, response: { deny: ['set-cookie'] } },
    },
    beforeSend(event) {
      if (event.user) event.user = event.user.id === undefined ? {} : { id: event.user.id } // keep only the id
      return event
    },
  })
  sentry = S
  early.splice(0).forEach(([error, context]) => { S.captureException(error, { extra: context }) })
}

/** The only way code reports an error (standard §21). */
export function reportError(error: unknown, context: Context = {}) {
  if (!dsn) return
  if (sentry) sentry.captureException(error, { extra: context })
  else if (early.length < 20) early.push([error, context])
}

/** React 19's root error hooks: errors no boundary handled, and errors a boundary caught. */
export const reactErrorHandlers = {
  onUncaughtError: (error: unknown, info: { componentStack?: string | undefined }) => { reportError(error, { componentStack: info.componentStack }) },
  onCaughtError: (error: unknown, info: { componentStack?: string | undefined }) => { reportError(error, { componentStack: info.componentStack }) },
}
