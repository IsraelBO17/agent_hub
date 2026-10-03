// The bar at the top of a page beside the sidebar (Pencil Chat Header H0YWK, 60 px; mobile Top Bar E3SDEa,
// 52 px): the navigation toggle whenever the sidebar isn't showing, the page's context, and its actions.
import type { ReactNode } from 'react'
import { SidebarToggle } from '@/components/layout/sidebar-toggle'
import { useSidebar } from '@/components/ui/sidebar'

interface Props {
  children?: ReactNode
  actions?: ReactNode
  /** Render nothing while the desktop sidebar is open (pages whose title is in the content, like Archived). */
  onlyForNavigation?: boolean
}

export function ShellBar({ children, actions, onlyForNavigation = false }: Props) {
  const { isMobile, state } = useSidebar()
  const showToggle = isMobile || state === 'collapsed'
  if (onlyForNavigation && !showToggle) return null
  return (
    <div className="sticky top-0 z-10 flex h-(--layout-mobile-bar-height) shrink-0 items-center gap-2.5 border-b bg-background px-3 md:h-(--layout-chat-header-height) md:px-6">
      {showToggle ? <SidebarToggle kind="open" /> : null}
      <div className="flex min-w-0 flex-1 items-center gap-2.5">{children}</div>
      {actions ? <div className="flex shrink-0 items-center gap-1">{actions}</div> : null}
    </div>
  )
}
