import { Skeleton } from '@/components/ui/skeleton'

/** The signed-in user's avatar and name while unknown (sign-in is issue #6). */
export function UserSkeleton({ size }: { size: 'sidebar' | 'header' }) {
  if (size === 'header') return <Skeleton aria-hidden className="size-7.5 rounded-full" />
  return (
    <div aria-hidden className="flex min-w-0 flex-1 items-center gap-2">
      <Skeleton className="size-7 rounded-full" />
      <Skeleton className="h-3.5 w-20 rounded-4" />
    </div>
  )
}
