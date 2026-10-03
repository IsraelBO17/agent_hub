// Pages with the App Header and no desktop sidebar (the catalog, agent detail; Pencil PBQLh, x05s4W). On
// mobile the header's menu opens the sessions drawer.
import { Outlet } from 'react-router'
import { AppHeader } from '@/components/layout/app-header'
import { AppShell } from '@/components/layout/app-shell'
import { SidebarToggle } from '@/components/layout/sidebar-toggle'
import { AppSidebar } from '@/modules/shell/components/app-sidebar'
import { Brand } from '@/modules/shell/components/brand'
import { UserBadge } from '@/modules/shell/components/user-badge'

export function HubLayout() {
  return (
    <AppShell
      desktopSidebar={false}
      sidebar={<AppSidebar />}
      header={<AppHeader brand={<Brand size="header" />} menu={<SidebarToggle kind="open" className="md:hidden" />} actions={<UserBadge size="header" />} />}
    >
      <Outlet />
    </AppShell>
  )
}
