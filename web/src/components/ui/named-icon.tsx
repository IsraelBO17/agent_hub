import { lazy, Suspense } from 'react'

const DynamicGlyph = lazy(() => import('@/components/ui/dynamic-glyph'))

/** A lucide icon by name (e.g. an agent's). Its box is reserved while the icon loads, so nothing moves. */
export function NamedIcon({ name, className }: { name: string; className?: string }) {
  return (
    <Suspense fallback={<span aria-hidden className={className} />}>
      <DynamicGlyph name={name} {...(className ? { className } : {})} />
    </Suspense>
  )
}
