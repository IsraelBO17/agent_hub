import { useMutation, useQueryClient } from '@tanstack/react-query'
import { forgetGoogleAccount } from '@/lib/google-identity'
import { broadcastSignOut } from '@/modules/auth/utils/auth-channel'
import { noteSignOut } from '@/modules/auth/utils/signed-out-here'
import { signOut } from '@/service/auth'
import { clearDrafts } from '@/utils/drafts'

/** Signs out here and in the app's other tabs; the guard then shows the "You've signed out" sign-in screen. */
export function useSignOut() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => { noteSignOut(); clearDrafts(); return signOut(queryClient) },
    onSuccess: () => {
      forgetGoogleAccount()
      broadcastSignOut()
    },
  })
}
