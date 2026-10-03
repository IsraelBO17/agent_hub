// The app shell (standard §8.4; Pencil Sidebar hj5RV): the sidebar (284 px wide; the drawer below the mobile
// breakpoint), an optional header, and the content region, which scrolls instead of the page. Domain-free:
// modules/shell passes the sidebar's contents and the header.
import type { ReactNode } from 'react'
import { ShellSidebar } from '@/components/layout/shell-sidebar'
import { SkipLink } from '@/components/layout/skip-link'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'

interface Props {
  /** The sidebar's contents: SidebarHeader, SidebarContent, SidebarFooter. */
  sidebar: ReactNode
  /** false: no sidebar on desktop (pages with the App Header). On mobile it is always the drawer. */
  desktopSidebar?: boolean
  header?: ReactNode
  children: ReactNode
}

export function AppShell({ sidebar, desktopSidebar = true, header, children }: Props) {
  return (
    <SidebarProvider className="h-dvh min-h-0">
      <SkipLink />
      <ShellSidebar desktop={desktopSidebar}>{sidebar}</ShellSidebar>
      <SidebarInset className="min-h-0 min-w-0">
        {header}
        <div id="main" tabIndex={-1} className="flex min-h-0 flex-1 flex-col overflow-y-auto outline-none">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  )
}
