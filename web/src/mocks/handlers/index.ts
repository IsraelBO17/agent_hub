// Every mock handler, one file per resource (standard §11.5). Recipe 5 adds each resource's handlers here.
import type { RequestHandler } from 'msw'
import { agentHandlers } from '@/mocks/handlers/agents'
import { authHandlers } from '@/mocks/handlers/auth'

export const handlers: RequestHandler[] = [...authHandlers, ...agentHandlers]
