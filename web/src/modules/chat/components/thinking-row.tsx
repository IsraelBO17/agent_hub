// Design: Thinking Row (Fg95V): "Thought for Ns", collapsed by default (principle 3); open shows the reasoning
// with a left rule. While the agent is still thinking it says "Thinking…".
import { useId, useState } from 'react'
import { ChevronRight, Icon, Sparkles } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { thoughtSeconds, type Block } from '@/models/message'

export function ThinkingRow({ block, replyEndedAt }: { block: Extract<Block, { type: 'thinking' }>; replyEndedAt: Date | null }) {
  const [open, setOpen] = useState(false)
  const id = useId()
  const seconds = thoughtSeconds(block, replyEndedAt)
  return (
    <div className="flex flex-col gap-2.5">
      <button type="button" aria-expanded={open} aria-controls={id} onClick={() => { setOpen(!open) }} className="flex w-fit items-center gap-2 rounded-6 text-14 font-medium text-text-secondary">
        <Icon icon={Sparkles} className="size-3.75 text-text-tertiary" />
        {seconds === null ? 'Thinking…' : `Thought for ${String(seconds)}s`}
        <Icon icon={ChevronRight} className={cn('size-3.5 text-text-tertiary transition-transform', open && 'rotate-90')} />
      </button>
      {open ? <p id={id} className="border-l-2 py-0.5 pl-3.5 text-14 leading-relaxed whitespace-pre-wrap text-text-tertiary">{block.text}</p> : null}
    </div>
  )
}
