// The session resource (D8, contract Auth and Me): who is signed in, signing in with a Google ID token, and
// signing out. The tokens themselves are handled in service/client.ts.
import { queryOptions, type QueryClient } from '@tanstack/react-query'
import { toDomainUser, type User } from '@/models/user'
import { unwrap } from '@/service/api-error'
import { api, authClient, hasAccessToken, refreshSession, setAccessToken } from '@/service/client'

export const sessionKeys = { all: ['session'] as const }

/**
 * The signed-in user, or null when signed out. The first read restores the session from the refresh cookie
 * (once, on load); after that it's set by sign-in and sign-out, so it never goes stale on its own.
 */
export const sessionQuery = () =>
  queryOptions({
    queryKey: sessionKeys.all,
    queryFn: async ({ signal }): Promise<User | null> => {
      if (!hasAccessToken() && !(await refreshSession())) return null
      return toDomainUser(await unwrap(api.GET('/v1/me', { signal })))
    },
    staleTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
  })

export const signInMutation = (queryClient: QueryClient) => ({
  mutationFn: async (idToken: string) => {
    const session = await unwrap(authClient.POST('/v1/auth/google', { body: { idToken } }))
    setAccessToken(session.accessToken)
    return toDomainUser(session.user)
  },
  onSuccess: (user: User) => { queryClient.setQueryData(sessionKeys.all, user) },
})

/** Signs out on this device. The API call is best effort: the local session ends whatever it answers. */
export async function signOut(queryClient: QueryClient) {
  await authClient.POST('/v1/auth/logout').catch(() => undefined)
  endLocalSession(queryClient)
}

/**
 * Forgets the session here: the token, the user, and every other cached response. The session query is set
 * rather than removed, so the screens watching it see "signed out" (clearing the whole cache would detach them).
 */
export function endLocalSession(queryClient: QueryClient) {
  setAccessToken(null)
  queryClient.setQueryData(sessionKeys.all, null)
  void queryClient.cancelQueries({ predicate: (q) => q.queryKey[0] !== sessionKeys.all[0] })
  queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== sessionKeys.all[0] })
}
