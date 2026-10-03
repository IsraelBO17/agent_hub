// Design: the user in the Sidebar Footer (CpCSr: 28 px avatar, name 13/500) and the App Header (fqLch: 30 px
// avatar). Initials only: the CSP serves no Google photos.
import { useSession } from '@/modules/auth'
import { cn } from '@/lib/utils'

export function UserBadge({ size }: { size: 'sidebar' | 'header' }) {
  const { user } = useSession()
  if (!user) return null
  const avatar = (
    <span aria-hidden className={cn('flex shrink-0 items-center justify-center rounded-full bg-surface-muted text-12 font-semibold text-text-secondary', size === 'header' ? 'size-7.5' : 'size-7')}>
      {user.initials}
    </span>
  )
  if (size === 'header') return <span title={user.displayName} className="flex">{avatar}<span className="sr-only">Signed in as {user.displayName}</span></span>
  return (
    <div className="flex min-w-0 flex-1 items-center gap-2">
      {avatar}
      <span className="truncate text-13 font-medium text-text-primary">{user.displayName}</span>
    </div>
  )
}
