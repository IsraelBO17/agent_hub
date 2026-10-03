// Design: Agent Menu Item (UauTJ): avatar, name 14/600, the inline status. The check for the current agent is
// the radio item's indicator.
import { AgentAvatar } from '@/components/application/agent-avatar'
import { StatusBadge } from '@/components/application/status-badge'
import type { Agent } from '@/models/agent'

export function AgentMenuItemContent({ agent }: { agent: Agent }) {
  return (
    <>
      <AgentAvatar color={agent.color} icon={agent.icon} />
      <span className="min-w-0 flex-1 truncate text-14 font-semibold text-text-primary">{agent.name}</span>
      <StatusBadge status={agent.status} variant="inline" />
    </>
  )
}
