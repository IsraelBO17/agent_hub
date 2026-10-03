// Dates are displayed through these helpers only (standard §20). Locale and time zone come from the
// profile; undefined means the browser's.
const locale: string | undefined = undefined
const timeZone: string | undefined = undefined

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short', ...(timeZone ? { timeZone } : {}) }).format(date)
}

export function formatRelative(date: Date, now: Date = new Date()): string {
  const seconds = Math.round((date.getTime() - now.getTime()) / 1000)
  const units: [Intl.RelativeTimeFormatUnit, number][] = [['day', 86_400], ['hour', 3_600], ['minute', 60]]
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit)
  }
  return rtf.format(0, 'minute')
}

/** A day without the time, e.g. "Sep 24" (the year only when it isn't this one). */
export function formatDay(date: Date, now: Date = new Date()): string {
  const sameYear = date.getFullYear() === now.getFullYear()
  return new Intl.DateTimeFormat(locale, { month: 'short', day: 'numeric', ...(sameYear ? {} : { year: 'numeric' }), ...(timeZone ? { timeZone } : {}) }).format(date)
}
