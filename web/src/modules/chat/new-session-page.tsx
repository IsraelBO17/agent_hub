import { EmptyState } from '@/components/ui/empty-state'
import { PageBody } from '@/components/layout/page-body'
import { ChatHeader } from '@/modules/chat/components/chat-header'

/** New session (`/agents/:agentId`, Pencil uBRCZ). A placeholder until issue #8 adds starters and the composer. */
export function NewSessionPage() {
  return (
    <>
      <title>New session · Agent Hub</title>
      <ChatHeader title="New session" />
      <PageBody kind="chat" className="justify-center">
        <EmptyState kind="empty" title="What can I help you with today?" description="Starter prompts and the composer arrive with chat." />
      </PageBody>
    </>
  )
}
