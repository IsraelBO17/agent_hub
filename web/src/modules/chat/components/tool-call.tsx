// Design: Tool Call Chip (Hbhy0), and Tool Call Detail (pkhri) when opened: the tool's input and output.
import { useId, useState } from 'react'
import { ChevronRight, CircleCheck, CircleX, Icon, Loader2 } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import type { ToolCall as ToolCallModel } from '@/models/message'

const show = (value: unknown) => (typeof value === 'string' ? value : JSON.stringify(value, null, 2))

export function ToolCall({ call }: { call: ToolCallModel }) {
  const [open, setOpen] = useState(false)
  const id = useId()
  const running = call.status === 'running' || call.status === 'awaiting_approval'
  const failed = call.status === 'failed' || call.status === 'denied' || call.status === 'cancelled'
  const took = call.completedAt ? `${((call.completedAt.getTime() - call.startedAt.getTime()) / 1000).toFixed(1)}s` : null
  const meta = [call.summary, running ? 'Running' : call.status === 'cancelled' ? 'Cancelled' : took].filter(Boolean).join(' · ')
  const status = running
    ? <Icon icon={Loader2} label="Running" className="size-3.5 animate-spin text-text-tertiary" />
    : failed ? <Icon icon={CircleX} label="Failed" className="size-3.5 text-danger" /> : <Icon icon={CircleCheck} label="Done" className="size-3.5 text-online" />
  return (
    <div className={cn('w-fit max-w-full rounded-8 border bg-surface', open && 'w-full rounded-10')}>
      <button type="button" aria-expanded={open} aria-controls={id} onClick={() => { setOpen(!open) }} className={cn('flex w-full items-center gap-2 px-2.5 py-1.5 text-left', open && 'border-b px-3 py-2.25')}>
        {status}
        <span className="font-mono text-13 font-medium text-text-primary">{call.name}</span>
        {meta ? <span className="min-w-0 flex-1 truncate text-12 text-text-tertiary">{meta}</span> : null}
        <Icon icon={ChevronRight} className={cn('size-3.5 shrink-0 text-text-tertiary transition-transform', open && 'rotate-90')} />
      </button>
      {open ? (
        <div id={id} className="flex flex-col gap-px bg-border">
          {[['Input', call.input], ['Output', call.error ?? call.output]].map(([label, value]) => (
            <div key={label as string} className="flex flex-col gap-1.5 bg-bg px-3 py-2.5">
              <span className="text-12 font-semibold tracking-wide text-text-tertiary uppercase">{label as string}</span>
              <pre className="overflow-x-auto font-mono text-12 leading-normal whitespace-pre-wrap text-text-secondary">{value === null || value === undefined ? '—' : show(value)}</pre>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}
