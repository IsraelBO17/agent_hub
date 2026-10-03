/** The first focusable element on every page (standard §16). */
export function SkipLink({ target = 'main' }: { target?: string }) {
  return (
    <a href={`#${target}`} className="sr-only z-50 rounded-md bg-background px-3 py-2 text-sm focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:ring-3 focus:ring-ring">
      Skip to content
    </a>
  )
}
