// `make check`: no hand-written design values in app code (standard §8, §23). Vendored shadcn files,
// generated files and mock data are skipped.
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

export const rules: { name: string; pattern: RegExp }[] = [
  { name: 'hex colour', pattern: /#[0-9a-fA-F]{3,8}\b(?![\w-])/ },
  { name: 'colour function', pattern: /\b(?:rgba?|hsla?|oklch|oklab|lab|lch)\(/ },
  { name: 'arbitrary font size', pattern: /\btext-\[[^\]]*\]/ },
  { name: 'arbitrary pixel value', pattern: /-\[[^\]]*\d+px[^\]]*\]/ },
]

const skip = [
  /^src\/components\/ui\/(alert-dialog|button|card|dialog|field|input|label|separator|sheet|sidebar|skeleton|textarea|tooltip)\.tsx$/,
  /^src\/service\/generated\//,
  /^src\/styles\/tokens\.css$/,
  /^src\/mocks\//,
  /\.test\.tsx?$/,
]

export function findViolations(path: string, text: string) {
  return text.split('\n').flatMap((line, i) =>
    rules.filter((r) => r.pattern.test(line)).map((r) => `${path}:${String(i + 1)}: ${r.name}: ${line.trim()}`))
}

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name)
    return statSync(full).isDirectory() ? files(full) : /\.(tsx?|css)$/.test(name) ? [full] : []
  })
}

if (import.meta.main) {
  const problems = files('src').filter((f) => !skip.some((s) => s.test(f))).flatMap((f) => findViolations(f, readFileSync(f, 'utf8')))
  if (problems.length > 0) {
    process.stderr.write(`Hand-written design values (use a token instead, standard §8):\n${problems.join('\n')}\n`)
    process.exit(1)
  }
  process.stdout.write('check-tokens: no hand-written design values\n')
}
