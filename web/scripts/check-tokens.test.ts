import { describe, expect, it } from 'vitest'
import { findViolations } from './check-tokens.ts'

describe('check-tokens', () => {
  it('flags raw colours, arbitrary font sizes and pixel values', () => {
    const found = findViolations('x.tsx', [
      '<div className="bg-[#fff] text-[17px] w-[300px]" />',
      'const c = "rgb(0 0 0)"',
    ].join('\n'))
    expect(found.map((f) => f.split(': ')[1])).toEqual(['hex colour', 'arbitrary font size', 'arbitrary pixel value', 'colour function'])
  })
  it('allows tokens and anchors', () => {
    expect(findViolations('x.tsx', '<a href="#main" className="text-sm bg-primary w-(--layout-sidebar-width)" />')).toEqual([])
  })
})
