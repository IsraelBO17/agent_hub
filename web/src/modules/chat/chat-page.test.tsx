import { screen, waitFor } from '@testing-library/react'
import { http } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { SidebarProvider } from '@/components/ui/sidebar'
import { chatStore, newSession, startRun } from '@/mocks/data/chat'
import { seedAgents } from '@/mocks/data/agents'
import { chatHandlers } from '@/mocks/handlers/chat'
import { server } from '@/mocks/node'
import { problem } from '@/mocks/responses'
import { ChatRoute } from '@/modules/chat'
import { renderRoute } from '@/test/render-route'
import { HttpResponse } from 'msw'

const chat = (url = '/agents/research-analyst') =>
  renderRoute(<SidebarProvider><ChatRoute /></SidebarProvider>, { path: '/agents/:agentId/:sessionId?', url })

const composer = () => screen.findByRole('textbox', { name: 'Message Research Analyst' })

describe('chat', () => {
  it('starts a session with the first message and streams the reply', async () => {
    const { user, router } = chat()
    expect(await screen.findByRole('heading', { name: 'What should I read for you?' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Summarise a page/ }))
    const box = await composer()
    expect(box).toHaveValue('Summarise this page in five bullet points: ')
    await user.type(box, 'https://example.com{Enter}')
    expect(await screen.findByText('Summarise this page in five bullet points: https://example.com', { selector: 'div' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Summarise this page')
    expect(await screen.findByText('Ask me to dig into any of them.', {}, { timeout: 4000 })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /fetch_url/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Thought for \d+s/ })).toBeInTheDocument()
    const [session] = [...chatStore.sessions.keys()]
    expect(router.state.location.pathname).toBe(`/agents/research-analyst/${session ?? ''}`)
    expect(box).toHaveValue('')
    expect(box).toHaveFocus()
  })

  it('shows the error when the reply fails, keeping the message', async () => {
    server.use(...chatHandlers({ failAfterThinking: true }))
    const { user } = chat()
    await user.type(await composer(), 'Hello{Enter}')
    expect(await screen.findByText("Couldn't generate a reply", {}, { timeout: 4000 })).toBeInTheDocument()
    expect(screen.getByText('Reference: req_agent_error')).toBeInTheDocument()
    expect(screen.getByText('Hello', { selector: 'div' })).toBeInTheDocument()
  })

  it('keeps the draft when the send is refused', async () => {
    const session = newSession('research-analyst', 'Earlier')
    server.use(http.post('*/v1/sessions/:sessionId/messages', () => problem(409, 'run_in_progress', 'A reply is still running')))
    const { user } = chat(`/agents/research-analyst/${session.summary.id}`)
    await user.type(await composer(), 'Again{Enter}')
    expect(await screen.findByText("Your message wasn't sent")).toBeInTheDocument()
    expect(screen.getByText(/A reply is still running in this session/)).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Message Research Analyst' })).toHaveValue('Again')
  })

  it('turns the composer off while the agent is offline', async () => {
    server.use(http.get('*/v1/agents/research-analyst', () => HttpResponse.json({ ...seedAgents()[0], status: 'offline' })))
    chat()
    const box = await composer()
    await waitFor(() => { expect(box).toBeDisabled() })
    expect(box).toHaveAttribute('placeholder', "Research Analyst is offline. You can send when it's back.")
  })

  it('stops a reply with Esc and keeps what arrived', async () => {
    server.use(...chatHandlers({ gapMs: 150 }))
    const { user } = chat()
    await user.type(await composer(), 'Hello{Enter}')
    await screen.findByRole('button', { name: 'Stop generating' })
    await user.keyboard('{Escape}')
    expect(await screen.findByText('Stopped', {}, { timeout: 4000 })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument()
  })

  it('follows a reply that was already running when the page opened', async () => {
    const session = newSession('research-analyst', 'Running')
    startRun(session, crypto.randomUUID(), 'Started elsewhere', { gapMs: 20 })
    chat(`/agents/research-analyst/${session.summary.id}`)
    expect(await screen.findByText('Started elsewhere', { selector: 'div' })).toBeInTheDocument()
    expect(await screen.findByText('Ask me to dig into any of them.', {}, { timeout: 6000 })).toBeInTheDocument()
  }, 10_000)

  it('says when the session does not exist', async () => {
    chat('/agents/research-analyst/00000000-0000-4000-8000-000000000000')
    expect(await screen.findByRole('heading', { name: 'Session not found' })).toBeInTheDocument()
  })
})
