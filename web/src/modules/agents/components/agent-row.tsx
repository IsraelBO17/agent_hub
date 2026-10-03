// Design: the mobile catalog's agent row (F10.1 UK1JP): avatar, name and tagline, Beta, status.
import { Link } from 'react-router'
import { AgentAvatar } from '@/components/application/agent-avatar'
import { StageTag } from '@/components/application/stage-tag'
import { StatusBadge } from '@/components/application/status-badge'
import { cn } from '@/lib/utils'
import type { Agent } from '@/models/agent'

export function AgentRow({ agent }: { agent: Agent }) {
  const body = (
    <>
      <AgentAvatar color={agent.color} icon={agent.icon} size="md" className={agent.available ? '' : 'opacity-50'} />
      <span className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="truncate text-15 font-semibold text-text-primary">{agent.name}</span>
        <span className="truncate text-13 text-text-secondary">{agent.tagline}</span>
      </span>
      {agent.beta ? <StageTag label="Beta" /> : null}
      <StatusBadge status={agent.status} />
    </>
  )
  const row = 'flex items-center gap-3 rounded-14 border p-3'
  if (!agent.available) return <div className={cn(row, 'bg-bg')}>{body}</div>
  return <Link to={`/agents/${agent.slug}`} className={cn(row, 'bg-surface')}>{body}</Link>
}
