import type { ReactNode } from 'react'

/** The screen's one h1 (standard §16). Focus moves here after navigation, so it takes tabIndex -1. */
export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-3 pb-6">
      <div className="min-w-0">
        <h1 tabIndex={-1} className="text-2xl font-semibold outline-none">{title}</h1>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </header>
  )
}
