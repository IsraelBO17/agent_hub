import { isRouteErrorResponse, useRouteError } from 'react-router'
import { EmptyState } from '@/components/ui/empty-state'
import { reportError } from '@/lib/monitoring'
import { NotFoundPage } from '@/modules/shell/not-found-page'

/** The root error boundary (standard §9): never a blank screen or a stack trace. */
export function RootError() {
  const error = useRouteError()
  if (isRouteErrorResponse(error) && error.status === 404) return <NotFoundPage />
  reportError(error, { boundary: 'root' })
  return (
    <main className="mx-auto max-w-xl p-6">
      <title>Something went wrong · Agent Hub</title>
      <h1 className="sr-only">Something went wrong</h1>
      <EmptyState kind="error" message="This page failed to load. Reloading usually fixes it." onRetry={() => { location.reload() }} />
    </main>
  )
}
