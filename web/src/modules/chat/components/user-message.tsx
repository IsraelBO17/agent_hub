// Design: User Message (EfHME): a right-aligned bubble (max 520, radius 16 with a 4 px tail corner), the time below.
import { textOf, type Message } from '@/models/message'
import { formatTime } from '@/utils/format-date'

export function UserMessage({ message }: { message: Message }) {
  return (
    <div className="flex flex-col items-end gap-1.5">
      <div className="max-w-130 rounded-16 rounded-br-4 bg-surface-muted px-4 py-3 text-15 leading-normal break-words whitespace-pre-wrap text-text-primary">
        {textOf(message)}
      </div>
      <time dateTime={message.createdAt.toISOString()} className="text-12 text-text-tertiary">{formatTime(message.createdAt)}</time>
    </div>
  )
}
