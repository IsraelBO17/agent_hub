// Design: Sidebar Footer (CpCSr) links: 26 px Icon Buttons with a Tooltip (PRODUCT_PLAN §5: All agents,
// Artifacts and Archived live here, not in the main navigation).
import { NavLink } from 'react-router'
import { buttonVariants } from '@/components/ui/button'
import { Archive, Icon, type IconGlyph, LayoutGrid, Settings, Shapes } from '@/components/ui/icon'
import { useSidebar } from '@/components/ui/sidebar'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

const links: { label: string; to: string; icon: IconGlyph }[] = [
  { label: 'All agents', to: '/', icon: LayoutGrid },
  { label: 'Artifacts', to: '/artifacts', icon: Shapes },
  { label: 'Archived', to: '/archived', icon: Archive },
  { label: 'Settings', to: '/settings', icon: Settings },
]

export function SidebarFooterLinks() {
  const { isMobile, setOpenMobile } = useSidebar()
  return (
    <nav aria-label="Library and settings" className="flex items-center">
      {links.map((link) => (
        <Tooltip key={link.to}>
          <TooltipTrigger
            render={<NavLink to={link.to} end aria-label={link.label} onClick={() => { if (isMobile) setOpenMobile(false) }} />}
            className={buttonVariants({ variant: 'ghost', size: 'icon-2xs', className: 'size-6.5 rounded-7 text-text-tertiary aria-[current=page]:text-text-primary' })}
          >
            <Icon icon={link.icon} />
          </TooltipTrigger>
          <TooltipContent>{link.label}</TooltipContent>
        </Tooltip>
      ))}
    </nav>
  )
}
