import { NuqsAdapter } from 'nuqs/adapters/react-router/v8'
import { Outlet } from 'react-router'
import { useFocusOnNavigate } from '@/hooks/use-focus-on-navigate'

/** The root route: URL state and focus after navigation. The shell is chosen by HubLayout or WorkspaceLayout. */
export function RootLayout() {
  useFocusOnNavigate()
  return (
    <NuqsAdapter>
      <Outlet />
    </NuqsAdapter>
  )
}
