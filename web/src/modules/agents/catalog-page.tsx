import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { PageBody } from '@/components/layout/page-body'

/** The catalog (`/`, Pencil PBQLh). A placeholder until issue #7 loads the agents. */
export function CatalogPage() {
  return (
    <PageBody kind="hub">
      <title>Your agents · Agent Hub</title>
      <PageHeader title="Your agents" description="Pick an agent to start a new session." />
      <EmptyState kind="empty" title="Agents appear here soon" description="The catalog will list every registered agent, with where you left off." />
    </PageBody>
  )
}
