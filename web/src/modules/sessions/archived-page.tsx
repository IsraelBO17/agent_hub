import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { PageBody } from '@/components/layout/page-body'
import { ShellBar } from '@/components/layout/shell-bar'

/** Archived sessions (`/archived`, Pencil HbIFz, P1). A placeholder until it is built. */
export function ArchivedPage() {
  return (
    <>
      <title>Archived sessions · Agent Hub</title>
      <ShellBar onlyForNavigation />
      <PageBody kind="workspace">
        <PageHeader title="Archived sessions" description="Hidden from the sidebar and search, kept until you delete them." />
        <EmptyState kind="empty" title="Coming later" description="Restore a session or delete it for good." />
      </PageBody>
    </>
  )
}
