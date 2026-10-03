import { EmptyState } from '@/components/ui/empty-state'
import { PageHeader } from '@/components/ui/page-header'
import { PageBody } from '@/components/layout/page-body'
import { ShellBar } from '@/components/layout/shell-bar'
import { AccountSection } from '@/modules/settings/components/account-section'

/** Settings (`/settings`, Pencil RHrDH). The Account section is built (issue #6); the rest is P1. */
export function SettingsPage() {
  return (
    <>
      <title>Settings · Agent Hub</title>
      <ShellBar onlyForNavigation />
      <PageBody kind="workspace" className="gap-7.5">
        <PageHeader title="Settings" description="Your account and your data." />
        <AccountSection />
        <div className="max-w-160"><EmptyState kind="empty" title="More settings later" description="Appearance, your default agent, and your data." /></div>
      </PageBody>
    </>
  )
}
