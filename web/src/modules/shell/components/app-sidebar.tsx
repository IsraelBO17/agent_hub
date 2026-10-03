// Design: Sidebar (hj5RV): brand and collapse, Agent Switcher, New session and Search, the current agent's
// sessions, and the footer. The same contents are the mobile sessions drawer (F10.5).
import { SidebarToggle } from '@/components/layout/sidebar-toggle'
import { SidebarContent, SidebarFooter, SidebarHeader } from '@/components/ui/sidebar'
import { AgentSwitcher } from '@/modules/shell/components/agent-switcher'
import { Brand } from '@/modules/shell/components/brand'
import { SessionListNote } from '@/modules/shell/components/session-list-note'
import { SidebarFooterLinks } from '@/modules/shell/components/sidebar-footer-links'
import { SidebarNav } from '@/modules/shell/components/sidebar-nav'
import { UserBadge } from '@/modules/shell/components/user-badge'

export function AppSidebar() {
  return (
    <>
      <SidebarHeader className="gap-2.5 px-3.5 pt-4 pb-3">
        <div className="flex items-center justify-between px-1">
          <Brand size="sidebar" />
          <SidebarToggle kind="collapse" />
        </div>
        <AgentSwitcher />
        <SidebarNav />
      </SidebarHeader>
      <SidebarContent className="px-3.5 py-2.5">
        <SessionListNote />
      </SidebarContent>
      <SidebarFooter className="flex-row items-center gap-2 border-t px-3.5 py-3">
        <UserBadge size="sidebar" />
        <SidebarFooterLinks />
      </SidebarFooter>
    </>
  )
}
