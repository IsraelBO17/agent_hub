// Wires the session into the app (standard §14). A refresh that fails while signed in opens the "Session expired"
// dialog over the page (the draft stays); a sign-out in another tab ends the session here, and its drafts go too.
// RequireAuth then sends the user to sign-in, keeping where they were.
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, type ReactNode } from 'react'
import { listenForSignOut } from '@/modules/auth/utils/auth-channel'
import { markExpired } from '@/modules/auth/utils/session-expired'
import { endLocalSession, sessionKeys } from '@/service/auth'
import { onSessionEnd, setAccessToken } from '@/service/client'
import { clearDrafts } from '@/utils/drafts'

export function SessionProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  useEffect(() => {
    onSessionEnd(() => {
      if (!queryClient.getQueryData(sessionKeys.all)) { endLocalSession(queryClient); return }
      setAccessToken(null)
      markExpired()
    })
    return listenForSignOut(() => { clearDrafts(); endLocalSession(queryClient) })
  }, [queryClient])
  return children
}
