// New session and Session (`/agents/:agentId/:sessionId?`; SPEC: New session, Session; Pencil uBRCZ, wtDYF). One
// page for both, so a reply keeps streaming when the first message turns the URL into the session's.
import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { Link, useParams } from 'react-router'
import { PageBody } from '@/components/layout/page-body'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { cn } from '@/lib/utils'
import { textOf } from '@/models/message'
import { AgentMessage } from '@/modules/chat/components/agent-message'
import { AgentNotFound } from '@/modules/chat/components/agent-not-found'
import { ChatHeader } from '@/modules/chat/components/chat-header'
import { Composer } from '@/modules/chat/components/composer'
import { InlineError } from '@/modules/chat/components/inline-error'
import { JumpToLatest } from '@/modules/chat/components/jump-to-latest'
import { NewSessionHero } from '@/modules/chat/components/new-session-hero'
import { TranscriptSkeleton } from '@/modules/chat/components/transcript-skeleton'
import { UserMessage } from '@/modules/chat/components/user-message'
import { useChatRun } from '@/modules/chat/hooks/use-chat-run'
import { useDraft } from '@/modules/chat/hooks/use-draft'
import { useRouteAgent } from '@/modules/chat/hooks/use-route-agent'
import { useStickToBottom } from '@/modules/chat/hooks/use-stick-to-bottom'
import { ApiError } from '@/service/api-error'
import { sessionQuery, transcriptMessages, transcriptQuery } from '@/service/chat'
import { describeError } from '@/service/describe-error'

export function ChatPage() {
  const { sessionId } = useParams()
  const { slug, query: agentQuery, notFound } = useRouteAgent()
  const agent = agentQuery.data
  const transcript = useInfiniteQuery({ ...transcriptQuery(sessionId ?? ''), enabled: sessionId !== undefined })
  const messages = transcriptMessages(transcript.data)
  const summary = useQuery(sessionQuery(sessionId ?? '')).data
  const run = useChatRun({ agentSlug: slug, sessionId: sessionId ?? null, messages })
  const [text, setText] = useDraft(sessionId ?? `new:${slug}`)
  const input = useRef<HTMLTextAreaElement>(null)
  const top = useRef<HTMLDivElement>(null)
  const { scroller, content, atBottom, scrollToBottom } = useStickToBottom(messages[0]?.id)
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = transcript

  // Esc stops the reply (#9), unless something else (a menu, a dialog) handled it.
  const { running, stop } = run
  useEffect(() => {
    if (!running) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !e.defaultPrevented) void stop() }
    window.addEventListener('keydown', onKey)
    return () => { window.removeEventListener('keydown', onKey) }
  }, [running, stop])

  // Older pages load as the reader reaches the top.
  useEffect(() => {
    const el = top.current
    if (!el || !hasNextPage || typeof IntersectionObserver === 'undefined') return
    const observer = new IntersectionObserver(([entry]) => { if (entry?.isIntersecting && !isFetchingNextPage) void fetchNextPage() }, { root: scroller.current })
    observer.observe(el)
    return () => { observer.disconnect() }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage, scroller])

  if (notFound) return <AgentNotFound slug={slug} />

  const sessionMissing = transcript.error instanceof ApiError && transcript.error.status === 404
  const firstUser = messages.find((m) => m.role === 'user')
  const title = summary?.title ?? (firstUser ? textOf(firstUser) : sessionId ? 'Session' : 'New session')
  const latest = messages.at(-1)
  // A 401 means the session expired: its dialog says so instead.
  const refused = run.error && !(run.error instanceof ApiError && run.error.status === 401) ? describeError(run.error) : null

  const send = () => {
    const message = text.trim()
    if (!message) return
    scrollToBottom()
    void run.send(message, () => { setText('') })
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <title>{`${title} · Agent Hub`}</title>
      <ChatHeader title={title} />
      {sessionMissing ? (
        <PageBody kind="chat" className="justify-center">
          <EmptyState kind="not-found" title="Session not found" description="It doesn't exist, or it was deleted." action={<Button render={<Link to={`/agents/${slug}`} />}>New session</Button>} />
        </PageBody>
      ) : (
        <>
          <div ref={scroller} className="relative flex min-h-0 flex-1 flex-col overflow-y-auto">
            <div ref={content} className="flex flex-1 flex-col">
              <PageBody kind="chat" className={cn('gap-8 pb-4', !sessionId && 'justify-center')}>
                <div ref={top} aria-hidden />
                {!sessionId ? (agent ? <NewSessionHero agent={agent} onStarter={(prompt) => { setText(prompt); input.current?.focus() }} /> : null)
                  : transcript.isPending ? <TranscriptSkeleton />
                  : transcript.isError ? <EmptyState kind="error" title="Couldn't load this session" {...describeError(transcript.error)} onRetry={() => { void transcript.refetch() }} />
                  : null}
                {isFetchingNextPage ? <p className="text-center text-12 text-text-tertiary">Loading earlier messages…</p> : null}
                {messages.map((m) => m.role === 'user'
                  ? <UserMessage key={m.id} message={m} />
                  : <AgentMessage key={m.id} message={m} agent={agent} quietFor={m.id === latest?.id ? run.quietFor : 0} />)}
              </PageBody>
            </div>
          </div>
          <div className="relative mx-auto w-full max-w-(--layout-chat-width) px-4 pb-4">
            {!atBottom && messages.length > 0 ? (
              <div className="absolute -top-12 left-1/2 -translate-x-1/2">
                <JumpToLatest live={latest?.status === 'streaming'} onClick={() => { scrollToBottom('smooth') }} />
              </div>
            ) : null}
            {refused ? <InlineError tone="warning" className="mb-2.5" title="Your message wasn't sent" body={refused.message} reference={refused.requestId} /> : null}
            <Composer
              textareaRef={input}
              agentName={agent?.name ?? 'the agent'}
              disclaimer={agent?.disclaimer ?? null}
              showDisclaimer={agent !== undefined}
              text={text}
              onTextChange={(t) => { setText(t); if (run.error) run.clearError() }}
              onSend={send}
              onStop={() => { void run.stop() }}
              running={run.running && !run.sending}
              sending={run.sending}
              stopping={run.stopping}
              disabledReason={agent?.status === 'offline' ? `${agent.name} is offline. You can send when it's back.` : null}
            />
          </div>
        </>
      )}
    </div>
  )
}
