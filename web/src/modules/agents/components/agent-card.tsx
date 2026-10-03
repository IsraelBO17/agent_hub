// Design: Agent Card (VZuIf) in the catalog (PBQLh). The whole card is one link to the agent's new session; an
// offline agent's card is muted (its avatar dimmed), not a link, and says "Unavailable".
import { Link } from 'react-router'
import { AgentAvatar } from '@/components/application/agent-avatar'
import { StageTag } from '@/components/application/stage-tag'
import { StatusBadge } from '@/components/application/status-badge'
import { ArrowRight, Icon, Lock } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import type { Agent } from '@/models/agent'
import { agentMeta } from '@/modules/agents/components/agent-meta'

export function AgentCard({ agent }: { agent: Agent }) {
  const body = (
    <>
      <div className="flex items-start justify-between">
        <AgentAvatar color={agent.color} icon={agent.icon} size="lg" className={agent.available ? '' : 'opacity-50'} />
        <StatusBadge status={agent.status} />
      </div>
      <div className="flex flex-col gap-1.5">
        <h2 className="text-15 font-semibold text-text-primary">{agent.name}</h2>
        <p className="text-14 leading-normal text-text-secondary">{agent.description}</p>
      </div>
      <div className="flex items-center gap-1.5 font-mono text-12 text-text-tertiary">
        {agent.stack}
        {agent.beta ? <StageTag label="Beta" /> : null}
      </div>
      <div className="mt-auto flex items-center justify-between border-t pt-4 text-13">
        <span className="text-text-tertiary">{agentMeta(agent)}</span>
        {agent.available ? (
          <span className="flex items-center gap-1.5 font-semibold text-accent">New session<Icon icon={ArrowRight} className="size-3.75" /></span>
        ) : (
          <span className="flex items-center gap-1.5 font-medium text-text-tertiary">Unavailable<Icon icon={Lock} className="size-3.75" /></span>
        )}
      </div>
    </>
  )
  const card = 'flex h-full flex-col gap-4 rounded-14 border p-5.5'
  // The design dims the whole card (72 %); that takes its text below WCAG contrast, so only the avatar is dimmed.
  if (!agent.available) return <article className={cn(card, 'bg-bg')}>{body}</article>
  return (
    <Link to={`/agents/${agent.slug}`} aria-label={`${agent.name}: new session`} className={cn(card, 'bg-surface')}>
      {body}
    </Link>
  )
}
