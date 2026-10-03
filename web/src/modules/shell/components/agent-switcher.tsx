// Design: Agent Switcher (RZF5q) and its menu (uBRCZ, F8.2): the current agent, and every agent to switch to. On
// mobile the list is a bottom sheet (F11.10 wE4kz). Picking an agent opens a fresh session with it; offline
// agents can't be picked. The agents come from GET /v1/agents (issue #7). The list itself (agent-picker.tsx)
// loads on first use; until then the trigger is a plain button showing the same face.
import { useQuery } from '@tanstack/react-query'
import { lazy, Suspense, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { AgentAvatar } from '@/components/application/agent-avatar'
import { ChevronsUpDown, Icon } from '@/components/ui/icon'
import { useSidebar } from '@/components/ui/sidebar'
import { currentAgent } from '@/models/agent'
import { useSession } from '@/modules/auth'
import { AgentSwitcherSkeleton } from '@/modules/shell/components/agent-switcher-skeleton'
import { agentsQuery } from '@/service/agents'

const loadPicker = () => import('@/modules/shell/components/agent-picker')
const AgentPicker = lazy(loadPicker)
const preload = () => { void loadPicker() }

const trigger = 'flex w-full items-center gap-2.5 rounded-10 border bg-surface px-2.5 py-2.25 text-left shadow-control'
const statusWords = { online: 'Online', degraded: 'Degraded', offline: 'Offline' } as const

export function AgentSwitcher() {
  const agents = useQuery(agentsQuery())
  const { agentId } = useParams()
  const { user } = useSession()
  const { isMobile, setOpenMobile } = useSidebar()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  // Once loaded, the picker stays mounted, so its trigger keeps focus and the menu can animate closed.
  const [loaded, setLoaded] = useState(false)

  if (agents.isPending) return <AgentSwitcherSkeleton />
  if (agents.isError) {
    return <button type="button" className={`${trigger} text-13 text-text-secondary`} onClick={() => { void agents.refetch() }}>Agents didn&apos;t load · Try again</button>
  }
  const current = currentAgent(agents.data, agentId, user?.defaultAgentSlug ?? null)
  if (!current) return null

  const pick = (slug: string) => {
    setOpen(false)
    if (isMobile) setOpenMobile(false)
    void navigate(`/agents/${slug}`)
  }
  const face = (
    <>
      <AgentAvatar color={current.color} icon={current.icon} size="sm" />
      <span className="flex min-w-0 flex-1 flex-col gap-px">
        <span className="truncate text-14 font-semibold text-text-primary">{current.name}</span>
        <span className="flex items-center gap-1.25 truncate text-12 text-text-tertiary">
          <span aria-hidden className={`size-1.5 rounded-full ${current.status === 'online' ? 'bg-online' : current.status === 'degraded' ? 'bg-busy' : 'bg-offline'}`} />
          {[statusWords[current.status], current.stack.split(' · ')[0]].filter(Boolean).join(' · ')}
        </span>
      </span>
      <Icon icon={ChevronsUpDown} className="size-3.75 text-text-tertiary" />
    </>
  )
  const label = `Agent: ${current.name}. Switch agent`
  const plain = <button type="button" aria-label={label} className={trigger} onPointerEnter={preload} onFocus={preload} onClick={() => { setOpen(true) }}>{face}</button>
  if (!open && !loaded) return plain
  return (
    <Suspense fallback={plain}>
      <AgentPicker agents={agents.data} current={current} mobile={isMobile} open={open} onOpenChange={(next) => { setOpen(next); setLoaded(true) }} onPick={pick} face={face} triggerClassName={trigger} label={label} />
    </Suspense>
  )
}
