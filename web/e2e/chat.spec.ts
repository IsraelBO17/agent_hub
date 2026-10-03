import { expect, test, type Page } from '@playwright/test'
import { expectAccessible } from './axe.ts'

// Chat (issues #8, #9), in mock mode: the MSW "agent" streams a scripted reply (thinking, a tool, Markdown).
const composer = (page: Page) => page.getByRole('textbox', { name: 'Message Research Analyst' })

test('the first message starts a session, the reply streams, and a reload shows it', async ({ page }) => {
  await page.goto('/agents/research-analyst')
  await expect(page.getByRole('heading', { name: 'What should I read for you?' })).toBeVisible()
  await expectAccessible(page)
  await page.getByRole('button', { name: /Summarise a page/ }).click()
  await composer(page).pressSequentially('https://example.com')
  await composer(page).press('Enter')
  await expect(page).toHaveURL(/\/agents\/research-analyst\/[0-9a-f-]{36}$/)
  await expect(page.getByText('Ask me to dig into any of them.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Send' })).toBeVisible()
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Summarise this page')
  await page.getByRole('button', { name: /fetch_url/ }).click()
  await expect(page.getByText('"https://example.com/report"')).toBeVisible()
  await expectAccessible(page)
  await page.reload()
  await expect(page.getByText('Ask me to dig into any of them.')).toBeVisible()
  await expect(page.getByText('Summarise this page in five bullet points: https://example.com', { exact: true }).last()).toBeVisible()
})

test('Stop ends a reply and keeps what arrived', async ({ page }) => {
  await page.goto('/agents/research-analyst?scenario=slow-reply')
  await composer(page).fill('Hello')
  await composer(page).press('Enter')
  await page.getByRole('button', { name: 'Stop generating' }).click()
  await expect(page.getByText('Stopped', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Send' })).toBeVisible()
  await expectAccessible(page)
})

test('a failed reply says so, with its reference', async ({ page }) => {
  await page.goto('/agents/research-analyst?scenario=reply-fails')
  await composer(page).fill('Hello')
  await composer(page).press('Enter')
  await expect(page.getByText("Couldn't generate a reply")).toBeVisible()
  await expect(page.getByText('Reference: req_agent_error')).toBeVisible()
  await expectAccessible(page)
})

test('an offline agent turns the composer off', async ({ page }) => {
  await page.goto('/agents/research-analyst?scenario=agent-offline')
  await expect(composer(page)).toBeDisabled()
  await expect(composer(page)).toHaveAttribute('placeholder', "Research Analyst is offline. You can send when it's back.")
  await expectAccessible(page)
})

test('a draft survives a reload', async ({ page }) => {
  await page.goto('/agents/research-analyst')
  await composer(page).fill('Half a thought')
  await page.reload()
  await expect(composer(page)).toHaveValue('Half a thought')
})
