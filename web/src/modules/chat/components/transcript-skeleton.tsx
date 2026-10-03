// The transcript loading: a user bubble and a reply's lines, the size of the real ones.
import { Skeleton } from '@/components/ui/skeleton'

export function TranscriptSkeleton() {
  return (
    <div aria-hidden className="flex flex-col gap-8">
      {[0, 1].map((i) => (
        <div key={i} className="flex flex-col gap-8">
          <Skeleton className="ml-auto h-12 w-3/5 rounded-16" />
          <div className="flex gap-3.5">
            <Skeleton className="size-6.5 rounded-7" />
            <div className="flex flex-1 flex-col gap-2.5 pt-1">
              <Skeleton className="h-3.5 w-full rounded-4" />
              <Skeleton className="h-3.5 w-11/12 rounded-4" />
              <Skeleton className="h-3.5 w-2/3 rounded-4" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
