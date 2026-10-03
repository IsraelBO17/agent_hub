// `make check`: no hand-written design values in app code (standard §8, §23). Vendored shadcn files,
// generated files and mock data are skipped. Also: no font-size class the design doesn't define, in any
// component (vendored ones included), because Tailwind silently drops it.
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

export const rules: { name: string; pattern: RegExp }[] = [
  { name: 'hex colour', pattern: /#[0-9a-fA-F]{3,8}\b(?![\w-])/ },
  { name: 'colour function', pattern: /\b(?:rgba?|hsla?|oklch|oklab|lab|lch)\(/ },
  { name: 'arbitrary font size', pattern: /\btext-\[[^\]]*\]/ },
  { name: 'arbitrary pixel value', pattern: /-\[[^\]]*\d+px[^\]]*\]/ },
]

const skip = [
  /^src\/components\/ui\/(alert-dialog|button|card|dialog|field|input|label|separator|sheet|sidebar|skeleton|textarea|tooltip|dropdown-menu|drawer)\.tsx$/,
  /^src\/service\/generated\//,
  /^src\/styles\/tokens\.css$/,
  /^src\/lib\/token-names\.ts$/,
  /^src\/mocks\//,
  /\.test\.tsx?$/,
]
const vendored = skip[0]

export function findViolations(path: string, text: string) {
  return text.split('\n').flatMap((line, i) =>
    rules.filter((r) => r.pattern.test(line)).map((r) => `${path}:${String(i + 1)}: ${r.name}: ${line.trim()}`))
}

/** Font-size classes (`text-sm`, `md:text-2xl`, `text-13`) whose size isn't in the design's type scale. */
export function findUnknownSizes(path: string, text: string, sizes: Set<string>) {
  return text.split('\n').flatMap((line, i) =>
    [...line.matchAll(/(?<![\w-])text-(xs|sm|base|lg|\d*xl|\d+)(?![\w-])/g)]
      .filter((m) => !sizes.has(m[1] ?? ''))
      .map((m) => `${path}:${String(i + 1)}: font size not in the type scale: ${m[0]}`))
}

/** The type scale's names, read from the generated tokens.css. */
export const typeScale = (css: string) => new Set([...css.matchAll(/^ {2}--text-([\w-]+): /gm)].map((m) => m[1] ?? '').filter((n) => !n.includes('--')))

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name)
    return statSync(full).isDirectory() ? files(full) : /\.(tsx?|css)$/.test(name) ? [full] : []
  })
}

if (import.meta.main) {
  const sizes = typeScale(readFileSync('src/styles/tokens.css', 'utf8'))
  const problems = files('src').flatMap((f) => {
    if (skip.some((s) => s.test(f)) && !vendored?.test(f)) return []
    const text = readFileSync(f, 'utf8')
    return [...(vendored?.test(f) ? [] : findViolations(f, text)), ...(f.endsWith('.css') ? [] : findUnknownSizes(f, text, sizes))]
  })
  if (problems.length > 0) {
    process.stderr.write(`Hand-written design values (use a token instead, standard §8):\n${problems.join('\n')}\n`)
    process.exit(1)
  }
  process.stdout.write('check-tokens: no hand-written design values\n')
}
