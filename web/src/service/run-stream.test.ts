// The typed client and the SSE reader against Agent Hub's contract (issue #4): a reply to
// `POST /v1/sessions/{sessionId}/messages` arrives as `StreamEvent`s, and a stream that goes quiet for
// `streamStallMs` (45 s: three missed 15 s keep-alives, WEB_PROFILE Streams) is abandoned. The send flow
// itself (cache, polling after a stall, Stop) is built in issue #8.
import { http, HttpResponse } from 'msw/http'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { event, sse } from '@/mocks/responses'
import { server } from '@/mocks/node'
import { api } from '@/service/client'
import { streamStallMs } from '@/service/config'
import type { StreamEvent } from '@/service/generated/schema'
import { readSse, StreamStalledError, type SseEvent } from '@/service/sse'

const sessionId = '3f0c2a52-8a52-4a8c-9f3e-6c0f1b1f2e10'
const messageId = '5b1e0c7e-3f7a-4d4b-9a51-2f7c2d9e8a10'
const url = '*/v1/sessions/:sessionId/messages'

function send() {
  return api.POST('/v1/sessions/{sessionId}/messages', {
    params: { path: { sessionId } },
    body: { clientMessageId: '0b6a5f1e-2c1d-4e57-9d0b-7a1c9d3e4f21', text: 'Why is the test flaky?' },
    headers: { Accept: 'text/event-stream' },
    parseAs: 'stream',
  })
}

describe('a run stream', () => {
  afterEach(() => { vi.useRealTimers() })

  it('reads the contract\'s events, with their ids, through the client', async () => {
    server.use(http.post(url, () => sse([
      event(1, 'run.started', { type: 'run.started', messageId, n: 1 }),
      ': ping\n\n',
      event(2, 'block.started', { type: 'block.started', messageId, n: 2, index: 0, block: { id: 'b1', type: 'text', text: '' } }),
      event(3, 'block.delta', { type: 'block.delta', messageId, n: 3, blockId: 'b1', text: 'The failure is a timing race' }),
      event(4, 'run.completed', { type: 'run.completed', messageId, n: 4 }),
    ], 5)))
    const { response } = await send()
    expect(response.headers.get('content-type')).toBe('text/event-stream')
    const events: SseEvent[] = []
    await readSse(response.body ?? new ReadableStream(), { stallMs: streamStallMs, onEvent: (e) => { events.push(e) } })
    const types = events.map((e) => (JSON.parse(e.data) as Pick<StreamEvent, 'type'>).type)
    expect(types).toEqual(['run.started', 'block.started', 'block.delta', 'run.completed'])
    expect(events.map((e) => e.event)).toEqual(types)
    expect(events.at(-1)?.id).toBe('4')
  })

  it('stalls after 45 s without bytes, even though the response is still open', async () => {
    expect(streamStallMs).toBe(45_000)
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'], shouldAdvanceTime: true })
    server.use(http.post(url, () => new HttpResponse(
      new ReadableStream({ start(c) { c.enqueue(new TextEncoder().encode(event(1, 'run.started', { type: 'run.started', messageId, n: 1 }))) } }),
      { headers: { 'content-type': 'text/event-stream' } },
    )))
    const { response } = await send()
    const events: SseEvent[] = []
    const outcome = readSse(response.body ?? new ReadableStream(), { stallMs: streamStallMs, onEvent: (e) => { events.push(e) } })
      .then(() => 'ended', (e: unknown) => e)
    await vi.advanceTimersByTimeAsync(44_000)
    expect(events).toHaveLength(1)
    await vi.advanceTimersByTimeAsync(1_000)
    expect(await outcome).toBeInstanceOf(StreamStalledError)
  })
})
