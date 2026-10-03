// Design: Jump to Latest (R2yN9): shown when the reader has scrolled up; the dot says a reply is still arriving.
import { ArrowDown, Icon } from '@/components/ui/icon'

export function JumpToLatest({ live, onClick }: { live: boolean; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className="flex items-center gap-1.75 rounded-full border bg-surface py-1.75 pr-3 pl-2.5 text-13 font-medium text-text-primary shadow-float">
      {live ? <span aria-hidden className="size-1.75 rounded-full bg-accent" /> : null}
      Jump to latest
      <Icon icon={ArrowDown} className="size-3.5 text-text-secondary" />
    </button>
  )
}
