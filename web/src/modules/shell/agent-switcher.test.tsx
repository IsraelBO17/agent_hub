import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SidebarProvider } from '@/components/ui/sidebar'
import { AgentSwitcher } from '@/modules/shell/components/agent-switcher'
import { renderRoute } from '@/test/render-route'

describe('AgentSwitcher', () => {
  it('shows the URL\'s agent and opens another agent\'s new session', async () => {
    const { user, router } = renderRoute(<SidebarProvider><AgentSwitcher /></SidebarProvider>, { path: '/agents/:agentId', url: '/agents/ledger' })
    await user.click(await screen.findByRole('button', { name: 'Agent: Ledger. Switch agent' }))
    expect(await screen.findByRole('menuitemradio', { name: /Home Ops/ })).toHaveAttribute('aria-disabled', 'true')
    await user.click(screen.getByRole('menuitemradio', { name: /Coding Agent/ }))
    expect(router.state.location.pathname).toBe('/agents/coding-agent')
  })
})
