// Boot (standard §6): monitoring, mocks when enabled, providers, router. The only wiring.
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router/dom'
import { router } from '@/app/router'
import { initMonitoring, reactErrorHandlers } from '@/lib/monitoring'
import { AppProviders } from '@/provider/app-providers'
import '@/styles/globals.css'

void initMonitoring()

if (import.meta.env.VITE_API_MOCKS === 'true') {
  const { network } = await import('virtual:msw')
  const { handlersFor } = await import('@/mocks/scenarios')
  network.configure({ handlers: handlersFor(new URLSearchParams(location.search).get('scenario')), onUnhandledFrame: 'bypass' })
  await network.enable()
}

const root = document.getElementById('root')
if (!root) throw new Error('index.html has no #root element')

createRoot(root, reactErrorHandlers).render(
  <AppProviders>
    <RouterProvider router={router} />
  </AppProviders>,
)
