// A chat message (contract `Message`) and its blocks, as the transcript shows them (F04, D10). The closed set of
// block renderers (profile: Content types): text, thinking and tool are drawn in #8; any other type is
// "unsupported" until its issue, never a crash.
import type { Block as BlockWire, Message as MessageWire, StreamEvent, ToolCall as ToolCallWire } from '@/service/generated/schema'

export type MessageStatus = MessageWire['status']

export interface ToolCall {
  name: string
  status: ToolCallWire['status']
  summary: string | null
  input: unknown
  output: unknown
  error: string | null
  startedAt: Date
  completedAt: Date | null
}

export type Block =
  | { id: string; type: 'text'; text: string }
  | { id: string; type: 'thinking'; text: string; startedAt: Date; endedAt: Date | null }
  | { id: string; type: 'tool'; toolCall: ToolCall }
  | { id: string; type: 'unsupported'; kind: string }

export interface MessageError { title: string; code: string; requestId: string | null }

export interface Message {
  id: string
  seq: number
  role: 'user' | 'assistant'
  status: MessageStatus
  blocks: Block[]
  error: MessageError | null
  createdAt: Date
  completedAt: Date | null
}

const date = (v: string) => new Date(v)

export function toDomainBlock(b: BlockWire): Block {
  switch (b.type) {
    case 'text': return { id: b.id, type: 'text', text: b.text }
    case 'thinking': return { id: b.id, type: 'thinking', text: b.text, startedAt: date(b.startedAt), endedAt: b.endedAt ? date(b.endedAt) : null }
    case 'tool': {
      const t = b.toolCall
      return { id: b.id, type: 'tool', toolCall: { name: t.name, status: t.status, summary: t.summary, input: t.input, output: t.output, error: t.error ?? null, startedAt: date(t.startedAt), completedAt: t.completedAt ? date(t.completedAt) : null } }
    }
    default: return { id: b.id, type: 'unsupported', kind: b.type }
  }
}

export function toDomainMessage(m: MessageWire): Message {
  return {
    id: m.id,
    seq: m.seq,
    role: m.role,
    status: m.status,
    blocks: m.blocks.map(toDomainBlock),
    error: m.error ? { title: m.error.title, code: m.error.code, requestId: m.error.requestId } : null,
    createdAt: date(m.createdAt),
    completedAt: m.completedAt ? date(m.completedAt) : null,
  }
}

/** The plain text of a message (its text blocks), e.g. for a session's title or Copy. */
export const textOf = (m: Message) => m.blocks.flatMap((b) => (b.type === 'text' ? [b.text] : [])).join('\n\n')

/** Adds or replaces a message, keeping the transcript ordered by `seq`. */
export function upsertMessage(messages: Message[], message: Message): Message[] {
  const rest = messages.filter((m) => m.id !== message.id)
  return [...rest, message].sort((a, b) => a.seq - b.seq)
}

const updateBlocks = (m: Message, fn: (blocks: Block[]) => Block[]): Message => ({ ...m, blocks: fn(m.blocks) })

/** Applies one stream event to the transcript (SEND_MESSAGE; contract StreamEvent). Pure. */
export function applyEvent(messages: Message[], event: StreamEvent): Message[] {
  switch (event.type) {
    case 'run.started': {
      let next = messages
      if (event.userMessage) next = upsertMessage(next, toDomainMessage(event.userMessage))
      return upsertMessage(next, toDomainMessage(event.assistantMessage))
    }
    case 'block.started':
      return messages.map((m) => (m.id !== event.messageId ? m : updateBlocks(m, (blocks) => {
        const block = toDomainBlock(event.block)
        const copy = blocks.filter((b) => b.id !== block.id)
        copy.splice(Math.min(event.index, copy.length), 0, block)
        return copy
      })))
    case 'block.delta':
      return messages.map((m) => (m.id !== event.messageId ? m : updateBlocks(m, (blocks) => blocks.map((b) =>
        b.id === event.blockId && (b.type === 'text' || b.type === 'thinking') ? { ...b, text: b.text + event.text } : b))))
    case 'block.updated':
    case 'block.completed':
      return messages.map((m) => (m.id !== event.messageId ? m : updateBlocks(m, (blocks) => {
        const block = toDomainBlock(event.block)
        return blocks.some((b) => b.id === block.id) ? blocks.map((b) => (b.id === block.id ? block : b)) : [...blocks, block]
      })))
    case 'run.completed':
    case 'run.stopped':
    case 'run.failed':
    case 'run.awaiting_approval':
      return upsertMessage(messages, toDomainMessage(event.message))
    default:
      return messages // artifact.delta and anything newer: not drawn yet
  }
}

/**
 * Seconds a thinking block took, for "Thought for Ns". A reply that ended mid-thought (stopped, failed) has no
 * `endedAt`; its end is the reply's. Null while still thinking.
 */
export function thoughtSeconds(b: Extract<Block, { type: 'thinking' }>, replyEndedAt: Date | null = null) {
  const end = b.endedAt ?? replyEndedAt
  return end ? Math.max(1, Math.round((end.getTime() - b.startedAt.getTime()) / 1000)) : null
}
