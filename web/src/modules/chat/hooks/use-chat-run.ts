// Sending a message and following its reply (SEND_MESSAGE; standard §12). Events go into the transcript's cache,
// batched per frame. If the stream stalls (45 s without bytes) or drops after the reply started, or the reply is
// found still running on load, the message is polled every 2 s until it ends (rule 9; the agent keeps running,
// D11). Stop calls the API, then stops reading and polls for the final "stopped" message (P4).
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { keepFocus } from '@/hooks/use-focus-on-navigate'
import { reportError } from '@/lib/monitoring'
import { toDomainMessage, type Message } from '@/models/message'
import { applyToTranscript, chatKeys, messageQuery, putMessage, sendMessage, sessionQuery, stopMessage } from '@/service/chat'
import type { StreamEvent } from '@/service/generated/schema'
import { StreamStalledError } from '@/service/sse'
import { batchPerFrame } from '@/utils/batch-per-frame'

/** After this long without events (pings don't count), the reply says "Still working" (SEND_MESSAGE timers). */
export const stillWorkingMs = 60_000
const pollMs = 2_000

type Phase = 'idle' | 'sending' | 'streaming' | 'stopping' | 'polling'

interface Options { agentSlug: string; sessionId: string | null; messages: Message[] }

export function useChatRun({ agentSlug, sessionId, messages }: Options) {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [phase, setPhase] = useState<Phase>('idle')
  const [runId, setRunId] = useState<string | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [lastEventAt, setLastEventAt] = useState(0)
  const [now, setNow] = useState(0)
  const controller = useRef<AbortController | null>(null)

  useEffect(() => () => controller.current?.abort(), []) // leaving the page stops reading (the reply keeps running)

  const latest = messages.at(-1)
  // A reply that was already running when the page opened (another tab, a reload, a dropped stream).
  const orphan = phase === 'idle' && latest?.role === 'assistant' && latest.status === 'streaming' ? latest.id : null
  const pollTarget = phase === 'polling' || phase === 'stopping' ? runId : orphan
  const target = messages.find((m) => m.id === pollTarget)
  const targetRunning = target ? target.status === 'streaming' : pollTarget !== null

  useQuery({
    queryKey: [...chatKeys.message(pollTarget ?? ''), 'poll'],
    queryFn: async () => {
      const message = await qc.query({ ...messageQuery(pollTarget ?? ''), staleTime: 0 })
      if (sessionId) putMessage(qc, sessionId, message)
      return message
    },
    enabled: pollTarget !== null && sessionId !== null && targetRunning,
    refetchInterval: pollMs,
    refetchIntervalInBackground: false,
  })

  useEffect(() => {
    if (phase !== 'streaming') return
    const timer = setInterval(() => { setNow(Date.now()) }, 5_000)
    return () => { clearInterval(timer) }
  }, [phase])

  const send = useCallback(async (text: string, onAccepted: () => void) => {
    controller.current?.abort()
    const abort = new AbortController()
    controller.current = abort
    setError(null)
    setPhase('sending')
    let sid = sessionId
    const started = { replyId: null as string | null }
    const accept = (newSessionId: string | null, replyId: string) => {
      sid = newSessionId ?? sid
      started.replyId = replyId
      setRunId(replyId)
      onAccepted()
      if (!sessionId && sid) void navigate(`/agents/${agentSlug}/${sid}`, { replace: true, state: keepFocus })
    }
    const queue = batchPerFrame<StreamEvent>((events) => {
      if (sid) applyToTranscript(qc, sid, events)
      setLastEventAt(Date.now())
    })
    try {
      await sendMessage({
        agentSlug, sessionId, clientMessageId: crypto.randomUUID(), text, signal: abort.signal,
        onEvent: (event) => {
          if (event.type !== 'run.started') { queue.push(event); return }
          if (event.session) qc.setQueryData(sessionQuery(event.session.id).queryKey, event.session)
          accept(event.session?.id ?? null, event.assistantMessage.id)
          if (sid) applyToTranscript(qc, sid, [event])
          setLastEventAt(Date.now())
          setNow(Date.now())
          setPhase('streaming')
        },
        onReplay: (replay) => {
          qc.setQueryData(sessionQuery(replay.session.id).queryKey, replay.session)
          accept(replay.session.id, replay.assistantMessage.id)
          putMessage(qc, replay.session.id, toDomainMessage(replay.userMessage))
          putMessage(qc, replay.session.id, toDomainMessage(replay.assistantMessage))
          setPhase(replay.assistantMessage.status === 'streaming' ? 'polling' : 'idle')
        },
      })
      queue.flushNow()
      setPhase((p) => (p === 'polling' ? p : 'idle'))
    } catch (e) {
      if (abort.signal.aborted) { queue.cancel(); return } // left the page, sent again, or Stop
      queue.flushNow()
      if (started.replyId) {
        // The reply started, then the stream went away: the agent is still running, so follow it by polling.
        if (e instanceof StreamStalledError) reportError(e, { feature: 'chat', stream: 'reply' })
        setPhase('polling')
      } else {
        setPhase('idle')
        setError(e) // refused: nothing was saved, and the draft stays in the composer
      }
    }
  }, [agentSlug, navigate, qc, sessionId])

  const stop = useCallback(async () => {
    const id = runId ?? orphan
    if (!id) return
    setPhase('stopping')
    setRunId(id)
    try {
      await stopMessage(id)
    } catch (e) {
      setError(e)
    }
    controller.current?.abort()
    setPhase('polling') // the final "stopped" message arrives within about 2 s (P4)
  }, [orphan, runId])

  const running = phase === 'sending' || phase === 'streaming' || phase === 'stopping' || (pollTarget !== null && targetRunning)
  return {
    send,
    stop,
    /** A reply is being sent, streamed or followed: the composer shows Stop instead of Send. */
    running,
    stopping: phase === 'stopping',
    sending: phase === 'sending',
    /** The send was refused (ApiError) or Stop failed. */
    error,
    clearError: () => { setError(null) },
    /** Ms since the last event, once over a minute (pings don't count): the reply shows "Still working". */
    quietFor: phase === 'streaming' && now - lastEventAt >= stillWorkingMs ? now - lastEventAt : 0,
  }
}
