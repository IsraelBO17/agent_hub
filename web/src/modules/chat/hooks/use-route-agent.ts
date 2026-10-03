import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'
import { agentQuery } from '@/service/agents'
import { ApiError } from '@/service/api-error'

/** The agent named in the URL (`/agents/:agentId/...`), and whether it doesn't exist. */
export function useRouteAgent() {
  const { agentId = '' } = useParams()
  const query = useQuery(agentQuery(agentId))
  const notFound = query.error instanceof ApiError && (query.error.code === 'agent_not_found' || query.error.status === 404)
  return { slug: agentId, query, notFound }
}
