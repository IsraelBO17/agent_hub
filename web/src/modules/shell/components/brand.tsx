// Design: Sidebar Brand (T8TdZq) and the App Header's brand (fqLch): the mark and the product name, linking
// to the catalog.
import { Link } from 'react-router'
import { Icon, Orbit } from '@/components/ui/icon'
import { cn } from '@/lib/utils'

export function Brand({ size }: { size: 'sidebar' | 'header' }) {
  const header = size === 'header'
  return (
    <Link to="/" className={cn('flex items-center rounded-8', header ? 'gap-2.5' : 'gap-2.25')}>
      <span className={cn('flex items-center justify-center bg-accent text-on-accent', header ? 'size-7 rounded-8' : 'size-6 rounded-7')}>
        <Icon icon={Orbit} size={header ? 'sm' : 'xs'} />
      </span>
      <span className={cn('font-semibold text-text-primary', header ? 'text-15' : 'text-14')}>Agent Hub</span>
    </Link>
  )
}
