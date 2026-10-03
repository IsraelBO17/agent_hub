import { expect, test } from '@playwright/test'
import { expectAccessible } from './axe.ts'

// Sign-in (issue #6), in mock mode: the mock Google button sends a credential MSW accepts for the invited user.
test('a deep link while signed out returns there after sign-in', async ({ page }) => {
  await page.goto('/archived?scenario=signed-out')
  await expect(page).toHaveURL(/\/sign-in\?next=%2Farchived/)
  await expect(page.getByRole('heading', { level: 1, name: 'Agent Hub' })).toBeVisible()
  await expectAccessible(page)
  await page.getByRole('button', { name: 'Continue with Google' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Archived sessions' })).toBeVisible()
  await expect(page).toHaveURL(/\/archived\?scenario=signed-out$/) // next keeps the query
})

test('an account that isn\'t invited sees the not-allowed screen, and can try another', async ({ page }) => {
  await page.goto('/sign-in?scenario=not-invited')
  await page.getByRole('button', { name: 'Continue with Google' }).click()
  await expect(page.getByRole('heading', { level: 1, name: "This Google account doesn't have access to Agent Hub" })).toBeVisible()
  await expect(page.getByText('ada.okafor@example.com')).toBeVisible()
  await expectAccessible(page)
  await page.getByRole('button', { name: 'Use a different account' }).click()
  await expect(page.getByRole('button', { name: 'Continue with Google' })).toBeVisible()
})

test('when Google is down, sign-in says so and keeps the button', async ({ page }) => {
  await page.goto('/sign-in?scenario=google-down')
  await page.getByRole('button', { name: 'Continue with Google' }).click()
  await expect(page.getByRole('alert')).toContainText("Google sign-in isn't answering right now")
  await expectAccessible(page)
})

test('signing out from Settings shows the signed-out screen, and the app needs sign-in again', async ({ page }) => {
  await page.goto('/settings')
  await expect(page.getByText('Ada Owner').first()).toBeVisible()
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByText("You've signed out")).toBeVisible()
  await expectAccessible(page)
  // Go to a signed-in page inside the app: the session is gone, so the guard returns to sign-in. (A reload would
  // restart the mock API, which starts signed in; the real API has revoked the cookie.)
  await page.evaluate(() => { history.pushState(null, '', '/archived'); dispatchEvent(new PopStateEvent('popstate')) })
  await expect(page).toHaveURL(/\/sign-in/)
  await expect(page.getByRole('button', { name: 'Continue with Google' })).toBeVisible()
})
