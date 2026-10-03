import type { ReactNode } from 'react'
import { Sidebar, useSidebar } from '@/components/ui/sidebar'

/** The sidebar, or nothing on desktop when the page has none; on mobile it is always the drawer. */
export function ShellSidebar({ desktop, children }: { desktop: boolean; children: ReactNode }) {
  const { isMobile } = useSidebar()
  return desktop || isMobile ? <Sidebar>{children}</Sidebar> : null
}
