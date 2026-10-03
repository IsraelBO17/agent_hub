import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { PageBody } from '@/components/layout/page-body'
import { ShellBar } from '@/components/layout/shell-bar'

/** Artifacts (`/artifacts`, Pencil g2nGvw, P1). A placeholder until it is built. */
export function ArtifactsPage() {
  return (
    <>
      <title>Artifacts · Agent Hub</title>
      <ShellBar onlyForNavigation />
      <PageBody kind="workspace">
        <PageHeader title="Artifacts" description="Everything your agents have made." />
        <EmptyState kind="empty" title="Coming later" description="Documents, code, apps and tables from every session." />
      </PageBody>
    </>
  )
}
