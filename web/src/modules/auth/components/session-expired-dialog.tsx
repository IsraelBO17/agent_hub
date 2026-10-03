// Design: Session expired (N8ysh): over the page, which stays as it was. "Continue with Google" ends the session
// here; the guard then goes to sign-in with `next`, and the draft is still in the composer afterwards.
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Dialog, DialogBody, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Check, Icon } from '@/components/ui/icon'
import { GoogleMark } from '@/modules/auth/components/google-mark'
import { clearExpired } from '@/modules/auth/utils/session-expired'
import { endLocalSession } from '@/service/auth'

/** Rendered (lazily) by RequireAuth while the session is expired. Default export, for lazy. */
export default function SessionExpiredDialog({ name }: { name: string | undefined }) {
  const queryClient = useQueryClient()
  const signInAgain = () => {
    clearExpired()
    endLocalSession(queryClient)
  }
  return (
    <Dialog open onOpenChange={(next) => { if (!next) clearExpired() }}>
      <DialogContent showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>Your sign-in has expired</DialogTitle>
          <DialogDescription>Continue with Google to keep going. Nothing is lost.</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <ul className="flex flex-col gap-2 text-13 text-text-secondary">
            {['Your unsent message stays in the composer', 'This session reopens where you left it'].map((line) => (
              <li key={line} className="flex items-center gap-2"><Icon icon={Check} className="size-3.5 text-online" />{line}</li>
            ))}
          </ul>
          {name ? <p className="text-12 text-text-tertiary">Signed in with Google as {name}</p> : null}
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={clearExpired}>Cancel</Button>
          <Button onClick={signInAgain}><GoogleMark className="size-3.5" />Continue with Google</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
