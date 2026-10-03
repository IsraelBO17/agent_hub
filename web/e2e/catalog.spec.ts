import { expect, test } from '@playwright/test'
import { expectAccessible } from './axe.ts'

// The catalog (issue #7), in mock mode: synthetic agents from the MSW registry.
test('the catalog lists the registry\'s agents, and an agent opens its new session', async ({ page, isMobile }) => {
  await page.goto('/')
  const list = page.getByRole('list', { name: 'Agents' }).filter({ visible: true })
  await expect(list.getByText('Research Analyst')).toBeVisible()
  await expect(list.getByText('Home Ops')).toBeVisible()
  await expectAccessible(page)
  await list.getByRole('link', { name: isMobile ? /Coding Agent/ : 'Coding Agent: new session' }).click()
  await expect(page).toHaveURL(/\/agents\/coding-agent$/)
  await expect(page.locator('main').getByText('Coding Agent').first()).toBeVisible()
})

for (const [scenario, heading] of [['no-agents', 'No agents yet'], ['agents-down', "Couldn't load your agents"]] as const) {
  test(`the catalog's ${scenario} state`, async ({ page }) => {
    await page.goto(`/?scenario=${scenario}`)
    await expect(page.getByRole('heading', { name: heading })).toBeVisible()
    await expectAccessible(page)
  })
}

test('an unknown agent in the URL says so', async ({ page }) => {
  await page.goto('/agents/fitness-coach')
  await expect(page.getByRole('heading', { level: 2, name: 'Agent not found' })).toBeVisible()
  await expectAccessible(page)
})

test('the agent switcher opens another agent', async ({ page, isMobile }) => {
  await page.goto('/agents/ledger')
  if (isMobile) await page.getByRole('button', { name: 'Open navigation' }).click()
  await page.getByRole('button', { name: 'Agent: Ledger. Switch agent' }).click()
  const option = isMobile ? page.getByRole('dialog', { name: 'Switch agent' }).getByRole('button', { name: /Coding Agent/ }) : page.getByRole('menuitemradio', { name: /Coding Agent/ })
  await expect(option).toBeVisible()
  await expectAccessible(page)
  await option.click()
  await expect(page).toHaveURL(/\/agents\/coding-agent$/)
})
