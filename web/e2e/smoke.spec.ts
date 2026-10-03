import { expect, test } from '@playwright/test'
import { expectAccessible } from './axe.ts'

// Every route loads, by deep link, with no console errors and no blocking accessibility issues.
const routes: { path: string; heading: string; apiStatus?: number }[] = [
  { path: '/', heading: 'Your agents' },
  { path: '/agents/coding-agent', heading: 'New session' },
  { path: '/agents/coding-agent/0b6a5f1e-2c1d-4e57-9d0b-7a1c9d3e4f21', heading: 'Session' },
  { path: '/agents/coding-agent/about', heading: 'About this agent' },
  { path: '/artifacts', heading: 'Artifacts' },
  { path: '/archived', heading: 'Archived sessions' },
  { path: '/settings', heading: 'Settings' },
  { path: '/s/share-1', heading: 'Shared session' },
  { path: '/sign-in', heading: 'Your agents' }, // signed in (the mocks' default), sign-in sends you on
  { path: '/no-such-page', heading: 'Page not found' },
]

for (const { path, heading, apiStatus } of routes) {
  test(`${path} loads by deep link and is accessible`, async ({ page }) => {
    const errors: string[] = []
    // The browser logs every failed response; one the screen expects (a 404 it renders) isn't an error.
    const expected = apiStatus ? `status of ${String(apiStatus)}` : null
    page.on('console', (m) => { if (m.type() === 'error' && !(expected && m.text().includes(expected))) errors.push(m.text()) })
    await page.goto(path)
    await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible()
    await expectAccessible(page)
    expect(errors).toEqual([])
  })
}

test('the skip link is the first stop and jumps to the content', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1, name: 'Your agents' })).toBeVisible()
  await page.keyboard.press('Tab')
  const skip = page.getByRole('link', { name: 'Skip to content' })
  await expect(skip).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('#main')).toBeFocused()
})
