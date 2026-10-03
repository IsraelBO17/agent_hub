import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'
import { server } from '@/mocks/node'

// Testing Library only detects fake timers through a global `jest`; this lets it advance Vitest's.
Object.assign(globalThis, { jest: { advanceTimersByTime: (ms: number) => vi.advanceTimersByTime(ms) } })

beforeAll(() => { server.listen({ onUnhandledFrame: 'error' }) })
afterEach(() => {
  server.resetHandlers()
  cleanup()
  vi.useRealTimers()
})
afterAll(() => { server.close() })
