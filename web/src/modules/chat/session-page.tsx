import { EmptyState } from '@/components/ui/empty-state'
import { PageBody } from '@/components/layout/page-body'
import { AgentNotFound } from '@/modules/chat/components/agent-not-found'
import { ChatHeader } from '@/modules/chat/components/chat-header'
import { useRouteAgent } from '@/modules/chat/hooks/use-route-agent'

/** A session (`/agents/:agentId/:sessionId`, Pencil wtDYF). A placeholder until issue #8 loads its messages. */
export function SessionPage() {
  const { slug, notFound } = useRouteAgent()
  if (notFound) return <AgentNotFound slug={slug} />
  return (
    <>
      <title>Session · Agent Hub</title>
      <ChatHeader title="Session" />
      <PageBody kind="chat" className="justify-center">
        <EmptyState kind="empty" title="Messages appear here" description="The conversation and its streaming replies arrive with chat." />
      </PageBody>
    </>
  )
}
