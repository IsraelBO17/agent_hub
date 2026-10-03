// Design: Catalog (PBQLh); empty j8NhJ; error Jchi9; mobile F10.1 UK1JP, loading F11.1 EP1MN, error sMh7q, empty
// iX1f6. Every agent comes from GET /v1/agents (issue #7); "Continue where you left off" waits for the sessions
// list (owner, 2026-10-03).
import { useQuery } from '@tanstack/react-query'
import { PageBody } from '@/components/layout/page-body'
import { buttonVariants } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { BookOpen, Icon, RotateCw } from '@/components/ui/icon'
import { PageHeader } from '@/components/ui/page-header'
import { AgentCard } from '@/modules/agents/components/agent-card'
import { AgentRow } from '@/modules/agents/components/agent-row'
import { CatalogSkeleton } from '@/modules/agents/components/catalog-skeleton'
import { CopyErrorButton } from '@/modules/agents/components/copy-error-button'
import { RegistryNote } from '@/modules/agents/components/registry-note'
import { agentsQuery } from '@/service/agents'
import { ApiError } from '@/service/api-error'
import { describeError } from '@/service/describe-error'

/** Registering an agent is done in the backend (in-app registration is P2): the docs explain how. */
export const registerDocsUrl = 'https://github.com/IsraelBO17/agent_hub/blob/main/docs/AGENT_PROFILE.md'

const registerLink = (primary: boolean) => (
  <a href={registerDocsUrl} target="_blank" rel="noopener noreferrer" className={buttonVariants({ variant: primary ? 'primary' : 'secondary', className: primary ? '' : 'max-md:hidden' })}>
    <Icon icon={BookOpen} />
    {primary ? 'How to register an agent' : 'Register an agent'}
  </a>
)

export function CatalogPage() {
  const agents = useQuery(agentsQuery())
  const list = agents.data ?? []
  const available = list.filter((a) => a.available).length
  const description = agents.isSuccess
    ? list.length === 0 ? 'Agents come from the registry. None are registered yet.' : `Pick an agent to start a new session. ${String(list.length)} registered · ${String(available)} available now.`
    : 'Pick an agent to start a new session.'

  return (
    <PageBody kind="hub" className="gap-8">
      <title>Your agents · Agent Hub</title>
      <PageHeader title="Your agents" description={description} actions={registerLink(false)} />
      {agents.isPending ? <CatalogSkeleton /> : null}
      {agents.isError ? (
        <div className="flex min-h-96 items-center justify-center rounded-14 border bg-surface p-4">
          <EmptyState
            kind="error"
            title="Couldn't load your agents"
            {...describeError(agents.error)}
            onRetry={() => { void agents.refetch() }}
            action={<CopyErrorButton details={errorDetails(agents.error)} />}
          />
        </div>
      ) : null}
      {agents.isSuccess && list.length === 0 ? (
        <div className="flex min-h-96 items-center justify-center rounded-14 border bg-surface p-4">
          <EmptyState
            kind="empty"
            title="No agents yet"
            description="Agents appear here once they're in the registry. Register one with hub agents add agent.yaml, then reload this page."
            action={<>{registerLink(true)}<button type="button" className={buttonVariants({ variant: 'secondary' })} onClick={() => { void agents.refetch() }}><Icon icon={RotateCw} />Reload</button></>}
          />
        </div>
      ) : null}
      {list.length > 0 ? (
        <>
          <ul aria-label="Agents" className="hidden grid-cols-2 gap-3 md:grid lg:grid-cols-3">
            {list.map((agent) => <li key={agent.slug}><AgentCard agent={agent} /></li>)}
          </ul>
          <ul aria-label="Agents" className="flex flex-col gap-2.5 md:hidden">
            {list.map((agent) => <li key={agent.slug}><AgentRow agent={agent} /></li>)}
          </ul>
        </>
      ) : null}
      <RegistryNote />
    </PageBody>
  )
}

function errorDetails(error: unknown): string {
  if (!(error instanceof ApiError)) return `GET /v1/agents failed: ${String(error)}`
  return `GET /v1/agents failed: ${String(error.status)} ${error.code}${error.requestId ? ` (reference ${error.requestId})` : ''}`
}
