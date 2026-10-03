// The shell while the session is being restored (standard §14): the sidebar's and the page's shapes, nothing
// to read yet. Domain-free, so the auth guard can show it before any screen loads.
import { Skeleton } from '@/components/ui/skeleton'

export function AppShellSkeleton() {
  return (
    <div aria-busy="true" className="flex h-dvh">
      <span className="sr-only" role="status">Loading</span>
      <div aria-hidden className="hidden w-(--layout-sidebar-width) shrink-0 flex-col gap-3 border-r bg-sidebar px-3.5 pt-4 md:flex">
        <Skeleton className="h-6 w-28 rounded-7" />
        <Skeleton className="h-12.5 rounded-10" />
        <Skeleton className="h-4 w-32 rounded-4" />
      </div>
      <div aria-hidden className="flex flex-1 flex-col">
        <div className="h-(--layout-mobile-bar-height) border-b md:h-(--layout-chat-header-height)" />
      </div>
    </div>
  )
}
