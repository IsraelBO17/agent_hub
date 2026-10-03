import { useParams } from 'react-router'
import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { PageBody } from '@/components/layout/page-body'

/** Agent detail (`/agents/:agentId/about`, Pencil x05s4W, P1). A placeholder until it is built. */
export function AgentDetailPage() {
  const { agentId = '' } = useParams()
  return (
    <PageBody kind="hub">
      <title>About this agent · Agent Hub</title>
      <PageHeader title="About this agent" description={`Agent ${agentId}`} />
      <EmptyState kind="empty" title="Coming later" description="What this agent can do, its tools and its versions." />
    </PageBody>
  )
}
