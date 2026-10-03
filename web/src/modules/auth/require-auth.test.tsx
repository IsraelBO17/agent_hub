import { screen } from '@testing-library/react'
import { Outlet } from 'react-router'
import { describe, expect, it } from 'vitest'
import { resetMockSession } from '@/mocks/data/session'
import { RequireAuth, SessionProvider } from '@/modules/auth'
import { api } from '@/service/client'
import { renderRoute } from '@/test/render-route'
import { readDraft, writeDraft } from '@/utils/drafts'

const guarded = (url: string) => renderRoute(<Outlet />, {
  path: '/',
  url,
  routes: [
    { element: <SessionProvider><RequireAuth /></SessionProvider>, children: [{ path: '/archived', element: <h1>Archived sessions</h1> }] },
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

  describe('when the session runs out mid-use', () => {
    const expire = async () => {
      await screen.findByRole('heading', { name: 'Archived sessions' })
      resetMockSession(false) // the refresh cookie is gone, and the access token no longer works
      await api.GET('/v1/me')
    }

    it('opens "Session expired" over the page and keeps the draft', async () => {
      writeDraft('s1', 'Unsent words')
      const { user, router } = guarded('/archived')
      await expire()
      expect(await screen.findByRole('dialog', { name: 'Your sign-in has expired' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: 'Archived sessions', hidden: true })).toBeInTheDocument()
      await user.click(screen.getByRole('button', { name: 'Continue with Google' }))
      expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
      expect(new URLSearchParams(router.state.location.search).get('next')).toBe('/archived')
      expect(readDraft('s1')).toBe('Unsent words')
    })

    it('can be dismissed, leaving the page as it was', async () => {
      const { user } = guarded('/archived')
      await expire()
      await user.click(await screen.findByRole('button', { name: 'Cancel' }))
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      expect(screen.getByRole('heading', { name: 'Archived sessions' })).toBeInTheDocument()
    })
  })
})
