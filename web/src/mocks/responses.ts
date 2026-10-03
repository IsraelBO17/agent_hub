// Response helpers every handler uses (standard §11.5): problem details on errors, and SSE streams.
import { HttpResponse } from 'msw/http'
import { delay } from 'msw/utils/delay'
import type { Problem } from '@/service/generated/schema'

export const problem = (status: number, code: Problem['code'], title: string, extra: Partial<Problem> = {}) =>
  HttpResponse.json<Problem>({ type: 'about:blank', status, code, title, requestId: `req_${code}`, retryable: status >= 500, ...extra },
    { status, headers: { 'content-type': 'application/problem+json' } })

const enc = new TextEncoder()
export const sse = (frames: string[], gapMs = 60) =>
  new HttpResponse(
    new ReadableStream<Uint8Array>({
      async start(c) {
        for (const frame of frames) {
          await delay(gapMs)
          c.enqueue(enc.encode(frame))
        }
        c.close()
      },
    }),
    { headers: { 'content-type': 'text/event-stream', 'cache-control': 'no-cache' } },
  )
export const event = (id: number, type: string, data: unknown) => `id: ${String(id)}\nevent: ${type}\ndata: ${JSON.stringify(data)}\n\n`
