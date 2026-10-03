// Wires the session into the app (standard §14): a refresh that fails mid-session, or a sign-out in another
// tab, ends the session here. RequireAuth then sends the user to sign-in, keeping where they were.
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, type ReactNode } from 'react'
import { listenForSignOut } from '@/modules/auth/utils/auth-channel'
import { endLocalSession } from '@/service/auth'
import { onSessionEnd } from '@/service/client'

export function SessionProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  useEffect(() => {
    onSessionEnd(() => { endLocalSession(queryClient) })
    return listenForSignOut(() => { endLocalSession(queryClient) })
  }, [queryClient])
  return children
}
