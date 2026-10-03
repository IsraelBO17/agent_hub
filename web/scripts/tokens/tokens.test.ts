import { describe, expect, it } from 'vitest'
import { readSources, sources, toBoxShadow } from './read-design.ts'
import { writeCss, writeNames } from './write-css.ts'

// A tiny Pencil file and scale.json: the adapter's inputs (WEB_PROFILE, Token pipeline).
const pen = {
  variables: {
    accent: { type: 'color', value: '#1F5C4A' },
    'font-ui': { type: 'string', value: 'Inter' },
    'font-mono': { type: 'string', value: 'JetBrains Mono' },
  },
  children: [
    { id: 'lib', type: 'frame', children: [
      { id: 'seg', type: 'frame', effect: { type: 'shadow', shadowType: 'outer', color: '#0000000F', offset: { x: 0, y: 1 }, blur: 2 } },
      { id: 'side', type: 'frame', width: 284 },
    ] },
  ],
}
const scale = {
  fontSizes: { '13': 18 },
  radii: [9],
  shadows: { control: 'seg' },
  layout: { 'sidebar-width': { component: 'side', property: 'width' }, 'chat-width': 760 },
  fonts: { Inter: 'Inter Variable' },
}
const files: Record<string, unknown> = { '../design/fleet_dev.pen': pen, 'design/scale.json': scale }
const read = (path: string) => JSON.stringify(files[path])

describe('Pencil tokens', () => {
  it('reads colours and fonts from the variables, sizes from scale.json and the named components', () => {
    const set = readSources(read)
    expect(set.colors).toEqual([{ name: 'accent', light: '#1F5C4A' }])
    expect(set.fontFamilies[0]).toEqual({ name: 'ui', stack: ['Inter Variable', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] })
    expect(set.fontFamilies[1]?.stack.slice(0, 2)).toEqual(['JetBrains Mono', 'ui-monospace'])
    expect(set.fontSizes).toEqual([{ name: '13', size: '13px', lineHeight: '18px' }])
    expect(set.shadows).toEqual([{ name: 'control', value: '0 1px 2px #0000000F' }])
    expect(set.layout).toEqual([{ name: 'sidebar-width', value: '284px' }, { name: 'chat-width', value: '760px' }])
  })

  it('writes numeric type, radius and shadow names, replacing Tailwind\'s scales', () => {
    const css = writeCss(readSources(read), sources)
    expect(css).toContain('--text-*: initial;')
    expect(css).toContain('--text-13: 0.8125rem;')
    expect(css).toContain('--text-13--line-height: 1.125rem;')
    expect(css).toContain('--radius-*: initial;')
    expect(css).toContain('--radius-9: 0.5625rem;')
    expect(css).toContain('--shadow-control: 0 1px 2px #0000000F;')
    expect(css).toContain('--font-ui: "Inter Variable", Inter, ui-sans-serif')
    expect(css).not.toContain('.dark')
    expect(writeNames(readSources(read), sources)).toContain("fontSizes: readonly string[] = ['13']")
  })

  it('turns several shadows into one box-shadow, and rejects a missing or token colour', () => {
    expect(toBoxShadow([
      { type: 'shadow', color: '#1B1A1733', offset: { x: 0, y: 24 }, blur: 60 },
      { type: 'shadow', shadowType: 'inner', color: '#1B1A170F', offset: { x: 0, y: 2 }, blur: 6, spread: 1 },
    ], 'x')).toBe('0 24px 60px #1B1A1733, inset 0 2px 6px 1px #1B1A170F')
    expect(() => toBoxShadow(undefined, 'x')).toThrow(/no shadow/)
    expect(() => toBoxShadow({ type: 'shadow', color: '$scrim' }, 'x')).toThrow(/hex/)
  })

  it('fails loudly when scale.json names a component the file doesn\'t have', () => {
    files['design/scale.json'] = { ...scale, shadows: { control: 'gone' } }
    expect(() => readSources(read)).toThrow(/no component gone/)
    files['design/scale.json'] = scale
  })
})
