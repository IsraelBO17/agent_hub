// Design: Agent not found (the States board; mobile V97EP): an unknown or removed agent in the URL.
import { Link, useNavigate } from 'react-router'
import { PageBody } from '@/components/layout/page-body'
import { Button, buttonVariants } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'

export function AgentNotFound({ slug }: { slug: string }) {
  const navigate = useNavigate()
  return (
    <PageBody kind="chat" className="justify-center">
      <title>Agent not found · Agent Hub</title>
      <h1 tabIndex={-1} className="sr-only">Agent not found</h1>
      <EmptyState
        kind="not-found"
        title="Agent not found"
        description={`No agent with the id “${slug}” is registered. It may have been renamed or removed from the catalog.`}
        action={<>
          <Link to="/" className={buttonVariants()}>Browse agents</Link>
          <Button variant="secondary" onClick={() => { void navigate(-1) }}>Go back</Button>
        </>}
      />
    </PageBody>
  )
}
