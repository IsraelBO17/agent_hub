import { describe, expect, it } from 'vitest'
import { applyEvent, textOf, thoughtSeconds, toDomainMessage, type Message } from '@/models/message'
import type { Message as MessageWire, StreamEvent } from '@/service/generated/schema'

const wire = (over: Partial<MessageWire>): MessageWire => ({
  id: 'a1', sessionId: 's1', seq: 2, role: 'assistant', status: 'streaming', blocks: [], clientMessageId: null, replyToId: null,
  agentVersion: null, error: null, usage: null, feedback: null, createdAt: '2026-10-03T10:00:00Z', startedAt: null, completedAt: null, ...over,
})
const user = wire({ id: 'u1', seq: 1, role: 'user', status: 'complete', blocks: [{ id: 'b0', type: 'text', text: 'Hi' }] })
const run = (events: Omit<StreamEvent, 'messageId' | 'n'>[], start: Message[] = []) =>
  events.reduce<Message[]>((ms, e, i) => applyEvent(ms, { ...e, messageId: 'a1', n: i + 1 } as StreamEvent), start)

const first = (ms: Message[]) => {
  const m = ms[0]
  if (!m) throw new Error('no message')
  return m
}

describe('applyEvent', () => {
  it('adds the saved messages on run.started, in seq order', () => {
    const ms = run([{ type: 'run.started', userMessage: user, assistantMessage: wire({}) } as never])
    expect(ms.map((m) => m.id)).toEqual(['u1', 'a1'])
  })

  it('builds a reply from blocks and deltas, then takes the final message', () => {
    const ms = run([
      { type: 'run.started', assistantMessage: wire({}) } as never,
      { type: 'block.started', index: 0, block: { id: 't', type: 'text', text: '' } } as never,
      { type: 'block.delta', blockId: 't', text: 'Hello' } as never,
      { type: 'block.delta', blockId: 't', text: ', world' } as never,
    ])
    expect(textOf(first(ms))).toBe('Hello, world')
    const done = applyEvent(ms, { type: 'run.completed', messageId: 'a1', n: 9, message: wire({ status: 'complete', blocks: [{ id: 't', type: 'text', text: 'Hello, world.' }] }) })
    expect(done[0]?.status).toBe('complete')
    expect(textOf(first(done))).toBe('Hello, world.')
  })

  it('replaces a block on block.completed and keeps the block order', () => {
    const ms = run([
      { type: 'run.started', assistantMessage: wire({}) } as never,
      { type: 'block.started', index: 0, block: { id: 'k', type: 'thinking', text: '', startedAt: '2026-10-03T10:00:00Z', endedAt: null } } as never,
      { type: 'block.started', index: 1, block: { id: 't', type: 'text', text: 'x' } } as never,
      { type: 'block.completed', block: { id: 'k', type: 'thinking', text: 'Plan', startedAt: '2026-10-03T10:00:00Z', endedAt: '2026-10-03T10:00:06Z' } } as never,
    ])
    const blocks = first(ms).blocks
    expect(blocks.map((b) => b.type)).toEqual(['thinking', 'text'])
    const thinking = blocks[0]
    expect(thinking?.type === 'thinking' && thoughtSeconds(thinking)).toBe(6)
  })

  it('times a thought cut short by the end of the reply', () => {
    const thinking = { id: 'k', type: 'thinking' as const, text: '', startedAt: new Date('2026-10-03T10:00:00Z'), endedAt: null }
    expect(thoughtSeconds(thinking)).toBeNull()
    expect(thoughtSeconds(thinking, new Date('2026-10-03T10:00:03Z'))).toBe(3)
  })

  it('shows an unknown block type as unsupported instead of failing', () => {
    const m = toDomainMessage(wire({ blocks: [{ id: 'z', type: 'chart' } as never] }))
    expect(m.blocks[0]).toEqual({ id: 'z', type: 'unsupported', kind: 'chart' })
  })

  it('ignores events it does not draw yet', () => {
    const ms = run([{ type: 'run.started', assistantMessage: wire({}) } as never])
    expect(applyEvent(ms, { type: 'artifact.delta', messageId: 'a1', n: 2 } as never)).toBe(ms)
  })
})
