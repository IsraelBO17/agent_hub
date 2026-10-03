// Design: the Session List (hj5RV) while it loads (the States board; mobile F11.15). The current agent's
// sessions arrive with issue #8.
import { Skeleton } from '@/components/ui/skeleton'

const widths = ['w-44', 'w-36', 'w-40', 'w-32', 'w-38']

export function SessionListSkeleton() {
  return (
    <div aria-hidden className="flex flex-col gap-1">
      <Skeleton className="mx-2.5 mb-2 h-3 w-12 rounded-4" />
      {widths.map((w) => <Skeleton key={w} className={`mx-2.5 my-2 h-3.5 rounded-4 ${w}`} />)}
    </div>
  )
}
