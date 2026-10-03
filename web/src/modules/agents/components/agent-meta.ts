import type { Agent } from '@/models/agent'
import { formatDay, formatRelative } from '@/utils/format-date'

/** The card's footer line: sessions and last use, or since when an offline agent has been down. */
export function agentMeta(agent: Agent, now = new Date()): string {
  if (!agent.available) return agent.statusChangedAt ? `Offline since ${formatDay(agent.statusChangedAt, now)}` : 'Offline'
  if (agent.sessionCount === 0) return 'No sessions yet'
  const sessions = `${String(agent.sessionCount)} ${agent.sessionCount === 1 ? 'session' : 'sessions'}`
  return agent.lastActiveAt ? `${sessions} · ${formatRelative(agent.lastActiveAt, now)}` : sessions
}
