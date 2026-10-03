// Agent text as Markdown (Design: Agent Message, BsXl7: 15 px). Code uses the Code Block's colours (wW1XY) and
// Inline Code (Uzd9M), without highlighting or Copy: those come with the Code Block (M2). Default export, for lazy.
import { SafeMarkdown } from '@/components/ui/safe-markdown'

export default function MarkdownText({ text }: { text: string }) {
  return (
    <div className="text-15 leading-relaxed text-text-primary [&_:not(pre)>code]:rounded-5 [&_:not(pre)>code]:border [&_:not(pre)>code]:bg-surface-muted [&_:not(pre)>code]:px-1.25 [&_:not(pre)>code]:text-code-inline-fg [&_code]:font-mono [&_code]:text-13 [&_pre]:overflow-x-auto [&_pre]:rounded-10 [&_pre]:bg-code [&_pre]:px-4 [&_pre]:py-3.5 [&_pre]:text-code-text [&_table]:w-full [&_table]:text-14 [&_td]:border-b [&_td]:py-1.5 [&_td]:pr-3 [&_th]:border-b [&_th]:py-1.5 [&_th]:pr-3 [&_th]:text-left [&_th]:font-semibold">
      <SafeMarkdown>{text}</SafeMarkdown>
    </div>
  )
}
