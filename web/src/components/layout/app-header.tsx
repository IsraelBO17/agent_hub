// Design: App Header (fqLch): the brand on the left, the account on the right, 64 px with a bottom border.
// On mobile it is the Top Bar (52 px) and carries the navigation toggle the layout passes in `menu`.
import type { ReactNode } from 'react'

export function AppHeader({ brand, menu, actions }: { brand: ReactNode; menu?: ReactNode; actions?: ReactNode }) {
  return (
    <header className="sticky top-0 z-10 flex h-(--layout-mobile-bar-height) shrink-0 items-center justify-between gap-2.5 border-b bg-background px-3 md:h-(--layout-app-header-height) md:px-10">
      <div className="flex min-w-0 items-center gap-2.5">{menu}{brand}</div>
      {actions ? <div className="flex shrink-0 items-center gap-4">{actions}</div> : null}
    </header>
  )
}
