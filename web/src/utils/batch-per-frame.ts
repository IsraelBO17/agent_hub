/** Collects values and hands them over at most once per animation frame (standard §12, §18). */
export function batchPerFrame<T>(flush: (items: T[]) => void) {
  let queue: T[] = []
  let frame: number | null = null
  const run = () => {
    frame = null
    const items = queue
    queue = []
    if (items.length > 0) flush(items)
  }
  return {
    push(item: T) {
      queue.push(item)
      frame ??= requestAnimationFrame(run)
    },
    /** Hands over anything still queued, now. */
    flushNow() {
      if (frame !== null) cancelAnimationFrame(frame)
      run()
    },
    cancel() {
      if (frame !== null) cancelAnimationFrame(frame)
      frame = null
      queue = []
    },
  }
}
