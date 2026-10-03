// Design: Agent Switcher (RZF5q), loading. The switcher lists the agents (issue #7); until they load it keeps
// its size, so nothing below it moves.
import { Skeleton } from '@/components/ui/skeleton'

export function AgentSwitcherSkeleton() {
  return (
    <div aria-hidden className="flex items-center gap-2.5 rounded-10 border bg-surface px-2.5 py-2.25 shadow-control">
      <Skeleton className="size-7.5 rounded-8" />
      <div className="flex flex-1 flex-col gap-1.5">
        <Skeleton className="h-3.5 w-28 rounded-4" />
        <Skeleton className="h-3 w-20 rounded-4" />
      </div>
    </div>
  )
}
