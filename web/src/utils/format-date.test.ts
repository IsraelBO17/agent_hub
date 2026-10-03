import { describe, expect, it } from 'vitest'
import { formatRelative } from '@/utils/format-date'

describe('formatRelative', () => {
  const now = new Date('2026-10-03T12:00:00Z')
  it('uses the largest whole unit', () => {
    expect(formatRelative(new Date('2026-10-01T12:00:00Z'), now)).toMatch(/2 days ago/)
    expect(formatRelative(new Date('2026-10-03T09:00:00Z'), now)).toMatch(/3 hours ago/)
  })
  it('says now for under a minute', () => {
    expect(formatRelative(new Date('2026-10-03T11:59:40Z'), now)).toMatch(/this minute|now/)
  })
})
