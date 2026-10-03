import { Link } from 'react-router'
import { buttonVariants } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'

export function NotFoundPage() {
  return (
    <>
      <title>Page not found · Agent Hub</title>
      <PageHeader title="Page not found" />
      <EmptyState kind="not-found" title="There's nothing at this address" action={<Link to="/" className={buttonVariants({ variant: 'outline' })}>Back to agents</Link>} />
    </>
  )
}
