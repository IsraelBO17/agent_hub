import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { PageBody } from '@/components/layout/page-body'
import { ShellBar } from '@/components/layout/shell-bar'

/** Settings (`/settings`, Pencil RHrDH, P1). A placeholder until it is built. */
export function SettingsPage() {
  return (
    <>
      <title>Settings · Agent Hub</title>
      <ShellBar onlyForNavigation />
      <PageBody kind="workspace">
        <PageHeader title="Settings" description="Your account and your data." />
        <EmptyState kind="empty" title="Coming later" description="Your Google account, signing out, and deleting your data." />
      </PageBody>
    </>
  )
}
