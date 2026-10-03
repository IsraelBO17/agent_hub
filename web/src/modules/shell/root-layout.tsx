import { NuqsAdapter } from 'nuqs/adapters/react-router/v8'
import { Outlet } from 'react-router'
import { AppShell } from '@/components/layout/app-shell'
import { useFocusOnNavigate } from '@/hooks/use-focus-on-navigate'
import { navSections } from '@/modules/shell/nav'

export function RootLayout() {
  useFocusOnNavigate()
  return (
    <NuqsAdapter>
      <AppShell brand={<span className="text-base font-semibold">Agent Hub</span>} sections={navSections}>
        <Outlet />
      </AppShell>
    </NuqsAdapter>
  )
}
