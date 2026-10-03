// An agent's text: GitHub-flavoured Markdown through SafeMarkdown (profile: Untrusted content), loaded lazily
// (standard §18). Until it loads, the text shows as is, in the same type, so nothing jumps.
import { lazy, Suspense } from 'react'

const Markdown = lazy(() => import('@/modules/chat/components/markdown-text'))

export function TextBlock({ text }: { text: string }) {
  return (
    <Suspense fallback={<p className="text-15 leading-relaxed whitespace-pre-wrap text-text-primary">{text}</p>}>
      <Markdown text={text} />
    </Suspense>
  )
}
