// The only place icons are imported from (standard §8.3). Sized by token, never by raw pixels.
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

export type IconGlyph = LucideIcon

const sizes = { xs: 'size-3', sm: 'size-4', md: 'size-5', lg: 'size-6', xl: 'size-8' } as const

export function Icon({ icon: Glyph, size = 'sm', label, className }: { icon: LucideIcon; size?: keyof typeof sizes; label?: string; className?: string }) {
  // Decorative by default (lucide sets aria-hidden); a label makes it meaningful to assistive tech.
  return label ? <Glyph role="img" aria-hidden={false} aria-label={label} className={cn(sizes[size], className)} /> : <Glyph className={cn(sizes[size], className)} />
}

export { AlertCircle, FileText, LayoutGrid, Loader2, Lock, SearchX } from 'lucide-react'
