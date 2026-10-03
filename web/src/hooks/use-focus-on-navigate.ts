import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router'

/** Navigation state that leaves focus where it is (e.g. the composer, when a first message names the session). */
export const keepFocus = { keepFocus: true } as const

export const keepsFocus = (state: unknown) => typeof state === 'object' && state !== null && 'keepFocus' in state

/** After a route change (not the first load), move focus to the new page's h1 (standard §9, §16). */
export function useFocusOnNavigate() {
  const location = useLocation()
  const pathname = location.pathname
  const state: unknown = location.state
  const first = useRef(true)
  const skip = keepsFocus(state)
  useEffect(() => {
    if (first.current) {
      first.current = false
      return
    }
    if (skip) return
    // Lazy routes render after the navigation settles; wait a frame for the heading to exist.
    const frame = requestAnimationFrame(() => document.querySelector<HTMLElement>('main h1')?.focus())
    return () => { cancelAnimationFrame(frame) }
  }, [pathname, skip])
}
