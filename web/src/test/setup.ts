import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'
import { resetChatStore } from '@/mocks/data/chat'
import { resetMockSession } from '@/mocks/data/session'
import { server } from '@/mocks/node'
import { onSessionEnd, setAccessToken } from '@/service/client'

// jsdom has no matchMedia; components that ask (the sidebar's mobile check) see a desktop screen.
Object.defineProperty(window, 'matchMedia', {
  configurable: true,
  value: (query: string) => ({ matches: false, media: query, onchange: null, addEventListener: () => undefined, removeEventListener: () => undefined, addListener: () => undefined, removeListener: () => undefined, dispatchEvent: () => false }),
})

// jsdom doesn't lay out, so it has no element scrolling; the transcript calls scrollTo.
if (!('scrollTo' in Element.prototype)) Object.assign(Element.prototype, { scrollTo: () => undefined })

// Testing Library only detects fake timers through a global `jest`; this lets it advance Vitest's.
Object.assign(globalThis, { jest: { advanceTimersByTime: (ms: number) => vi.advanceTimersByTime(ms) } })

beforeAll(() => { server.listen({ onUnhandledFrame: 'error' }) })
afterEach(() => {
  server.resetHandlers()
  resetMockSession()
  resetChatStore()
  setAccessToken(null)
  onSessionEnd(() => undefined)
  cleanup()
  vi.useRealTimers()
})
afterAll(() => { server.close() })
