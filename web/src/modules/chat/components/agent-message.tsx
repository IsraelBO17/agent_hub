// Design: Agent Message (BsXl7): the agent's avatar, then the reply's blocks in order (thinking, tools, text),
// the typing dots until the first block, and the footer for how it ended (Message Footer / Stopped XebGB, Still
// working K5UJmM, Inline Error Sl1FL / Warning U4HXP).
import { AgentAvatar, type AvatarColor } from '@/components/application/agent-avatar'
import { Icon, Timer } from '@/components/ui/icon'
import type { Block, Message } from '@/models/message'
import { InlineError } from '@/modules/chat/components/inline-error'
import { TextBlock } from '@/modules/chat/components/text-block'
import { ThinkingRow } from '@/modules/chat/components/thinking-row'
import { ToolCall } from '@/modules/chat/components/tool-call'
import { TypingIndicator } from '@/modules/chat/components/typing-indicator'
import { describeError } from '@/service/describe-error'
import { ApiError } from '@/service/api-error'
import { formatDuration } from '@/utils/format-date'

function renderBlock(block: Block, replyEndedAt: Date | null) {
  switch (block.type) {
    case 'text': return <TextBlock key={block.id} text={block.text} />
    case 'thinking': return <ThinkingRow key={block.id} block={block} replyEndedAt={replyEndedAt} />
    case 'tool': return <ToolCall key={block.id} call={block.toolCall} />
    case 'unsupported': return <p key={block.id} className="text-13 text-text-tertiary italic">This content can&apos;t be shown yet.</p>
  }
}

interface Props {
  message: Message
  agent: { color: AvatarColor; icon: string } | undefined
  /** Ms since the last event, when over a minute ("Still working"). */
  quietFor: number
}

export function AgentMessage({ message, agent, quietFor }: Props) {
  const streaming = message.status === 'streaming'
  const visible = message.blocks.filter((b) => b.type !== 'text' || b.text !== '')
  const error = message.error ? describeError(new ApiError({ status: 500, code: message.error.code, message: message.error.title })) : null
  return (
    <article aria-label="Agent reply" aria-busy={streaming} className="flex gap-3.5">
      {agent ? <AgentAvatar color={agent.color} icon={agent.icon} /> : <span className="size-6.5 shrink-0" />}
      <div className="flex min-w-0 flex-1 flex-col gap-3.5 pt-0.5">
        {visible.map((b) => renderBlock(b, streaming ? null : (message.completedAt ?? message.createdAt)))}
        {streaming && visible.length === 0 ? <TypingIndicator /> : null}
        {streaming && quietFor > 0 ? (
          <p role="status" className="flex items-center gap-1.5 text-13 text-text-tertiary">
            <Icon icon={Timer} className="size-3.5" />Still working · {formatDuration(quietFor)}
          </p>
        ) : null}
        {message.status === 'stopped' ? (
          <p className="flex items-center gap-1.5 text-13 text-text-tertiary">
            <span aria-hidden className="size-2.5 rounded-2 bg-text-tertiary" />Stopped
          </p>
        ) : null}
        {message.status === 'failed' ? (
          <InlineError title="Couldn't generate a reply" body={`${error?.message ?? 'The agent returned an error.'} Your message was saved.`} reference={message.error?.requestId} />
        ) : null}
        {message.status === 'interrupted' ? (
          <InlineError tone="warning" title="Interrupted: the reply didn't finish." body={`${error && message.error?.code !== 'run_interrupted' ? `${error.message} ` : ''}The partial reply is saved.`} reference={message.error?.requestId} />
        ) : null}
      </div>
    </article>
  )
}
