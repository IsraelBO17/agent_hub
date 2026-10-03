import { describe, expect, it } from 'vitest'
import { readDesign } from './read-design.ts'
import { writeCss } from './write-css.ts'

const design = {
  color: { brand: { $type: 'color', $value: '#2f54d1', $extensions: { dark: '#7c96f2' } }, line: { $type: 'color', $value: '#e2e5ea' } },
  'font-family': { sans: { $value: ['Geist Variable', 'sans-serif'] } },
  'font-size': { sm: { $value: '14px', $extensions: { lineHeight: '20px' } } },
  radius: { base: { $value: '10px' } },
  layout: { 'sidebar-width': { $value: '256px' } },
}

describe('design tokens', () => {
  it('reads DTCG groups into a token set', () => {
    const set = readDesign(design)
    expect(set.colors).toEqual([{ name: 'brand', light: '#2f54d1', dark: '#7c96f2' }, { name: 'line', light: '#e2e5ea', dark: undefined }])
    expect(set.fontSizes).toEqual([{ name: 'sm', size: '14px', lineHeight: '20px' }])
  })

  it('writes Tailwind theme variables, replacing the default type scale', () => {
    const css = writeCss(readDesign(design), 'design/tokens.json')
    expect(css).toContain('--text-*: initial;')
    expect(css).toContain('--text-sm: 0.875rem;')
    expect(css).toContain('--text-sm--line-height: 1.25rem;')
    expect(css).toContain('--font-sans: "Geist Variable", sans-serif;')
    expect(css).toContain('--radius-base: 0.625rem;')
    expect(css).toContain('--layout-sidebar-width: 256px;')
    expect(css).toMatch(/\.dark \{\n {2}--color-brand: #7c96f2;\n\}/)
  })

  it('rejects a token without a value it needs', () => {
    expect(() => readDesign({ 'font-size': { sm: { $value: '14px' } } })).toThrow(/lineHeight/)
  })
})
