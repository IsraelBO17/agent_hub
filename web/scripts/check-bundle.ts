// `make check`: the JavaScript the first screen needs stays within the budget (standard §18). Reads
// Vite's manifest: the entry chunk and everything it imports statically (lazy routes don't count).
import { readFileSync } from 'node:fs'
import { gzipSync } from 'node:zlib'

export interface ManifestChunk { file: string; isEntry?: boolean; imports?: string[] }
export type Manifest = Record<string, ManifestChunk>

export function initialFiles(manifest: Manifest): string[] {
  const seen = new Set<string>()
  const visit = (key: string) => {
    if (seen.has(key)) return
    seen.add(key)
    manifest[key]?.imports?.forEach(visit)
  }
  Object.entries(manifest).filter(([, c]) => c.isEntry).forEach(([key]) => { visit(key) })
  return [...seen].map((key) => manifest[key]?.file).filter((f): f is string => f?.endsWith('.js') ?? false)
}

if (import.meta.main) {
  const manifest = JSON.parse(readFileSync('dist/.vite/manifest.json', 'utf8')) as Manifest
  const { budget } = JSON.parse(readFileSync('package.json', 'utf8')) as { budget: { initialJsKb: number } }
  const kb = initialFiles(manifest).reduce((sum, file) => sum + gzipSync(readFileSync(`dist/${file}`)).length, 0) / 1024
  const line = `check-bundle: initial JS ${kb.toFixed(1)} KB gzip (budget ${String(budget.initialJsKb)} KB)`
  if (kb > budget.initialJsKb) {
    process.stderr.write(`${line}: over budget. Lazy-load more, or raise the budget with a reason in the decision log.\n`)
    process.exit(1)
  }
  process.stdout.write(`${line}\n`)
}
