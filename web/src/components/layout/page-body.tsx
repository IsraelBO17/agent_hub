// A page's content area, with the design's padding: `hub` pages under the App Header (catalog: 48 × 120),
// `workspace` pages beside the sidebar (Archived: 36 × 48), and the `chat` column (about 760 wide).
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

const kinds = {
  hub: 'px-4 py-6 md:px-30 md:py-12',
  workspace: 'px-4 py-6 md:px-12 md:py-9',
  chat: 'mx-auto w-full max-w-(--layout-chat-width) px-4 py-6',
}

export function PageBody({ kind, className, children }: { kind: keyof typeof kinds; className?: string; children: ReactNode }) {
  return <div className={cn('flex flex-1 flex-col', kinds[kind], className)}>{children}</div>
}
