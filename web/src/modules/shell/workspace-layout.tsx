// Pages beside the sidebar: an agent's sessions, Artifacts, Archived and Settings (Pencil wtDYF, uBRCZ,
// g2nGvw, HbIFz, RHrDH). Each page renders its own bar (ShellBar or the Chat Header).
import { Outlet } from 'react-router'
import { AppShell } from '@/components/layout/app-shell'
import { AppSidebar } from '@/modules/shell/components/app-sidebar'

export function WorkspaceLayout() {
  return (
    <AppShell sidebar={<AppSidebar />}>
      <Outlet />
    </AppShell>
  )
}
