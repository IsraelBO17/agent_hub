import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { NewSessionPage } from '@/modules/chat'
import { renderRoute } from '@/test/render-route'
import { SidebarProvider } from '@/components/ui/sidebar'

const page = (slug: string) => renderRoute(<SidebarProvider><NewSessionPage /></SidebarProvider>, { path: '/agents/:agentId', url: `/agents/${slug}` })

describe('an agent in the URL', () => {
  it('shows the agent in the chat header', async () => {
    page('coding-agent')
    expect(await screen.findByText('Coding Agent')).toBeInTheDocument()
  })

  it('says when the agent doesn\'t exist', async () => {
    page('fitness-coach')
    expect(await screen.findByRole('heading', { name: 'Agent not found', level: 2 })).toBeInTheDocument()
    expect(screen.getByText(/No agent with the id “fitness-coach”/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Browse agents' })).toHaveAttribute('href', '/')
  })
})
