// MSW handlers for sending, streaming, reloading, polling and Stop (contract Sessions, Messages; SEND_MESSAGE).
import { http, HttpResponse } from 'msw/http'
import { chatStore, newSession, startRun, type ReplyScript } from '@/mocks/data/chat'
import { seedAgents } from '@/mocks/data/agents'
import { problem } from '@/mocks/responses'
import type { SendMessageRequest, StreamEvent } from '@/service/generated/schema'

const enc = new TextEncoder()
const frame = (e: StreamEvent) => `id: ${e.messageId}:${String(e.n)}\nevent: ${e.type}\ndata: ${JSON.stringify(e)}\n\n`

/** Streams a run: `run.started`, then whatever the agent emits, until it ends (or the client goes away). */
function streamRun(started: StreamEvent, assistantId: string) {
  return new HttpResponse(new ReadableStream<Uint8Array>({
    start(c) {
      c.enqueue(enc.encode(frame(started)))
      chatStore.listeners.set(assistantId, (event) => {
        try {
          if (event) c.enqueue(enc.encode(frame(event)))
          else c.close()
        } catch { chatStore.listeners.delete(assistantId) } // the client hung up; the agent keeps going (D11)
      })
    },
    cancel() { chatStore.listeners.delete(assistantId) },
  }), { headers: { 'content-type': 'text/event-stream', 'cache-control': 'no-cache' } })
}

function replay(clientMessageId: string) {
  const known = chatStore.byClientId.get(clientMessageId)
  if (!known) return null
  const session = chatStore.sessions.get(known.sessionId)
  if (!session) return null
  const userMessage = session.messages.find((m) => m.id === known.userId)
  const assistantMessage = session.messages.find((m) => m.id === known.assistantId)
  if (!userMessage || !assistantMessage) return null
  return HttpResponse.json({ session: session.summary, userMessage, assistantMessage })
}

const offline = (slug: string) => seedAgents().find((a) => a.slug === slug)?.status === 'offline'

export const chatHandlers = (script: ReplyScript = {}) => [
  http.post<{ slug: string }, SendMessageRequest>('*/v1/agents/:slug/sessions', async ({ request, params }) => {
    const body = await request.json()
    const again = replay(body.clientMessageId)
    if (again) return again
    if (!seedAgents().some((a) => a.slug === params.slug)) return problem(404, 'agent_not_found', 'Agent not found')
    if (offline(params.slug)) return problem(503, 'agent_unavailable', 'This agent is offline')
    const session = newSession(params.slug, body.text ?? '')
    const { started, assistant } = startRun(session, body.clientMessageId, body.text ?? '', script)
    return streamRun(started, assistant.id)
  }),
  http.post<{ sessionId: string }, SendMessageRequest>('*/v1/sessions/:sessionId/messages', async ({ request, params }) => {
    const body = await request.json()
    const again = replay(body.clientMessageId)
    if (again) return again
    const session = chatStore.sessions.get(params.sessionId)
    if (!session) return problem(404, 'session_not_found', 'Session not found')
    if (session.messages.some((m) => m.status === 'streaming')) return problem(409, 'run_in_progress', 'A reply is still running in this session')
    const { started, assistant } = startRun(session, body.clientMessageId, body.text ?? '', script)
    return streamRun(started, assistant.id)
  }),
  http.get<{ sessionId: string }>('*/v1/sessions/:sessionId/messages', ({ params }) => {
    const session = chatStore.sessions.get(params.sessionId)
    if (!session) return problem(404, 'session_not_found', 'Session not found')
    return HttpResponse.json({ items: structuredClone(session.messages), nextBefore: null })
  }),
  http.get<{ messageId: string }>('*/v1/messages/:messageId', ({ params }) => {
    for (const s of chatStore.sessions.values()) {
      const m = s.messages.find((x) => x.id === params.messageId)
      if (m) return HttpResponse.json(structuredClone(m))
    }
    return problem(404, 'message_not_found', 'Message not found')
  }),
  http.post<{ messageId: string }>('*/v1/messages/:messageId/stop', ({ params }) => {
    chatStore.cancelled.add(params.messageId)
    return new HttpResponse(null, { status: 202 })
  }),
]
