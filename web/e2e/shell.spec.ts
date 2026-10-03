import { expect, test } from '@playwright/test'
import { expectAccessible } from './axe.ts'

// The shell at the design's sizes (Pencil Sidebar hj5RV, Chat Header H0YWK; mobile drawer F10.5). Sizes are
// compared to the nearest pixel: layout can land a fraction off (316.00001 on CI's runner).
test.describe('desktop', () => {
  test.skip(({ viewport }) => (viewport?.width ?? 0) < 1024, 'desktop only')

  test('the sidebar is 284 px, the chat column about 760, and the catalog has no sidebar', async ({ page }) => {
    await page.goto('/agents/coding-agent')
    await expect(page.getByRole('heading', { level: 1, name: 'New session' })).toBeVisible()
    expect((await page.locator('[data-slot=sidebar-container]').boundingBox())?.width).toBeCloseTo(284, 0)
    expect((await page.locator('[data-page-body=chat]').boundingBox())?.width).toBeCloseTo(760, 0)
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1, name: 'Your agents' })).toBeVisible()
    await expect(page.locator('[data-slot=sidebar-container]')).toHaveCount(0)
    expect((await page.locator('header').first().boundingBox())?.height).toBeCloseTo(64, 0)
  })

  test('collapsing the sidebar leaves a way back', async ({ page }) => {
    await page.goto('/archived')
    const sidebar = page.locator('[data-slot=sidebar-container]')
    await page.getByRole('button', { name: 'Collapse sidebar' }).click()
    await expect(sidebar).toHaveAttribute('inert')
    await page.getByRole('button', { name: 'Open navigation' }).click()
    await expect(sidebar).not.toHaveAttribute('inert')
    await expect(page.getByRole('button', { name: 'Open navigation' })).toHaveCount(0)
  })
})

test.describe('mobile', () => {
  test.skip(({ viewport }) => (viewport?.width ?? 0) >= 768, 'mobile only')

  test('the menu opens the drawer, and a link in it navigates and closes it', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1, name: 'Your agents' })).toBeVisible()
    await page.getByRole('button', { name: 'Open navigation' }).click()
    const drawer = page.getByRole('dialog', { name: 'Navigation' })
    await expect(drawer).toBeVisible()
    expect((await drawer.boundingBox())?.width).toBeCloseTo(316, 0)
    await expectAccessible(page)
    await drawer.getByRole('link', { name: 'Archived' }).click()
    await expect(page.getByRole('heading', { level: 1, name: 'Archived sessions' })).toBeVisible()
    await expect(drawer).toBeHidden()
  })

  test('no page scrolls sideways at 360 px', async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 780 })
    for (const path of ['/', '/agents/coding-agent', '/archived', '/no-such-page']) {
      await page.goto(path)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(360)
    }
  })
})
