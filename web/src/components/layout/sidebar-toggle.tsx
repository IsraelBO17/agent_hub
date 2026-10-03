// Opens or closes the navigation. `open`: the Top Bar's menu icon on mobile (Pencil E3SDEa), and the way
// back to a collapsed sidebar on desktop. `collapse`: the panel icon in the Sidebar Brand (T8TdZq).
import { Button } from '@/components/ui/button'
import { Icon, Menu, PanelLeft } from '@/components/ui/icon'
import { useSidebar } from '@/components/ui/sidebar'

export function SidebarToggle({ kind, className }: { kind: 'open' | 'collapse'; className?: string }) {
  const { isMobile, openMobile, open, toggleSidebar } = useSidebar()
  const label = kind === 'open' ? 'Open navigation' : isMobile ? 'Close navigation' : 'Collapse sidebar'
  return (
    <Button
      variant="ghost"
      size={kind === 'open' ? 'icon' : 'icon-xs'}
      aria-label={label}
      aria-expanded={isMobile ? openMobile : open}
      className={className}
      onClick={toggleSidebar}
    >
      {kind === 'open'
        ? <Icon icon={Menu} size="md" className="text-text-primary" />
        : <Icon icon={PanelLeft} className="text-text-tertiary" />}
    </Button>
  )
}
