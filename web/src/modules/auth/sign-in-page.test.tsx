import { screen } from '@testing-library/react'
import { http } from 'msw/http'
import { describe, expect, it } from 'vitest'
import { resetMockSession } from '@/mocks/data/session'
import { server } from '@/mocks/node'
import { problem } from '@/mocks/responses'
import { SignInPage } from '@/modules/auth'
import { renderRoute } from '@/test/render-route'

const signIn = (url = '/sign-in?next=%2Farchived') => {
  resetMockSession(false)
  return renderRoute(<SignInPage />, { path: '/sign-in', url, routes: [{ path: '/archived', element: <h1>Archived sessions</h1> }, { path: '/', element: <h1>Your agents</h1> }] })
}

describe('SignInPage', () => {
  it('signs in with Google and goes where the user was going', async () => {
    const { user } = signIn()
    await user.click(await screen.findByRole('button', { name: 'Continue with Google' }))
    expect(await screen.findByRole('heading', { name: 'Archived sessions' })).toBeInTheDocument()
  })

  it('shows the not-allowed screen with the Google email, and goes back for another account', async () => {
    server.use(http.post('*/v1/auth/google', () => problem(403, 'not_invited', 'No access', { email: 'ada.okafor@example.com' })))
    const { user } = signIn()
    await user.click(await screen.findByRole('button', { name: 'Continue with Google' }))
    expect(await screen.findByRole('heading', { name: "This Google account doesn't have access to Agent Hub" })).toBeInTheDocument()
    expect(screen.getByText('ada.okafor@example.com')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Use a different account' }))
    expect(screen.getByRole('button', { name: 'Continue with Google' })).toBeInTheDocument()
  })

  it('says sign-in didn\'t work when Google is unavailable, and keeps the button', async () => {
    server.use(http.post('*/v1/auth/google', () => problem(503, 'identity_provider_unavailable', 'Google is down')))
    const { user } = signIn()
    await user.click(await screen.findByRole('button', { name: 'Continue with Google' }))
    expect(await screen.findByRole('alert')).toHaveTextContent("Google sign-in isn't answering right now")
    expect(screen.getByRole('button', { name: 'Continue with Google' })).toBeInTheDocument()
  })

  it('confirms a sign-out, and never sends anyone to another site', async () => {
    signIn('/sign-in?signed-out&next=%2F%2Fevil.example')
    expect(await screen.findByText("You've signed out")).toBeInTheDocument()
  })

  it('sends a signed-in user straight on', async () => {
    resetMockSession(true)
    renderRoute(<SignInPage />, { path: '/sign-in', url: '/sign-in', routes: [{ path: '/', element: <h1>Your agents</h1> }] })
    expect(await screen.findByRole('heading', { name: 'Your agents' })).toBeInTheDocument()
  })
})
