// `make check`: no high or critical advisories in production dependencies, except those accepted in
// docs/security-exceptions.md with an expiry that hasn't passed (standard §19).
import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'

export interface Exception { id: string; expires: string }

/** Rows of the exceptions table: | advisory | reason | owner | expires (YYYY-MM-DD) | */
export function parseExceptions(markdown: string): Exception[] {
  return markdown.split('\n')
    .map((line) => line.split('|').map((cell) => cell.trim()))
    .filter((cells) => (cells[1] ?? '').startsWith('GHSA-'))
    .map((cells) => ({ id: cells[1] ?? '', expires: cells[4] ?? '' }))
}

interface Advisory { name: string; severity: string; via: (string | { url?: string; severity?: string })[] }

export function blocking(vulns: Record<string, Advisory>, exceptions: Exception[], today: string): string[] {
  const accepted = new Set(exceptions.filter((e) => e.expires >= today).map((e) => e.id))
  return Object.values(vulns).flatMap((v) => v.via
    .filter((via): via is { url?: string; severity?: string } => typeof via !== 'string')
    .filter((via) => via.severity === 'high' || via.severity === 'critical')
    .map((via) => via.url?.split('/').pop() ?? v.name)
    .filter((id) => !accepted.has(id))
    .map((id) => `${v.name}: ${id}`))
}

if (import.meta.main) {
  let out: string
  try {
    out = execFileSync('npm', ['audit', '--omit=dev', '--json'], { encoding: 'utf8' })
  } catch (e) {
    out = (e as { stdout?: string }).stdout ?? '{}' // npm audit exits non-zero when it finds anything
  }
  const { vulnerabilities = {} } = JSON.parse(out) as { vulnerabilities?: Record<string, Advisory> }
  const exceptions = parseExceptions(readFileSync('docs/security-exceptions.md', 'utf8'))
  const today = new Date().toISOString().slice(0, 10)
  const expired = exceptions.filter((e) => e.expires < today)
  const found = [...new Set(blocking(vulnerabilities, exceptions, today))]
  if (expired.length > 0) process.stderr.write(`Expired exceptions (renew or remove): ${expired.map((e) => e.id).join(', ')}\n`)
  if (found.length > 0 || expired.length > 0) {
    if (found.length > 0) process.stderr.write(`High or critical advisories in production dependencies:\n${found.join('\n')}\n`)
    process.exit(1)
  }
  process.stdout.write('check-audit: no unaccepted high or critical advisories\n')
}
