// MSW handlers for the registry (contract Agents).
import { http, HttpResponse } from 'msw/http'
import { seedAgents } from '@/mocks/data/agents'
import { problem } from '@/mocks/responses'
import type { Agent, Problem } from '@/service/generated/schema'

export const agentHandlers = [
  http.get('*/v1/agents', () => HttpResponse.json({ items: seedAgents() })),
  http.get<{ slug: string }, never, Agent | Problem>('*/v1/agents/:slug', ({ params }) => {
    const found = seedAgents().find((a) => a.slug === params.slug)
    return found ? HttpResponse.json(found) : problem(404, 'agent_not_found', 'Agent not found')
  }),
]
