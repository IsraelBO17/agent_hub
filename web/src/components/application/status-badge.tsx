// Design: Status Badge (JQ0rx: a pill, dot 7, 12/500) and the inline status in Agent Menu Item (UauTJ: dot 6,
// 12 px). The one place status colours appear (standard §8.3); it always carries the word, never colour alone.
import { cn } from '@/lib/utils'

export type Status = 'online' | 'degraded' | 'offline'

const labels: Record<Status, string> = { online: 'Online', degraded: 'Degraded', offline: 'Offline' }
const dots: Record<Status, string> = { online: 'bg-online', degraded: 'bg-busy', offline: 'bg-offline' }

export function StatusBadge({ status, variant = 'pill', className }: { status: Status; variant?: 'pill' | 'inline'; className?: string }) {
  const pill = variant === 'pill'
  return (
    <span className={cn('inline-flex shrink-0 items-center', pill ? 'gap-1.5 rounded-full bg-surface-muted px-2 py-0.75 text-12 font-medium text-text-secondary' : 'gap-1.25 text-12 text-text-tertiary', className)}>
      <span aria-hidden className={cn('rounded-full', pill ? 'size-1.75' : 'size-1.5', dots[status])} />
      {labels[status]}
    </span>
  )
}
