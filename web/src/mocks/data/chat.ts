// The mock API's sessions and messages, and a scripted "agent" that keeps running whether or not anyone reads its
// stream (D11), so polling can pick a reply up. Synthetic content only.
import type { Block, Message, SessionSummary, StreamEvent } from '@/service/generated/schema'
import { seedAgents } from '@/mocks/data/agents'

interface StoredSession { summary: SessionSummary; messages: Message[] }
type Listener = (event: StreamEvent | null) => void

export interface ReplyScript { failAfterThinking?: boolean; stallStreamAfter?: number; gapMs?: number }

export const chatStore = {
  sessions: new Map<string, StoredSession>(),
  byClientId: new Map<string, { sessionId: string; userId: string; assistantId: string }>(),
  cancelled: new Set<string>(),
  listeners: new Map<string, Listener>(),
}

// In the browser the sessions are kept in sessionStorage, so a reload in mock mode finds them (as the real API
// would). A reply that was running when the page went away is "interrupted": the mock agent ran in the page.
const saved = 'agent-hub:mock-chat'
const persist = import.meta.env.MODE !== 'test'

export function saveChatStore() {
  if (!persist) return
  try { sessionStorage.setItem(saved, JSON.stringify([...chatStore.sessions])) } catch { /* mock only: best effort */ }
}

function loadChatStore() {
  if (!persist) return
  try {
    const entries = JSON.parse(sessionStorage.getItem(saved) ?? '[]') as [string, StoredSession][]
    for (const [id, session] of entries) {
      for (const m of session.messages) {
        if (m.status !== 'streaming') continue
        m.status = 'interrupted'
        m.completedAt = now()
        m.error = { type: 'about:blank', title: "The reply didn't finish", status: 500, code: 'run_interrupted', requestId: 'req_mock_reload', retryable: true }
      }
      session.summary.isRunning = false
      chatStore.sessions.set(id, session)
    }
  } catch { /* nothing saved */ }
}

export function resetChatStore() {
  chatStore.sessions.clear()
  chatStore.byClientId.clear()
  chatStore.cancelled.clear()
  chatStore.listeners.clear()
}

const now = () => new Date().toISOString()
loadChatStore()
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

export function agentRef(slug: string) {
  const a = seedAgents().find((x) => x.slug === slug)
  if (!a) return null
  return { id: a.id, slug: a.slug, name: a.name, icon: a.icon, color: a.color, status: a.status, stage: a.stage, retired: false }
}

export function newSession(slug: string, title: string): StoredSession {
  const ref = agentRef(slug)
  if (!ref) throw new Error(`no agent ${slug}`)
  const id = crypto.randomUUID()
  const session: StoredSession = {
    summary: { id, agent: ref, title: title.slice(0, 80), titleSource: 'auto', createdAt: now(), lastMessageAt: now(), pinnedAt: null, archivedAt: null, isRunning: false, pendingApprovals: 0, messageCount: 0 },
    messages: [],
  }
  chatStore.sessions.set(id, session)
  return session
}

function message(sessionId: string, seq: number, role: 'user' | 'assistant', blocks: Block[], status: Message['status']): Message {
  return { id: crypto.randomUUID(), sessionId, seq, role, status, blocks, clientMessageId: null, replyToId: null, agentVersion: null, error: null, usage: null, feedback: null, createdAt: now(), startedAt: role === 'assistant' ? now() : null, completedAt: status === 'streaming' ? null : now() }
}

/** Saves the user message and an empty streaming reply (SEND_MESSAGE rule 1), then runs the agent. */
export function startRun(session: StoredSession, clientMessageId: string, text: string, script: ReplyScript) {
  const seq = session.messages.length
  const user = { ...message(session.summary.id, seq + 1, 'user', [{ id: crypto.randomUUID(), type: 'text', text }], 'complete'), clientMessageId }
  const assistant = message(session.summary.id, seq + 2, 'assistant', [], 'streaming')
  session.messages.push(user, assistant)
  session.summary.isRunning = true
  chatStore.byClientId.set(clientMessageId, { sessionId: session.summary.id, userId: user.id, assistantId: assistant.id })
  const started: StreamEvent = { type: 'run.started', messageId: assistant.id, n: 1, session: session.summary, userMessage: user, assistantMessage: assistant }
  saveChatStore()
  void runAgent(session, assistant, text, script)
  return { started, assistant }
}

const reply = (question: string) =>
  `Here is what I found about **${question.slice(0, 40)}**:\n\n- The page says the answer has three parts.\n- Each part links to its source.\n\nAsk me to dig into any of them.`

async function runAgent(session: StoredSession, assistant: Message, question: string, script: ReplyScript) {
  let n = 1
  const gap = script.gapMs ?? 40
  const emit = async (event: Omit<StreamEvent, 'messageId' | 'n'>) => {
    n += 1
    if (script.stallStreamAfter !== undefined && n > script.stallStreamAfter) chatStore.listeners.delete(assistant.id)
    chatStore.listeners.get(assistant.id)?.({ ...event, messageId: assistant.id, n } as StreamEvent)
    await sleep(gap)
  }
  const finish = async (status: Message['status'], type: 'run.completed' | 'run.stopped' | 'run.failed', error?: Message['error']) => {
    assistant.status = status
    assistant.completedAt = now()
    assistant.error = error ?? null
    assistant.usage = { inputTokens: 812, outputTokens: 164 }
    session.summary.isRunning = false
    saveChatStore()
    await emit(type === 'run.failed' ? { type, message: assistant, error: error ?? null } as never : { type, message: assistant } as never)
    chatStore.listeners.get(assistant.id)?.(null)
    chatStore.listeners.delete(assistant.id)
  }
  const stopped = () => chatStore.cancelled.has(assistant.id)

  const thinking = { id: crypto.randomUUID(), type: 'thinking' as const, text: '', startedAt: now(), endedAt: null as string | null }
  assistant.blocks.push(thinking)
  await emit({ type: 'block.started', index: 0, block: { ...thinking } } as never)
  for (const word of 'The user wants a short answer with sources. I should read the page first.'.split(/(?<= )/)) {
    if (stopped()) return finish('stopped', 'run.stopped')
    thinking.text += word
    await emit({ type: 'block.delta', blockId: thinking.id, text: word } as never)
  }
  thinking.endedAt = new Date(Date.now() + 6000).toISOString()
  await emit({ type: 'block.completed', block: { ...thinking } } as never)
  if (script.failAfterThinking) {
    return finish('failed', 'run.failed', { type: 'about:blank', title: 'The agent failed while answering', status: 500, code: 'agent_error', requestId: 'req_agent_error', retryable: true })
  }

  const tool = { id: crypto.randomUUID(), type: 'tool' as const, toolCall: { id: crypto.randomUUID(), toolUseId: 'tooluse_1', name: 'fetch_url', status: 'running' as const, summary: null as string | null, input: { url: 'https://example.com/report' }, output: null as unknown, error: null, startedAt: now(), completedAt: null as string | null } }
  assistant.blocks.push(tool)
  await emit({ type: 'block.started', index: 1, block: structuredClone(tool) } as never)
  await sleep(gap * 4)
  if (stopped()) return finish('stopped', 'run.stopped')
  tool.toolCall = { ...tool.toolCall, status: 'succeeded' as never, summary: 'Read 1 page', output: { title: 'Example report', words: 1240 }, completedAt: now() }
  await emit({ type: 'block.completed', block: structuredClone(tool) } as never)

  const text = { id: crypto.randomUUID(), type: 'text' as const, text: '' }
  assistant.blocks.push(text)
  await emit({ type: 'block.started', index: 2, block: { ...text } } as never)
  for (const word of reply(question).split(/(?<= )/)) {
    if (stopped()) return finish('stopped', 'run.stopped')
    text.text += word
    await emit({ type: 'block.delta', blockId: text.id, text: word } as never)
  }
  await emit({ type: 'block.completed', block: { ...text } } as never)
  return finish('complete', 'run.completed')
}
