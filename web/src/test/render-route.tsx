// Renders a screen as the app does: a fresh query client (no retries), the URL-state adapter and a
// memory router (standard §22).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NuqsAdapter } from 'nuqs/adapters/react-router/v8'
import type { ReactElement } from 'react'
import { createMemoryRouter, type RouteObject } from 'react-router'
import { RouterProvider } from 'react-router/dom'

interface Options {
  path?: string
  url?: string
  /** Other routes the screen navigates to, e.g. `{ path: '/', element: <p>List</p> }`. */
  routes?: RouteObject[]
  user?: Parameters<typeof userEvent.setup>[0]
}

export function renderRoute(element: ReactElement, { path = '/', url, routes = [], user }: Options = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  const router = createMemoryRouter([{ path, element: <NuqsAdapter>{element}</NuqsAdapter> }, ...routes], { initialEntries: [url ?? path] })
  return {
    user: userEvent.setup(user),
    router,
    queryClient,
    ...render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    ),
  }
}
