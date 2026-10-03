// Design: the catalog's Page Heading (PBQLh): title 28/600 and a 15 px subtitle, actions on the right.
import type { ReactNode } from 'react'

/** The screen's one h1 (standard §16). Focus moves here after navigation, so it takes tabIndex -1. */
export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3 pb-8">
      <div className="flex min-w-0 flex-col gap-2">
        <h1 tabIndex={-1} className="text-28 font-semibold tracking-tight text-text-primary outline-none">{title}</h1>
        {description ? <p className="text-15 text-text-secondary">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-3">{actions}</div> : null}
    </header>
  )
}
