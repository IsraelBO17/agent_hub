import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import type { ReactNode } from 'react'
import { TooltipProvider } from '@/components/ui/tooltip'
import { SessionProvider } from '@/modules/auth'
import { createQueryClient } from '@/provider/query-client'

const queryClient = createQueryClient()

/** App-wide providers (standard §6). The session provider is the auth wiring (issue #6); the Base UI toast provider
 * comes with the first issue that needs a toast (profile: Exceptions). */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <TooltipProvider>
          {children}
        </TooltipProvider>
      </SessionProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
