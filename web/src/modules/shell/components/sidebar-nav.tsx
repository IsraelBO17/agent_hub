// Design: Sidebar Nav Item (MoK3u), as New session and Search in the Sidebar (hj5RV). New session opens the
// current agent's new session, or the catalog to pick one. Search is the ⌘K palette (P1), not built yet.
import { Link, useParams } from 'react-router'
import { Icon, Search, SquarePen } from '@/components/ui/icon'
import { useSidebar } from '@/components/ui/sidebar'

const item = 'flex w-full items-center gap-2 rounded-9 px-2.5 py-2 text-14'

export function SidebarNav() {
  const { agentId } = useParams()
  const { isMobile, setOpenMobile } = useSidebar()
  return (
    <nav aria-label="Sessions" className="flex flex-col gap-0.5">
      <Link to={agentId ? `/agents/${agentId}` : '/'} className={`${item} font-medium text-text-primary`} onClick={() => { if (isMobile) setOpenMobile(false) }}>
        <Icon icon={SquarePen} />
        New session
      </Link>
      <button type="button" disabled className={`${item} text-text-secondary disabled:opacity-50`}>
        <Icon icon={Search} />
        Search
        <span className="ml-auto text-12 text-text-tertiary">Soon</span>
      </button>
    </nav>
  )
}
