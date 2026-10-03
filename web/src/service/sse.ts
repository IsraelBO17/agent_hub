// Server-Sent Events over fetch (standard §12, Appendix C6). EventSource can't send a body or an
// Authorization header, so streams are read here.
export interface SseEvent {
  id: string | undefined // the last id seen; it carries over to later events
  event: string          // "message" when the server sent no event field
  data: string           // data lines joined with "\n"
}

/** Incremental text/event-stream parser. Feed it decoded text split anywhere. */
export function createSseParser(onEvent: (event: SseEvent) => void) {
  let buffer = ''
  let data: string[] = []
  let type = ''
  let lastId: string | undefined

  function dispatch() {
    if (data.length > 0) onEvent({ id: lastId, event: type || 'message', data: data.join('\n') })
    data = []
    type = ''
  }

  function line(text: string) {
    if (text === '') {
      dispatch()
      return
    }
    if (text.startsWith(':')) return // a comment, e.g. a keep-alive ping
    const colon = text.indexOf(':')
    const field = colon === -1 ? text : text.slice(0, colon)
    let value = colon === -1 ? '' : text.slice(colon + 1)
    if (value.startsWith(' ')) value = value.slice(1)
    if (field === 'event') type = value
    else if (field === 'data') data.push(value)
    else if (field === 'id' && !value.includes('\0')) lastId = value
    // `retry` and unknown fields are ignored.
  }

  return {
    feed(chunk: string) {
      buffer += chunk
      let start = 0
      for (let i = 0; i < buffer.length; i++) {
        const c = buffer[i]
        if (c !== '\n' && c !== '\r') continue
        if (c === '\r' && i === buffer.length - 1) break // may be the first half of "\r\n"
        line(buffer.slice(start, i))
        if (c === '\r' && buffer[i + 1] === '\n') i++
        start = i + 1
      }
      buffer = buffer.slice(start)
    },
  }
}

export class StreamStalledError extends Error {
  override name = 'StreamStalledError'
}

/** Reads an SSE body to its end. Rejects with StreamStalledError after `stallMs` without bytes,
 *  or with the signal's reason when aborted. */
export async function readSse(body: ReadableStream<Uint8Array>,
  { stallMs, signal, onEvent }: { stallMs: number; signal?: AbortSignal | undefined; onEvent: (e: SseEvent) => void }) {
  signal?.throwIfAborted()
  const reader = body.getReader()
  const decoder = new TextDecoder()
  const parser = createSseParser(onEvent)
  const stall = { hit: false } // an object, so the read loop sees the timer's write
  let timer: ReturnType<typeof setTimeout> | undefined
  const arm = () => {
    clearTimeout(timer)
    timer = setTimeout(() => { stall.hit = true; cancel() }, stallMs)
  }
  // cancel() rejects if the body already errored; the read loop reports what happened, so ignore it.
  const cancel = () => { reader.cancel().catch(() => undefined) }
  const abort = cancel
  signal?.addEventListener('abort', abort, { once: true })
  try {
    arm()
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      arm()
      parser.feed(decoder.decode(value, { stream: true }))
    }
    if (stall.hit) throw new StreamStalledError(`No data for ${String(stallMs)} ms`)
    signal?.throwIfAborted()
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', abort)
  }
}
