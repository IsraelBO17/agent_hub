// The Agent Switcher's list (uBRCZ, F8.2; mobile F11.10 wE4kz), loaded the first time the switcher is opened:
// Base UI's Menu and Drawer stay out of the first page load (standard §18). Default export, for React.lazy.
import type { ReactNode } from 'react'
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle } from '@/components/ui/drawer'
import { DropdownMenu, DropdownMenuContent, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Icon, Info } from '@/components/ui/icon'
import type { Agent } from '@/models/agent'
import { AgentMenuItemContent } from '@/modules/shell/components/agent-menu-item-content'

interface Props {
  agents: Agent[]
  current: Agent
  mobile: boolean
  open: boolean
  onOpenChange: (open: boolean) => void
  onPick: (slug: string) => void
  /** The switcher's face (avatar, name, status), drawn inside the trigger. */
  face: ReactNode
  triggerClassName: string
  label: string
}

const note = (
  <p className="flex items-center gap-1.5 px-2.25 pt-1.5 pb-1 text-12 text-text-tertiary">
    <Icon icon={Info} className="size-3" />
    Switching opens a fresh session with that agent.
  </p>
)

export default function AgentPicker({ agents, current, mobile, open, onOpenChange, onPick, face, triggerClassName, label }: Props) {
  if (mobile) {
    return (
      <Drawer open={open} onOpenChange={onOpenChange}>
        <button type="button" aria-label={label} className={triggerClassName} onClick={() => { onOpenChange(true) }}>{face}</button>
        <DrawerContent>
          <DrawerHeader className="group-data-[swipe-axis=y]/drawer-popup:text-left"><DrawerTitle>Switch agent</DrawerTitle></DrawerHeader>
          <ul className="flex flex-col gap-0.5 p-3 pb-6">
            {agents.map((agent) => (
              <li key={agent.slug}>
                <button type="button" disabled={!agent.available} aria-current={agent.slug === current.slug} onClick={() => { onPick(agent.slug) }}
                  className="flex min-h-11 w-full items-center gap-2.5 rounded-8 px-2 py-1.75 text-left aria-[current=true]:bg-hover disabled:opacity-50">
                  <AgentMenuItemContent agent={agent} />
                </button>
              </li>
            ))}
          </ul>
          {note}
        </DrawerContent>
      </Drawer>
    )
  }
  return (
    <DropdownMenu open={open} onOpenChange={onOpenChange}>
      <DropdownMenuTrigger aria-label={label} className={triggerClassName}>{face}</DropdownMenuTrigger>
      <DropdownMenuContent className="w-75">
        <DropdownMenuRadioGroup value={current.slug} onValueChange={(slug: string) => { onPick(slug) }}>
          {agents.map((agent) => (
            <DropdownMenuRadioItem key={agent.slug} value={agent.slug} disabled={!agent.available} className="gap-2.5 rounded-8 py-1.75 pr-7 pl-2">
              <AgentMenuItemContent agent={agent} />
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
        {note}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
