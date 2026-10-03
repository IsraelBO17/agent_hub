import { AppHeader } from '@/components/layout/app-header'
import { EmptyState } from '@/components/ui/empty-state'
import { PageBody } from '@/components/layout/page-body'
import { PageHeader } from '@/components/ui/page-header'

/** A shared session (`/s/:shareId`, Pencil q1bvDq, P1): public and read-only, without the app's shell. */
export function SharedSessionPage() {
  return (
    <div className="flex min-h-dvh flex-col">
      <title>Shared session · Agent Hub</title>
      <AppHeader brand={<span className="text-15 font-semibold text-text-primary">Agent Hub</span>} />
      <main id="main" tabIndex={-1} className="flex flex-1 flex-col outline-none">
        <PageBody kind="chat">
          <PageHeader title="Shared session" />
          <EmptyState kind="empty" title="Coming later" description="A read-only copy of a session someone shared with you." />
        </PageBody>
      </main>
    </div>
  )
}
