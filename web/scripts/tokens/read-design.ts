// Agent Hub's adapter (WEB_PROFILE, Token pipeline): colours and fonts from the Pencil file's variables,
// sizes from design/scale.json. Shadows and layout sizes are read from the Pencil components that scale.json
// names, so no value is copied from the design by hand.
import type { TokenSet } from './token-set.ts'

const pen = '../design/fleet_dev.pen'
const scale = 'design/scale.json'

/** The files the tokens are generated from, relative to web/. `make tokens` reads each one. */
export const sources = [pen, scale]

interface Variable { type: string; value: unknown }
type PenNode = { id?: string; children?: unknown; effect?: unknown } & Record<string, unknown>
interface Effect { type: string; shadowType?: string; enabled?: boolean; offset?: { x: number; y: number }; blur?: number; spread?: number; color?: string }
interface Scale {
  fontSizes: Record<string, number>
  radii: number[]
  shadows: Record<string, string>
  layout: Record<string, { component: string; property: 'width' | 'height' } | number>
  fonts: Record<string, string>
}

const px = (n: number) => (n === 0 ? '0' : `${String(n)}px`)

function nodesById(nodes: unknown, found = new Map<string, PenNode>()): Map<string, PenNode> {
  if (!Array.isArray(nodes)) return found
  for (const n of nodes as PenNode[]) {
    if (typeof n.id === 'string') found.set(n.id, n)
    nodesById(n.children, found)
  }
  return found
}

function component(nodes: Map<string, PenNode>, id: string): PenNode {
  const node = nodes.get(id)
  if (!node) throw new Error(`${scale}: no component ${id} in ${pen}`)
  return node
}

/** A Pencil drop shadow (one effect or several) as a CSS box-shadow value. */
export function toBoxShadow(effect: unknown, where: string): string {
  const effects = (Array.isArray(effect) ? effect : effect ? [effect] : []) as Effect[]
  const shadows = effects.filter((e) => e.type === 'shadow' && e.enabled !== false)
  if (shadows.length === 0) throw new Error(`${where}: has no shadow`)
  return shadows.map((s) => {
    if (typeof s.color !== 'string' || s.color.startsWith('$')) throw new Error(`${where}: shadow colour must be a hex value`)
    const parts = [px(s.offset?.x ?? 0), px(s.offset?.y ?? 0), px(s.blur ?? 0), ...(s.spread ? [px(s.spread)] : []), s.color]
    return `${s.shadowType === 'inner' ? 'inset ' : ''}${parts.join(' ')}`
  }).join(', ')
}

const genericStack = (font: string) => (/mono/i.test(font) ? ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'] : ['ui-sans-serif', 'system-ui', 'sans-serif'])

/** Builds the token set from the sources' contents (`read(path)` returns a file's text). */
export function readSources(read: (path: string) => string): TokenSet {
  const doc = JSON.parse(read(pen)) as { variables?: Record<string, Variable>; children?: unknown }
  const sizes = JSON.parse(read(scale)) as Scale
  const variables = Object.entries(doc.variables ?? {})
  const nodes = nodesById(doc.children)
  const value = (name: string, v: Variable) => {
    if (typeof v.value !== 'string') throw new Error(`${pen}: variable ${name} has themed values; Agent Hub is light only`)
    return v.value
  }
  return {
    colors: variables.filter(([, v]) => v.type === 'color').map(([name, v]) => ({ name, light: value(name, v) })),
    fontFamilies: variables.filter(([name, v]) => v.type === 'string' && name.startsWith('font-')).map(([name, v]) => {
      const family = value(name, v)
      const hosted = sizes.fonts[family]
      return { name: name.slice('font-'.length), stack: [...(hosted ? [hosted] : []), family, ...genericStack(family)] }
    }),
    fontSizes: Object.entries(sizes.fontSizes).map(([size, lineHeight]) => ({ name: size, size: `${size}px`, lineHeight: `${String(lineHeight)}px` })),
    radii: sizes.radii.map((r) => ({ name: String(r), value: `${String(r)}px` })),
    shadows: Object.entries(sizes.shadows).map(([name, id]) => ({ name, value: toBoxShadow(component(nodes, id).effect, `${pen} ${id}`) })),
    layout: Object.entries(sizes.layout).map(([name, from]) => {
      if (typeof from === 'number') return { name, value: `${String(from)}px` }
      const size = component(nodes, from.component)[from.property]
      if (typeof size !== 'number') throw new Error(`${pen} ${from.component}: ${from.property} is not a fixed number`)
      return { name, value: `${String(size)}px` }
    }),
  }
}
