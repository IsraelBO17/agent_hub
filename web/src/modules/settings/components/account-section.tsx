// Design: Settings → Account (RHrDH): the signed-in user and Sign out (issue #6).
import { Button } from '@/components/ui/button'
import { Icon, LogOut } from '@/components/ui/icon'
import { GoogleMark, useSession, useSignOut } from '@/modules/auth'

export function AccountSection() {
  const { user } = useSession()
  const signOut = useSignOut()
  if (!user) return null
  return (
    <section aria-labelledby="account-title" className="flex max-w-160 flex-col gap-3">
      <div className="flex flex-col gap-0.75">
        <h2 id="account-title" className="text-15 font-semibold text-text-primary">Account</h2>
        <p className="text-13 text-text-tertiary">Access is by invitation</p>
      </div>
      <div className="flex flex-wrap items-center gap-3 rounded-12 border bg-surface p-3.5">
        <span aria-hidden className="flex size-9 shrink-0 items-center justify-center rounded-full bg-surface-muted text-13 font-semibold text-text-secondary">{user.initials}</span>
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="truncate text-14 font-semibold text-text-primary">{user.displayName}</span>
          <span className="truncate text-13 text-text-secondary">{user.email}</span>
          <span className="flex items-center gap-1.5 text-12 text-text-tertiary"><GoogleMark className="size-3" />Signed in with Google</span>
        </div>
        <Button variant="secondary" size="sm" disabled={signOut.isPending} onClick={() => { signOut.mutate() }}>
          <Icon icon={LogOut} />
          Sign out
        </Button>
      </div>
    </section>
  )
}
