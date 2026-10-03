import { EmptyState } from '@/components/ui/empty-state'
import { PageBody } from '@/components/layout/page-body'
import { ChatHeader } from '@/modules/chat/components/chat-header'

/** A session (`/agents/:agentId/:sessionId`, Pencil wtDYF). A placeholder until issue #8 loads its messages. */
export function SessionPage() {
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
