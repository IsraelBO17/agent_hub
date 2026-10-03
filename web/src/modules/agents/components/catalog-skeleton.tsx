// The catalog while it loads: the cards' shape on desktop (the States board), the rows' on mobile (F11.1 EP1MN).
import { Skeleton } from '@/components/ui/skeleton'

export function CatalogSkeleton() {
  return (
    <div aria-busy="true">
      <span role="status" className="sr-only">Loading your agents</span>
      <div aria-hidden className="hidden grid-cols-2 gap-3 md:grid lg:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex flex-col gap-4 rounded-14 border bg-surface p-5.5">
            <div className="flex justify-between"><Skeleton className="size-11 rounded-11" /><Skeleton className="h-5 w-16 rounded-full" /></div>
            <Skeleton className="h-4 w-36 rounded-4" />
            <Skeleton className="h-3.5 w-full rounded-4" />
            <Skeleton className="h-3.5 w-3/4 rounded-4" />
          </div>
        ))}
      </div>
      <div aria-hidden className="flex flex-col gap-2.5 md:hidden">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3 rounded-14 border bg-surface p-3">
            <Skeleton className="size-10.5 rounded-11" />
            <div className="flex flex-1 flex-col gap-2"><Skeleton className="h-3 w-32 rounded-4" /><Skeleton className="h-2.5 w-48 rounded-4" /></div>
            <Skeleton className="h-5 w-14 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  )
}
