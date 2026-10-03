/**
 * Collects values and hands them over at most once per animation frame (standard §12, §18). Browsers don't run
 * animation frames in a background tab, so a timer hands them over there instead (at most every `fallbackMs`);
 * otherwise a stream read in a hidden tab would pile up unseen until the tab came back.
 */
export function batchPerFrame<T>(flush: (items: T[]) => void, fallbackMs = 250) {
  let queue: T[] = []
  let frame: number | null = null
  let timer: ReturnType<typeof setTimeout> | null = null
  const stop = () => {
    if (frame !== null) cancelAnimationFrame(frame)
    if (timer !== null) clearTimeout(timer)
    frame = null
    timer = null
  }
  const run = () => {
    stop()
    const items = queue
    queue = []
    if (items.length > 0) flush(items)
  }
  return {
    push(item: T) {
      queue.push(item)
      frame ??= requestAnimationFrame(run)
      timer ??= setTimeout(run, fallbackMs)
    },
    /** Hands over anything still queued, now. */
    flushNow() {
      run()
    },
    cancel() {
      stop()
      queue = []
    },
  }
}
