import { describe, expect, it } from 'vitest'
import { seedAgents } from '@/mocks/data/agents'
import { currentAgent, toDomainAgent } from '@/models/agent'

const agents = seedAgents().map(toDomainAgent)

describe('agent', () => {
  it('maps the registry\'s agent for the UI', () => {
    const travel = agents.find((a) => a.slug === 'travel-planner')
    expect(travel).toMatchObject({ stack: 'LangGraph · HTTP adapter', beta: true, available: true, sessionCount: 0 })
    expect(agents.find((a) => a.slug === 'home-ops')).toMatchObject({ available: false, statusChangedAt: new Date('2026-09-24T09:00:00Z') })
  })

  it('falls back to the description when there is no tagline', () => {
    const [first] = seedAgents()
    if (!first) throw new Error('no agents')
    expect(toDomainAgent({ ...first, tagline: null }).tagline).toBe(first.description)
  })

  it('starts on the URL\'s agent, else the default, else the most recent, else the first', () => {
    expect(currentAgent(agents, 'ledger', 'coding-agent')?.slug).toBe('ledger')
    expect(currentAgent(agents, undefined, 'travel-planner')?.slug).toBe('travel-planner')
    expect(currentAgent(agents, 'unknown', null)?.slug).toBe('coding-agent') // used 20 minutes ago
    expect(currentAgent([], undefined, null)).toBeUndefined()
  })
})
