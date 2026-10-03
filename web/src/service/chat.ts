// Sessions and messages (contract Sessions, Messages; SEND_MESSAGE, D5, D11): the transcript, sending with its
// stream, one message (for polling), and Stop.
import { infiniteQueryOptions, queryOptions, type InfiniteData, type QueryClient } from '@tanstack/react-query'
import { applyEvent, toDomainMessage, upsertMessage, type Message } from '@/models/message'
import { toApiError, unwrap } from '@/service/api-error'
import { api } from '@/service/client'
import { streamStallMs } from '@/service/config'
import type { SendReplay, SessionSummary, StreamEvent } from '@/service/generated/schema'
import { readSse } from '@/service/sse'

export interface TranscriptPage { items: Message[]; nextBefore: number | null }
export type Transcript = InfiniteData<TranscriptPage, number | null>

export const chatKeys = {
  all: ['chat'] as const,
  transcript: (sessionId: string) => [...chatKeys.all, 'transcript', sessionId] as const,
  message: (messageId: string) => [...chatKeys.all, 'message', messageId] as const,
  session: (sessionId: string) => [...chatKeys.all, 'session', sessionId] as const,
}

const pageSize = 50

/** A session's messages, newest page first; older pages on demand (`before`). The stream keeps it current. */
export const transcriptQuery = (sessionId: string) =>
  infiniteQueryOptions({
    queryKey: chatKeys.transcript(sessionId),
    queryFn: async ({ pageParam, signal }): Promise<TranscriptPage> => {
      const page = await unwrap(api.GET('/v1/sessions/{sessionId}/messages', {
        params: { path: { sessionId }, query: { limit: pageSize, ...(pageParam === null ? {} : { before: pageParam }) } },
        signal,
      }))
      return { items: page.items.map(toDomainMessage), nextBefore: page.nextBefore }
    },
    initialPageParam: null as number | null,
    getNextPageParam: (last) => last.nextBefore,
    staleTime: Infinity, // the stream and polling keep it current
  })

/** One message, polled every 2 s while it is `streaming` and no stream is open (SEND_MESSAGE rule 9). */
export const messageQuery = (messageId: string) =>
  queryOptions({
    queryKey: chatKeys.message(messageId),
    queryFn: async ({ signal }) => toDomainMessage(await unwrap(api.GET('/v1/messages/{messageId}', { params: { path: { messageId } }, signal }))),
    staleTime: 0,
  })

/** The session's summary, as `run.started` reported it (its title, D21). Not fetched: there is no GET yet. */
export const sessionQuery = (sessionId: string) =>
  queryOptions<SessionSummary | null>({ queryKey: chatKeys.session(sessionId), queryFn: () => null, staleTime: Infinity, enabled: false })

/** All messages, oldest first. */
export const transcriptMessages = (t: { pages: TranscriptPage[] } | undefined) => (t ? [...t.pages].reverse().flatMap((p) => p.items) : [])

/** Changes the newest page (where new and streaming messages live), creating the transcript if needed. */
export function updateTranscript(qc: QueryClient, sessionId: string, fn: (messages: Message[]) => Message[]) {
  qc.setQueryData<Transcript>(chatKeys.transcript(sessionId), (prev) => {
    if (!prev) return { pages: [{ items: fn([]), nextBefore: null }], pageParams: [null] }
    const [newest, ...older] = prev.pages
    return { ...prev, pages: [{ items: fn(newest?.items ?? []), nextBefore: newest?.nextBefore ?? null }, ...older] }
  })
}

export const applyToTranscript = (qc: QueryClient, sessionId: string, events: StreamEvent[]) => {
  updateTranscript(qc, sessionId, (messages) => events.reduce(applyEvent, messages))
}

export const putMessage = (qc: QueryClient, sessionId: string, message: Message) => {
  updateTranscript(qc, sessionId, (messages) => upsertMessage(messages, message))
}

interface SendOptions {
  agentSlug: string
  /** Absent for the first message: the API creates the session (lazy creation, F03). */
  sessionId: string | null
  clientMessageId: string
  text: string
  signal: AbortSignal
  onEvent: (event: StreamEvent) => void
  /** A resend of an earlier `clientMessageId`: the existing rows, as JSON instead of a stream. */
  onReplay: (replay: SendReplay) => void
}

/**
 * Sends a message and reads its reply's stream to the end. Rejects with ApiError when the send is refused,
 * StreamStalledError after 45 s without bytes, or the signal's reason. The reply keeps running on the server
 * either way (D11); the caller polls.
 */
export async function sendMessage({ agentSlug, sessionId, clientMessageId, text, signal, onEvent, onReplay }: SendOptions) {
  const body = { clientMessageId, text }
  const headers = { Accept: 'text/event-stream, application/json' }
  const call = sessionId
    ? api.POST('/v1/sessions/{sessionId}/messages', { params: { path: { sessionId } }, body, headers, parseAs: 'stream', signal })
    : api.POST('/v1/agents/{slug}/sessions', { params: { path: { slug: agentSlug } }, body, headers, parseAs: 'stream', signal })
  const { data: stream, error, response } = await call
  if (error !== undefined || !stream) throw toApiError(error, response)
  if (response.headers.get('content-type')?.includes('application/json')) {
    onReplay(JSON.parse(await new Response(stream).text()) as SendReplay)
    return
  }
  await readSse(stream, { stallMs: streamStallMs, signal, onEvent: (e) => { onEvent(JSON.parse(e.data) as StreamEvent) } })
}

export async function stopMessage(messageId: string) {
  const { error, response } = await api.POST('/v1/messages/{messageId}/stop', { params: { path: { messageId } } })
  if (error !== undefined || !response.ok) throw toApiError(error, response)
}
