// Design: Composer (K6k66O; mobile OUcXN) and Composer Disclaimer (QTWM6). Enter sends, Shift + Enter adds a line;
// while a reply runs, Send becomes "Stop generating". Attachments and voice wait for their issues (M2).
import type { KeyboardEvent, Ref } from 'react'
import { ArrowUp, Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'

interface Props {
  agentName: string
  disclaimer: string | null
  /** Off until the agent has loaded. */
  showDisclaimer: boolean
  text: string
  onTextChange: (text: string) => void
  onSend: () => void
  onStop: () => void
  /** A reply is running: show Stop. */
  running: boolean
  /** The message is on its way and not yet saved. */
  sending: boolean
  stopping: boolean
  /** Why the composer can't be used (e.g. the agent is offline), shown as its placeholder. */
  disabledReason: string | null
  textareaRef?: Ref<HTMLTextAreaElement>
}

export function Composer({ agentName, disclaimer, showDisclaimer, text, onTextChange, onSend, onStop, running, sending, stopping, disabledReason, textareaRef }: Props) {
  const disabled = disabledReason !== null
  const canSend = !disabled && !running && !sending && text.trim() !== ''
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Enter' || e.shiftKey || e.nativeEvent.isComposing) return
    e.preventDefault()
    if (canSend) onSend()
  }
  return (
    <div className="flex flex-col gap-2">
      <form
        onSubmit={(e) => { e.preventDefault(); if (canSend) onSend() }}
        className={cn('flex items-end gap-2 rounded-16 border bg-surface p-2.5 pl-4 shadow-raised has-focus-visible:border-control-border sm:flex-col sm:items-stretch sm:gap-2.5 sm:p-3.5 sm:pl-4', disabled && 'bg-surface-muted shadow-none')}
      >
        <textarea
          ref={textareaRef}
          aria-label={`Message ${agentName}`}
          placeholder={disabledReason ?? `Message ${agentName}…`}
          value={text}
          disabled={disabled}
          rows={1}
          onChange={(e) => { onTextChange(e.target.value) }}
          onKeyDown={onKeyDown}
          className="field-sizing-content max-h-50 min-h-6 w-full resize-none self-center bg-transparent text-15 leading-normal text-text-primary outline-none placeholder:text-text-tertiary focus-visible:outline-none disabled:cursor-not-allowed"
        />
        <div className="flex shrink-0 items-center justify-between gap-3">
          <p className={cn('hidden text-12 text-text-tertiary sm:block', disabled && 'invisible')}>Shift + Enter for a new line</p>
          {running ? (
            <button type="button" onClick={onStop} disabled={stopping} aria-label={stopping ? 'Stopping' : 'Stop generating'} className="ml-auto flex h-8.5 items-center gap-2 rounded-9 bg-text-primary px-3 text-13 text-bg disabled:opacity-60 sm:h-7.5">
              <span aria-hidden className="size-2.25 rounded-2 bg-bg" /><span aria-hidden className="hidden sm:inline">{stopping ? 'Stopping…' : 'Stop generating'}</span>
            </button>
          ) : (
            <button type="submit" aria-label="Send" disabled={!canSend} className="ml-auto flex size-8.5 items-center justify-center rounded-9 bg-accent text-on-accent disabled:opacity-40">
              <Icon icon={ArrowUp} className="size-4.25" />
            </button>
          )}
        </div>
      </form>
      <p className={cn('min-h-4 text-center text-12 text-text-tertiary', !showDisclaimer && 'invisible')}>{agentName} can make mistakes.{disclaimer ? ` ${disclaimer}` : ''}</p>
    </div>
  )
}
