// Design: Agent Avatar (vCJQN): the agent's icon on its colour, the only place agent colours appear (profile:
// Colour rules). Sizes from the components that use it: 26 (Chat Header, menus), 30 (Agent Switcher), 42 (mobile
// catalog), 44 (Agent Card).
import { NamedIcon } from '@/components/ui/named-icon'
import { cn } from '@/lib/utils'

export type AvatarColor = 'red' | 'blue' | 'green' | 'purple' | 'amber' | 'grey'

const colors: Record<AvatarColor, string> = {
  red: 'bg-agent-red-bg text-agent-red-fg',
  blue: 'bg-agent-blue-bg text-agent-blue-fg',
  green: 'bg-agent-green-bg text-agent-green-fg',
  purple: 'bg-agent-purple-bg text-agent-purple-fg',
  amber: 'bg-agent-amber-bg text-agent-amber-fg',
  grey: 'bg-agent-grey-bg text-agent-grey-fg',
}

const sizes = {
  xs: ['size-6.5 rounded-7', 'size-3.5'],
  sm: ['size-7.5 rounded-8', 'size-4'],
  md: ['size-10.5 rounded-11', 'size-5'],
  lg: ['size-11 rounded-11', 'size-5.5'],
} as const

export function AgentAvatar({ color, icon, size = 'xs', className }: { color: AvatarColor; icon: string; size?: keyof typeof sizes; className?: string }) {
  const [box, glyph] = sizes[size]
  return (
    <span aria-hidden className={cn('flex shrink-0 items-center justify-center', box, colors[color], className)}>
      <NamedIcon name={icon} className={glyph} />
    </span>
  )
}
