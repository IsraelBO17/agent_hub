import { screen, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { server } from '@/mocks/node'
import { problem } from '@/mocks/responses'
import { CatalogPage } from '@/modules/agents'
import { renderRoute } from '@/test/render-route'

describe('CatalogPage', () => {
  it('lists every agent from the registry; offline ones aren\'t links', async () => {
    renderRoute(<CatalogPage />)
    const [grid] = await screen.findAllByRole('list', { name: 'Agents' })
    if (!grid) throw new Error('no grid')
    expect(within(grid).getByRole('link', { name: 'Research Analyst: new session' })).toHaveAttribute('href', '/agents/research-analyst')
    expect(within(grid).queryByRole('link', { name: /Home Ops/ })).not.toBeInTheDocument()
    expect(within(grid).getByText('Offline since Sep 24')).toBeInTheDocument()
    expect(screen.getByText(/5 registered · 4 available now/)).toBeInTheDocument()
  })

  it('says when no agents are registered, with how to register one', async () => {
    server.use(http.get('*/v1/agents', () => HttpResponse.json({ items: [] })))
    renderRoute(<CatalogPage />)
    expect(await screen.findByRole('heading', { name: 'No agents yet' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'How to register an agent' })).toHaveAttribute('href', expect.stringContaining('AGENT_PROFILE.md'))
  })

  it('shows the error with a reference, and Try again recovers', async () => {
    server.use(http.get('*/v1/agents', () => problem(503, 'internal_error', 'Down'), { once: true }))
    const { user } = renderRoute(<CatalogPage />)
    expect(await screen.findByRole('heading', { name: "Couldn't load your agents" })).toBeInTheDocument()
    expect(screen.getByText('Reference: req_internal_error')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findAllByRole('list', { name: 'Agents' })).toHaveLength(2)
  })
})
