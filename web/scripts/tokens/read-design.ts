// Adapter for W3C Design Tokens (DTCG) JSON, as exported by most design tools. A project whose design
// tool exports something else replaces this file and keeps the TokenSet shape (standard §8.1).
import type { TokenSet } from './token-set.ts'

type Node = { $value?: unknown; $extensions?: Record<string, unknown> } & Record<string, unknown>

const leaves = (group: unknown): [string, Node][] =>
  group && typeof group === 'object'
    ? Object.entries(group as Record<string, unknown>).filter(
        (entry): entry is [string, Node] => !entry[0].startsWith('$') && typeof entry[1] === 'object' && entry[1] !== null && '$value' in entry[1],
      )
    : []

const str = (v: unknown, where: string): string => {
  if (typeof v !== 'string') throw new Error(`${where}: expected a string, got ${JSON.stringify(v)}`)
  return v
}

export function readDesign(json: Record<string, unknown>): TokenSet {
  return {
    colors: leaves(json.color).map(([name, t]) => ({
      name,
      light: str(t.$value, `color.${name}`),
      dark: t.$extensions?.dark === undefined ? undefined : str(t.$extensions.dark, `color.${name} dark`),
    })),
    fontFamilies: leaves(json['font-family']).map(([name, t]) => ({
      name,
      stack: Array.isArray(t.$value) ? t.$value.map((f, i) => str(f, `font-family.${name}[${String(i)}]`)) : [str(t.$value, `font-family.${name}`)],
    })),
    fontSizes: leaves(json['font-size']).map(([name, t]) => ({
      name,
      size: str(t.$value, `font-size.${name}`),
      lineHeight: str(t.$extensions?.lineHeight, `font-size.${name} lineHeight`),
    })),
    radii: leaves(json.radius).map(([name, t]) => ({ name, value: str(t.$value, `radius.${name}`) })),
    layout: leaves(json.layout).map(([name, t]) => ({ name, value: str(t.$value, `layout.${name}`) })),
  }
}
