import { describe, expect, it } from 'vitest'
import { blocking, parseExceptions } from './check-audit.ts'

const table = `| Advisory | Reason | Owner | Expires |
|---|---|---|---|
| GHSA-aaaa-bbbb-cccc | Not reachable: build-time only | Owner | 2026-12-31 |
| GHSA-dddd-eeee-ffff | Old | Owner | 2026-01-01 |`

const vulns = {
  braces: { name: 'braces', severity: 'high', via: [{ url: 'https://github.com/advisories/GHSA-aaaa-bbbb-cccc', severity: 'high' }] },
  other: { name: 'other', severity: 'high', via: [{ url: 'https://github.com/advisories/GHSA-dddd-eeee-ffff', severity: 'high' }] },
  low: { name: 'low', severity: 'low', via: [{ url: 'https://github.com/advisories/GHSA-1111-2222-3333', severity: 'low' }] },
}

describe('check-audit', () => {
  it('reads the exceptions table', () => {
    expect(parseExceptions(table)).toEqual([{ id: 'GHSA-aaaa-bbbb-cccc', expires: '2026-12-31' }, { id: 'GHSA-dddd-eeee-ffff', expires: '2026-01-01' }])
  })
  it('blocks high advisories unless accepted and unexpired', () => {
    expect(blocking(vulns, parseExceptions(table), '2026-10-03')).toEqual(['other: GHSA-dddd-eeee-ffff'])
  })
})
