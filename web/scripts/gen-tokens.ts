// `make tokens`: design variables → src/styles/tokens.css (standard §8.1). `--check` fails if the file is stale.
import { readFileSync, writeFileSync } from 'node:fs'
import { readDesign } from './tokens/read-design.ts'
import { writeCss } from './tokens/write-css.ts'

const source = 'design/tokens.json'
const target = 'src/styles/tokens.css'

const css = writeCss(readDesign(JSON.parse(readFileSync(source, 'utf8')) as Record<string, unknown>), source)

if (process.argv.includes('--check')) {
  let current = ''
  try { current = readFileSync(target, 'utf8') } catch { /* missing counts as stale */ }
  if (current !== css) {
    process.stderr.write(`${target} is out of date. Run \`make tokens\`.\n`)
    process.exit(1)
  }
} else {
  writeFileSync(target, css)
  process.stdout.write(`Wrote ${target}\n`)
}
