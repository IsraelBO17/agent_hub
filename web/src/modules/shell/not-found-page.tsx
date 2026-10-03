import { Link } from 'react-router'
import { PageBody } from '@/components/layout/page-body'
import { buttonVariants } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'

/** An unknown address (adapted from Session not found, Pencil H7ZqtC / F11.19). */
export function NotFoundPage() {
  return (
    <PageBody kind="hub">
      <title>Page not found · Agent Hub</title>
      <PageHeader title="Page not found" />
      <EmptyState kind="not-found" title="There's nothing at this address" action={<Link to="/" className={buttonVariants({ variant: 'secondary' })}>Back to agents</Link>} />
    </PageBody>
  )
}
