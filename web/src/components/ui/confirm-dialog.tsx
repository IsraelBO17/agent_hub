// Design: Confirm Dialog (i3B1e), used for Delete all only (session delete uses undo; profile Exceptions).
// The confirmation for every irreversible action (standard §8.5). Controlled by its owner's mutation:
// it stays open with a spinner while `pending`, shows `error` and stays open on failure, and the owner
// closes it on success.
import {
  AlertDialog, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Icon, Loader2 } from '@/components/ui/icon'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel: string
  onConfirm: () => void
  pending: boolean
  error?: string | null | undefined
}

export function ConfirmDialog({ open, onOpenChange, title, description, confirmLabel, onConfirm, pending, error }: Props) {
  return (
    <AlertDialog open={open} onOpenChange={(next) => { if (!pending) onOpenChange(next) }}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        {error ? <p role="alert" className="text-13 text-danger">{error}</p> : null}
        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>Cancel</AlertDialogCancel>
          <Button variant="danger" disabled={pending} aria-busy={pending} onClick={onConfirm}>
            {pending ? <Icon icon={Loader2} className="animate-spin" /> : null}
            {confirmLabel}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
