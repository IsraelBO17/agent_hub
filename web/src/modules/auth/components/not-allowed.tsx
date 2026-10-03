// Design: Sign in · Not allowed (zte2v; mobile dLCVX). Also used, with its own words, for a turned-off account
// (not drawn; logged in docs/decisions.md).
import { Button } from '@/components/ui/button'
import { Icon, Orbit, Repeat, UserX } from '@/components/ui/icon'

interface Props { reason: 'not-invited' | 'disabled'; email: string | undefined; onUseAnotherAccount: () => void }

export function NotAllowed({ reason, email, onUseAnotherAccount }: Props) {
  const invited = reason === 'not-invited'
  return (
    <div className="flex w-full max-w-90 flex-col items-center gap-4 text-center">
      <span className="flex size-10 items-center justify-center rounded-11 bg-accent text-on-accent"><Icon icon={Orbit} className="size-5.5" /></span>
      <span className="flex size-12 items-center justify-center rounded-full bg-danger-soft text-danger"><Icon icon={UserX} className="size-5.5" /></span>
      <h1 tabIndex={-1} className="text-20 leading-tight font-semibold text-text-primary outline-none">
        {invited ? "This Google account doesn't have access to Agent Hub" : 'This account has been turned off'}
      </h1>
      {email ? (
        <span className="flex items-center gap-2 rounded-full border bg-surface py-1.5 pr-3 pl-1.5">
          <span aria-hidden className="flex size-6 items-center justify-center rounded-full bg-surface-muted text-12 font-semibold text-text-secondary">{email.slice(0, 1).toUpperCase()}</span>
          <span className="text-14 text-text-primary">{email}</span>
        </span>
      ) : null}
      <p className="text-14 leading-normal text-text-secondary">
        {invited ? 'Access is by invitation. Sign in with an account that has been invited.' : 'Ask the person who invited you to turn it back on, or sign in with another account.'}
      </p>
      <Button variant="secondary" className="h-11 w-full text-14" onClick={onUseAnotherAccount}>
        <Icon icon={Repeat} />
        Use a different account
      </Button>
    </div>
  )
}
