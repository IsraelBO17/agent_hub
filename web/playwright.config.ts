// End-to-end, in mock mode, at desktop and mobile widths (standard §22). The profile sets the widths.
import { defineConfig, devices } from '@playwright/test'

const port = 4173
// Set PLAYWRIGHT_BASE_URL to run against a deployment instead of a local mocked build (recipe 9).
const deployed = process.env.PLAYWRIGHT_BASE_URL

export default defineConfig({
  testDir: './e2e',
  outputDir: './artifacts/test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['github'], ['html', { outputFolder: 'artifacts/playwright-report', open: 'never' }]] : 'list',
  use: { baseURL: deployed ?? `http://localhost:${String(port)}`, trace: 'on-first-retry' },
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.01, animations: 'disabled', caret: 'hide' } },
  // The profile's widths: the design's desktop and mobile frames, and a tablet in between.
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1024 } } },
    { name: 'tablet', use: { ...devices['Desktop Chrome'], viewport: { width: 768, height: 1024 } } },
    { name: 'mobile', use: { ...devices['Pixel 7'], viewport: { width: 390, height: 844 } } },
  ],
  webServer: deployed ? undefined : {
    command: 'npm run build && npm run preview',
    url: `http://localhost:${String(port)}`,
    env: { VITE_API_MOCKS: 'true', VITE_API_URL: `http://localhost:${String(port)}` },
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
})
