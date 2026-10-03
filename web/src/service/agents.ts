// The agent registry (contract Agents; F01, F02, D6): the catalog and one agent. Agents are data: nothing in the
// web app lists them.
import { queryOptions } from '@tanstack/react-query'
import { toDomainAgent } from '@/models/agent'
import { unwrap } from '@/service/api-error'
import { api } from '@/service/client'

export const agentKeys = {
  all: ['agents'] as const,
  list: () => [...agentKeys.all, 'list'] as const,
  detail: (slug: string) => [...agentKeys.all, 'detail', slug] as const,
}

/** Status is set by hand in v1 (D23), so a minute is fresh enough; a reload always asks again. */
const staleTime = 60_000

export const agentsQuery = () =>
  queryOptions({
    queryKey: agentKeys.list(),
    queryFn: async ({ signal }) => (await unwrap(api.GET('/v1/agents', { signal }))).items.map(toDomainAgent),
    staleTime,
  })

export const agentQuery = (slug: string) =>
  queryOptions({
    queryKey: agentKeys.detail(slug),
    queryFn: async ({ signal }) => toDomainAgent(await unwrap(api.GET('/v1/agents/{slug}', { params: { path: { slug } }, signal }))),
    staleTime,
  })
