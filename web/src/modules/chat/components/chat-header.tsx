// Design: Chat Header (H0YWK): the agent's avatar, name and status, then the session's title (the page's h1).
// The agent comes from GET /v1/agents/{slug} (issue #7); a skeleton of the same size while it loads.
import { AgentAvatar } from '@/components/application/agent-avatar'
import { StatusBadge } from '@/components/application/status-badge'
import { ShellBar } from '@/components/layout/shell-bar'
import { Skeleton } from '@/components/ui/skeleton'
import { useRouteAgent } from '@/modules/chat/hooks/use-route-agent'

export function ChatHeader({ title }: { title: string }) {
  const { query } = useRouteAgent()
  const agent = query.data
  return (
    <ShellBar>
      {agent ? (
        <div className="flex shrink-0 items-center gap-2.5">
          <AgentAvatar color={agent.color} icon={agent.icon} />
          <span className="text-14 font-semibold text-text-primary">{agent.name}</span>
          <StatusBadge status={agent.status} className="hidden sm:inline-flex" />
          <span aria-hidden className="hidden text-15 text-border sm:inline">/</span>
        </div>
      ) : query.isPending ? (
        <div aria-hidden className="flex shrink-0 items-center gap-2.5">
          <Skeleton className="size-6.5 rounded-7" />
          <Skeleton className="h-3.5 w-24 rounded-4" />
          <Skeleton className="hidden h-5 w-16 rounded-full sm:block" />
        </div>
      ) : null}
      <h1 tabIndex={-1} className="min-w-0 truncate text-14 text-text-secondary outline-none">{title}</h1>
    </ShellBar>
  )
}
