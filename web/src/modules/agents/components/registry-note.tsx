// Design: the catalog's Registry Note (PBQLh).
import { Icon, Info } from '@/components/ui/icon'

export function RegistryNote() {
  return (
    <p className="flex items-center gap-2 text-13 text-text-tertiary">
      <Icon icon={Info} className="size-3.5 shrink-0" />
      Agents are loaded from GET /v1/agents. Register a new agent in the backend and it appears here, no UI changes needed.
    </p>
  )
}
