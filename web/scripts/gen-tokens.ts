// `make tokens`: design variables → src/styles/tokens.css and src/lib/token-names.ts (standard §8.1).
// `--check` fails if either file is stale.
import { readFileSync, writeFileSync } from 'node:fs'
import { readSources, sources } from './tokens/read-design.ts'
import { writeCss, writeNames } from './tokens/write-css.ts'

const set = readSources((path) => readFileSync(path, 'utf8'))
const outputs: [string, string][] = [
  ['src/styles/tokens.css', writeCss(set, sources)],
  ['src/lib/token-names.ts', writeNames(set, sources)],
]

if (process.argv.includes('--check')) {
  const stale = outputs.filter(([target, text]) => {
    try { return readFileSync(target, 'utf8') !== text } catch { return true }
  })
  if (stale.length > 0) {
    process.stderr.write(`${stale.map(([t]) => t).join(' and ')} out of date. Run \`make tokens\`.\n`)
    process.exit(1)
  }
} else {
  for (const [target, text] of outputs) {
    writeFileSync(target, text)
    process.stdout.write(`Wrote ${target}\n`)
  }
}
