import { NavLink } from 'react-router'
import { Icon, type IconGlyph } from '@/components/ui/icon'
import { SidebarMenuButton, SidebarMenuItem, useSidebar } from '@/components/ui/sidebar'

export interface NavItem { label: string; to: string; icon: IconGlyph; end?: boolean }

/** A sidebar link. NavLink sets aria-current="page"; on mobile, choosing it closes the sheet. */
export function NavItemLink({ item }: { item: NavItem }) {
  const { isMobile, setOpenMobile } = useSidebar()
  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        tooltip={item.label}
        render={<NavLink to={item.to} end={item.end ?? false} onClick={() => { if (isMobile) setOpenMobile(false) }} />}
        className="aria-[current=page]:bg-sidebar-accent aria-[current=page]:font-medium"
      >
        <Icon icon={item.icon} />
        <span>{item.label}</span>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}

