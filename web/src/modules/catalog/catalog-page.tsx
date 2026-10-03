import { PageHeader } from '@/components/ui/page-header'

/** The catalog (`/`, PRODUCT_PLAN §5). A placeholder until issue #7 loads the agents. */
export function CatalogPage() {
  return (
    <>
      <title>All agents · Agent Hub</title>
      <PageHeader title="All agents" description="Pick an agent to start a session." />
    </>
  )
}
