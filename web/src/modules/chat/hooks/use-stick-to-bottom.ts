// The transcript's scrolling: it follows new content while the reader is at the bottom, says when they aren't
// (Jump to latest), and keeps their place when older messages are added above.
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'

const threshold = 80

/** `scroller` goes on the scrolling element, `content` on what grows inside it; `firstId` is the oldest message's. */
export function useStickToBottom(firstId: string | undefined) {
  const scroller = useRef<HTMLDivElement>(null)
  const content = useRef<HTMLDivElement>(null)
  const [atBottom, setAtBottom] = useState(true)
  const stick = useRef(true)
  const fromBottom = useRef(0)

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'auto') => {
    const el = scroller.current
    if (!el) return
    stick.current = true
    setAtBottom(true)
    el.scrollTo({ top: el.scrollHeight, behavior })
  }, [])

  useEffect(() => {
    const el = scroller.current
    if (!el) return
    const onScroll = () => {
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight
      fromBottom.current = el.scrollHeight - el.scrollTop
      stick.current = distance < threshold
      setAtBottom(stick.current)
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => { el.removeEventListener('scroll', onScroll) }
  }, [])

  useEffect(() => {
    const el = scroller.current
    const inner = content.current
    if (!el || !inner || typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(() => { if (stick.current) el.scrollTo({ top: el.scrollHeight }) })
    observer.observe(inner)
    return () => { observer.disconnect() }
  }, [])

  // Older messages were added above: keep the same distance from the bottom, so nothing jumps.
  useLayoutEffect(() => {
    const el = scroller.current
    if (!el || stick.current || fromBottom.current === 0) return
    el.scrollTo({ top: el.scrollHeight - fromBottom.current })
  }, [firstId])

  return { scroller, content, atBottom, scrollToBottom }
}
