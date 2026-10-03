// Markdown from users, APIs or models (standard §19): no raw HTML, react-markdown's URL filter, safe links.
import Markdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

const components: Components = {
  a: ({ node: _node, href, children, ...rest }) => (
    <a {...rest} href={href} target="_blank" rel="noopener noreferrer nofollow" className="text-primary underline underline-offset-4">
      {children}
    </a>
  ),
}

export function SafeMarkdown({ children }: { children: string }) {
  return (
    <div className="space-y-3 text-base leading-relaxed [&_ol]:list-decimal [&_ol]:pl-6 [&_ul]:list-disc [&_ul]:pl-6">
      <Markdown remarkPlugins={[remarkGfm]} components={components} skipHtml>
        {children}
      </Markdown>
    </div>
  )
}
