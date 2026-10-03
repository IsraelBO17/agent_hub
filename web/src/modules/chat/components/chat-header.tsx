// Design: Chat Header (H0YWK): the agent's avatar, name and status, then the session's title (the page's h1).
// The agent loads with issue #7, so its part is a skeleton of the same size until then.
import { ShellBar } from '@/components/layout/shell-bar'
import { Skeleton } from '@/components/ui/skeleton'

export function ChatHeader({ title }: { title: string }) {
  return (
    <ShellBar>
      <div aria-hidden className="flex shrink-0 items-center gap-2.5">
        <Skeleton className="size-6.5 rounded-7" />
        <Skeleton className="h-3.5 w-24 rounded-4" />
        <Skeleton className="hidden h-5 w-16 rounded-full sm:block" />
        <span className="hidden text-15 text-border sm:inline">/</span>
      </div>
      <h1 tabIndex={-1} className="min-w-0 truncate text-14 text-text-secondary outline-none">{title}</h1>
    </ShellBar>
  )
}
