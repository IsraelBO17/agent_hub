// Synthetic agents for mock mode and tests (the real ones come from the registry). One per state the catalog
// draws: online, degraded, offline, beta, with and without sessions.
import type { Agent } from '@/service/generated/schema'

const hoursAgo = (h: number) => new Date(Date.now() - h * 3_600_000).toISOString()

function agent(fields: Pick<Agent, 'slug' | 'name' | 'description' | 'icon' | 'color'> & Partial<Agent>): Agent {
  return {
    id: crypto.randomUUID(),
    tagline: null,
    greeting: null,
    stage: 'stable',
    status: 'online',
    statusChangedAt: null,
    framework: 'strands',
    runtimeType: 'agentcore',
    version: '1.0.0',
    deployedAt: hoursAgo(72),
    details: {},
    disclaimer: null,
    capabilities: { attachments: { enabled: false, contentTypes: [], maxFileBytes: 0, maxFiles: 0 }, artifacts: false, approvals: false, questions: false },
    tools: [],
    starters: [],
    retiredAt: null,
    myStats: { sessionCount: 0, lastActiveAt: null },
    ...fields,
  }
}

export const seedAgents = (): Agent[] => [
  agent({ slug: 'research-analyst', name: 'Research Analyst', icon: 'book-open-text', color: 'purple', stage: 'beta',
    description: 'Reads the web pages you give it and answers your questions from what they say, with links to its sources.',
    tagline: 'Answers from the pages you share', greeting: 'What should I read for you?',
    disclaimer: 'It only reads the pages you link, and those pages can be wrong or out of date.',
    starters: [
      { title: 'Summarise a page', description: 'Five bullet points, with a link to the page', prompt: 'Summarise this page in five bullet points: ' },
      { title: 'Compare two pages', description: 'Where they agree and where they differ', prompt: 'Compare what these two pages say about ' },
      { title: 'Check a claim', description: 'Does the source actually say it?', prompt: 'Does this page support the claim that ' },
      { title: 'Pull out the numbers', description: 'Key figures, with context', prompt: 'List the key figures on this page, with context: ' },
    ],
    myStats: { sessionCount: 22, lastActiveAt: hoursAgo(5) } }),
  agent({ slug: 'coding-agent', name: 'Coding Agent', icon: 'code-xml', color: 'blue',
    description: 'Reads repositories, proposes patches and runs the test suite in an isolated sandbox.', tagline: 'Patches, tests and code review',
    myStats: { sessionCount: 31, lastActiveAt: hoursAgo(0.3) } }),
  agent({ slug: 'ledger', name: 'Ledger', icon: 'landmark', color: 'green', status: 'degraded', statusChangedAt: hoursAgo(2),
    description: 'Checks balances, categorises transactions and drafts transfers that wait for your approval.', tagline: 'Balances, transfers, reconciling',
    myStats: { sessionCount: 9, lastActiveAt: hoursAgo(26) } }),
  agent({ slug: 'travel-planner', name: 'Travel Planner', icon: 'plane', color: 'amber', stage: 'beta', framework: 'langgraph', runtimeType: 'http',
    description: 'Builds day-by-day itineraries with flights, stays and a running budget.', tagline: 'Itineraries and budgets' }),
  agent({ slug: 'home-ops', name: 'Home Ops', icon: 'house', color: 'grey', status: 'offline', statusChangedAt: '2026-09-24T09:00:00Z',
    description: 'Controls smart-home devices and schedules appliances around energy prices.', tagline: 'Devices and energy schedules' }),
]
