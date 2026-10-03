import { useQuery } from '@tanstack/react-query'
import type { User } from '@/models/user'
import { sessionQuery } from '@/service/auth'

export type SessionStatus = 'restoring' | 'signed-in' | 'signed-out' | 'error'

/** The current user and where the session stands. `useSession` is the only auth surface screens use (F13). */
export function useSession(): { status: SessionStatus; user: User | null; error: unknown; retry: () => void } {
  const query = useQuery(sessionQuery())
  const retry = () => { void query.refetch() }
  if (query.isPending) return { status: 'restoring', user: null, error: null, retry }
  if (query.isError) return { status: 'error', user: null, error: query.error, retry }
  return { status: query.data ? 'signed-in' : 'signed-out', user: query.data, error: null, retry }
}
