import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '@/service/api-error'

/** Retry once, except for client errors that won't change on a retry (standard §11.3). */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= 1) return false
  if (error instanceof ApiError && error.status < 500) return error.status === 408 || error.status === 429
  return true
}

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: shouldRetry, refetchOnWindowFocus: true },
      mutations: { retry: 0 },
    },
  })
}
