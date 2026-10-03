import { useMutation, useQueryClient } from '@tanstack/react-query'
import { forgetSignOut } from '@/modules/auth/utils/signed-out-here'
import { signInMutation } from '@/service/auth'

/** Exchanges a Google ID token for the app's session. */
export function useSignIn() {
  const queryClient = useQueryClient()
  const mutation = signInMutation(queryClient)
  return useMutation({ ...mutation, onSuccess: (user: Parameters<typeof mutation.onSuccess>[0]) => { forgetSignOut(); mutation.onSuccess(user) } })
}
