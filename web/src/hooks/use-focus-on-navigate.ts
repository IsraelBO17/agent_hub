import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router'

/** After a route change (not the first load), move focus to the new page's h1 (standard §9, §16). */
export function useFocusOnNavigate() {
  const { pathname } = useLocation()
  const first = useRef(true)
  useEffect(() => {
    if (first.current) {
      first.current = false
      return
    }
    // Lazy routes render after the navigation settles; wait a frame for the heading to exist.
    const frame = requestAnimationFrame(() => document.querySelector<HTMLElement>('main h1')?.focus())
    return () => { cancelAnimationFrame(frame) }
  }, [pathname])
}
