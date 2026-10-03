// Design: Typing Indicator (eFeRx): three dots while the agent hasn't sent anything yet (F2.5), announced politely.
export function TypingIndicator() {
  return (
    <div role="status" className="flex w-fit items-center gap-1.25 rounded-full bg-surface-muted px-3 py-2.5">
      <span className="sr-only">The agent is working on a reply</span>
      {[0, 1, 2].map((i) => <span key={i} aria-hidden className="size-1.75 rounded-full bg-text-secondary motion-safe:animate-pulse" style={{ animationDelay: `${String(i * 150)}ms` }} />)}
    </div>
  )
}
