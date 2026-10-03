import { screen } from '@testing-library/react'
import { Outlet } from 'react-router'
import { describe, expect, it } from 'vitest'
import { resetMockSession } from '@/mocks/data/session'
import { RequireAuth } from '@/modules/auth'
import { renderRoute } from '@/test/render-route'

const guarded = (url: string) => renderRoute(<Outlet />, {
  path: '/',
  url,
  routes: [
    { element: <RequireAuth />, children: [{ path: '/archived', element: <h1>Archived sessions</h1> }] },
    { path: '/sign-in', element: <h1>Sign in</h1> },
  ],
})

describe('RequireAuth', () => {
  it('restores the session from the cookie and shows the page', async () => {
    guarded('/archived')
    expect(await screen.findByRole('heading', { name: 'Archived sessions' })).toBeInTheDocument()
  })

  it('sends a signed-out user to sign-in, keeping where they were going', async () => {
    resetMockSession(false)
    const { router } = guarded('/archived?view=all')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/sign-in')
    expect(new URLSearchParams(router.state.location.search).get('next')).toBe('/archived?view=all')
  })
})
