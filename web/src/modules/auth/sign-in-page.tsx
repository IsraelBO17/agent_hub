// Design: Sign in (MMxdZ), loading (vkBhc), failed (G7FDcP), signed out (DfY8F); mobile U0HaRi. Not allowed
// (zte2v) is its own view. A signed-in user goes straight to `next`.
import { useCallback, useState } from 'react'
import { Navigate, useSearchParams } from 'react-router'
import { AlertCircle, Check, Icon, Orbit } from '@/components/ui/icon'
import { GoogleSignInButton } from '@/modules/auth/components/google-sign-in-button'
import { NotAllowed } from '@/modules/auth/components/not-allowed'
import { useSession } from '@/modules/auth/hooks/use-session'
import { useSignIn } from '@/modules/auth/hooks/use-sign-in'
import { safeNext } from '@/modules/auth/utils/safe-next'
import { forgetGoogleAccount } from '@/lib/google-identity'
import { ApiError } from '@/service/api-error'
import { describeError } from '@/service/describe-error'

export function SignInPage() {
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const session = useSession()
  const signIn = useSignIn()
  const onCredential = useCallback((idToken: string) => { signIn.mutate(idToken) }, [signIn])
  const [unavailable, setUnavailable] = useState(false)
  const onUnavailable = useCallback(() => { setUnavailable(true) }, [])

  if (session.status === 'signed-in') return <Navigate replace to={next} />

  const error = signIn.error
  const refused = error instanceof ApiError && (error.code === 'not_invited' || error.code === 'account_disabled')
  const useAnotherAccount = () => { forgetGoogleAccount(); signIn.reset() }

  return (
    <main id="main" tabIndex={-1} className="flex min-h-dvh flex-col items-center justify-center bg-bg px-4 pb-20 outline-none">
      <title>Sign in · Agent Hub</title>
      {refused ? (
        <NotAllowed
          reason={error.code === 'not_invited' ? 'not-invited' : 'disabled'}
          email={typeof error.extras.email === 'string' ? error.extras.email : undefined}
          onUseAnotherAccount={useAnotherAccount}
        />
      ) : (
        <div className="flex w-full max-w-90 flex-col items-center gap-5">
          <div className="flex w-full flex-col items-center gap-3 text-center">
            <span className="flex size-12 items-center justify-center rounded-13 bg-accent text-on-accent"><Icon icon={Orbit} className="size-6.5" /></span>
            <h1 tabIndex={-1} className="text-28 font-semibold text-text-primary outline-none">Agent Hub</h1>
            <p className="text-15 leading-normal text-text-secondary">One place to chat with all your AI agents.</p>
          </div>
          {params.has('signed-out') && !error ? (
            <p role="status" className="flex items-center gap-1.5 rounded-full bg-surface-muted px-3 py-1.5 text-13 text-text-secondary">
              <Icon icon={Check} className="size-3.5" />
              You&apos;ve signed out
            </p>
          ) : null}
          <div className="flex w-full flex-col items-center gap-3 pt-2">
            <GoogleSignInButton pending={signIn.isPending || session.status === 'restoring'} onCredential={onCredential} onUnavailable={onUnavailable} />
            {error || unavailable ? (
              <p role="alert" className="flex items-center gap-1.5 text-13 text-danger">
                <Icon icon={AlertCircle} className="size-3.5" />
                {error ? describeError(error).message : "Google sign-in didn't load. Check your connection and reload."}
              </p>
            ) : null}
            <p className="text-12 text-text-tertiary">Access is by invitation.</p>
          </div>
        </div>
      )}
    </main>
  )
}
