import { act, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { resetMockSession } from '@/mocks/data/session'
import { SessionProvider, useSession } from '@/modules/auth'
import { broadcastSignOut } from '@/modules/auth/utils/auth-channel'
import { renderRoute } from '@/test/render-route'

function Status() {
  const { status } = useSession()
  return <p>{status}</p>
}

describe('signing out in another tab', () => {
  it('ends the session here too', async () => {
    renderRoute(<SessionProvider><Status /></SessionProvider>)
    expect(await screen.findByText('signed-in')).toBeInTheDocument()
    expect(typeof BroadcastChannel).toBe('function')
    resetMockSession(false) // the other tab's sign-out revoked the cookie on the server
    act(() => { broadcastSignOut() })
    expect(await screen.findByText('signed-out')).toBeInTheDocument()
  })
})
