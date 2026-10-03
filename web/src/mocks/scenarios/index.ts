// Named handler sets chosen with ?scenario=<name> in mock mode (standard §11.5). The first matching
// handler wins, so a scenario lists its overrides before the defaults.
import type { RequestHandler } from 'msw'
import { http } from 'msw/http'
import { delay } from 'msw/utils/delay'
import { handlers } from '@/mocks/handlers'

const scenarios: Record<string, RequestHandler[]> = {
  slow: [http.all('*/v1/*', async () => { await delay(2_000) })],
}

export const scenarioNames = Object.keys(scenarios)

export function handlersFor(name: string | null): RequestHandler[] {
  return [...(name ? (scenarios[name] ?? []) : []), ...handlers]
}
