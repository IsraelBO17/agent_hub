// The layout route around every signed-in screen (standard §9, Appendix C3).
import { Navigate, Outlet, useLocation } from 'react-router'
import { AppShellSkeleton } from '@/components/layout/app-shell-skeleton'
import { EmptyState } from '@/components/ui/empty-state'
import { useSession } from '@/modules/auth/hooks/use-session'
import { signedOutHere } from '@/modules/auth/utils/signed-out-here'
import { describeError } from '@/service/describe-error'

export function RequireAuth() {
  const { status, error, retry } = useSession()
  const { pathname, search } = useLocation()
  if (status === 'restoring') return <AppShellSkeleton />
  if (status === 'signed-out') return <Navigate replace to={signedOutHere() ? '/sign-in?signed-out' : `/sign-in?next=${encodeURIComponent(pathname + search)}`} />
  if (status === 'error') {
    return (
      <main id="main" className="flex min-h-dvh items-center justify-center p-4">
        <h1 className="sr-only">Your account didn&apos;t load</h1>
        <EmptyState kind="error" {...describeError(error)} onRetry={retry} />
      </main>
    )
  }
  return <Outlet />
}
