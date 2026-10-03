import { setupServer } from 'msw/node'
import { handlers } from '@/mocks/handlers'

/** MSW for Vitest (standard §22). Tests override per test with server.use(...). */
export const server = setupServer(...handlers)
