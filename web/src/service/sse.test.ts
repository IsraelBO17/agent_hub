import { afterEach, describe, expect, it, vi } from 'vitest'
import { createSseParser, readSse, StreamStalledError, type SseEvent } from '@/service/sse'

function parse(...chunks: string[]) {
  const events: SseEvent[] = []
  const parser = createSseParser((e) => { events.push(e) })
  chunks.forEach((c) => { parser.feed(c) })
  return events
}

function streamOf(...chunks: string[]) {
  const enc = new TextEncoder()
  return new ReadableStream<Uint8Array>({
    start(c) { chunks.forEach((s) => { c.enqueue(enc.encode(s)) }); c.close() },
  })
}

describe('createSseParser', () => {
  it('parses id, event and data', () => {
    expect(parse('id: 7\nevent: run.delta\ndata: {"t":"hi"}\n\n')).toEqual([{ id: '7', event: 'run.delta', data: '{"t":"hi"}' }])
  })
  it('defaults the event type to message and joins data lines', () => {
    expect(parse('data: a\ndata: b\n\n')).toEqual([{ id: undefined, event: 'message', data: 'a\nb' }])
  })
  it('handles chunks split anywhere, including inside CRLF', () => {
    expect(parse('ev', 'ent: x\r', '\ndata: 1\r\n', '\r', '\n')).toEqual([{ id: undefined, event: 'x', data: '1' }])
  })
  it('accepts lone CR line endings', () => {
    // A trailing CR is held until the next chunk shows whether it starts a CRLF.
    expect(parse('data: 1\r\rdata: 2\r\r', 'data: 3')).toHaveLength(2)
  })
  it('ignores comments, retry and events without data', () => {
    expect(parse(': ping\n\nretry: 10\nevent: empty\n\ndata: x\n\n')).toEqual([{ id: undefined, event: 'message', data: 'x' }])
  })
  it('keeps the last id for later events and strips only one leading space', () => {
    expect(parse('id: 1\ndata:  two spaces\n\ndata:x\n\n')).toEqual([
      { id: '1', event: 'message', data: ' two spaces' },
      { id: '1', event: 'message', data: 'x' },
    ])
  })
  it('does not dispatch an unterminated event', () => {
    expect(parse('data: partial')).toEqual([])
  })
})

describe('readSse', () => {
  afterEach(() => vi.useRealTimers())

  it('reads to the end of the stream', async () => {
    const events: SseEvent[] = []
    await readSse(streamOf('data: 1\n\n', 'data: 2\n\n'), { stallMs: 1000, onEvent: (e) => { events.push(e) } })
    expect(events.map((e) => e.data)).toEqual(['1', '2'])
  })

  it('rejects with StreamStalledError after stallMs without bytes, and pings keep it alive', async () => {
    vi.useFakeTimers()
    const enc = new TextEncoder()
    let ctrl!: ReadableStreamDefaultController<Uint8Array>
    const body = new ReadableStream<Uint8Array>({ start(c) { ctrl = c } })
    const done = readSse(body, { stallMs: 45_000, onEvent: () => undefined })
    const outcome = done.then(() => 'resolved', (e: unknown) => e)
    await vi.advanceTimersByTimeAsync(44_000)
    ctrl.enqueue(enc.encode(': ping\n\n'))
    await vi.advanceTimersByTimeAsync(44_000) // 88 s since start, but only 44 s since the ping
    let settled = false
    void outcome.then(() => { settled = true })
    await Promise.resolve()
    expect(settled).toBe(false)
    await vi.advanceTimersByTimeAsync(1_000)
    expect(await outcome).toBeInstanceOf(StreamStalledError)
  })

  it('rejects with the abort reason when the signal aborts', async () => {
    const body = new ReadableStream<Uint8Array>()
    const controller = new AbortController()
    const done = readSse(body, { stallMs: 45_000, signal: controller.signal, onEvent: () => undefined })
    controller.abort(new DOMException('Stopped', 'AbortError'))
    await expect(done).rejects.toMatchObject({ name: 'AbortError' })
  })
})
