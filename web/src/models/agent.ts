// An agent from the registry (contract `Agent`), as the catalog, the switcher and the chat header show it.
import type { Agent as AgentWire } from '@/service/generated/schema'

export type AgentColor = AgentWire['color']
export type AgentStatus = AgentWire['status']

export interface Agent {
  slug: string
  name: string
  description: string
  /** The short line for the mobile catalog: the tagline, else the description. */
  tagline: string
  icon: string
  color: AgentColor
  status: AgentStatus
  statusChangedAt: Date | null
  beta: boolean
  /** e.g. "Strands · AgentCore". */
  stack: string
  sessionCount: number
  lastActiveAt: Date | null
  /** Offline agents can't start a session (degraded ones can). */
  available: boolean
  defaultGreeting: string | null
  starters: { title: string; description: string | null; prompt: string }[]
  /** Shown under the composer after "{name} can make mistakes." */
  disclaimer: string | null
}

const frameworkNames: Record<string, string> = { strands: 'Strands', langgraph: 'LangGraph' }
const runtimeNames: Record<AgentWire['runtimeType'], string> = { agentcore: 'AgentCore', http: 'HTTP adapter' }

const date = (value: string | null) => (value ? new Date(value) : null)

export function toDomainAgent(a: AgentWire): Agent {
  const framework = a.framework ? (frameworkNames[a.framework] ?? a.framework) : null
  return {
    slug: a.slug,
    name: a.name,
    description: a.description,
    tagline: a.tagline ?? a.description,
    icon: a.icon,
    color: a.color,
    status: a.status,
    statusChangedAt: date(a.statusChangedAt),
    beta: a.stage === 'beta',
    stack: [framework, runtimeNames[a.runtimeType]].filter(Boolean).join(' · '),
    sessionCount: a.myStats.sessionCount,
    lastActiveAt: date(a.myStats.lastActiveAt),
    available: a.status !== 'offline',
    defaultGreeting: a.greeting,
    starters: a.starters.map((s) => ({ title: s.title, description: s.description ?? null, prompt: s.prompt })),
    disclaimer: a.disclaimer,
  }
}

/** The agent the sidebar starts on: the one in the URL, else the user's default, else the most recently used, else the first. */
export function currentAgent(agents: Agent[], urlSlug: string | undefined, defaultSlug: string | null): Agent | undefined {
  const bySlug = (slug: string | null | undefined) => (slug ? agents.find((a) => a.slug === slug) : undefined)
  const recent = [...agents].filter((a) => a.lastActiveAt).sort((a, b) => (b.lastActiveAt?.getTime() ?? 0) - (a.lastActiveAt?.getTime() ?? 0))[0]
  return bySlug(urlSlug) ?? bySlug(defaultSlug) ?? recent ?? agents[0]
}
