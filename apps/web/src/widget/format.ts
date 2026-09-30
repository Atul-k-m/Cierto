// Dates and durations in Indian English, always in IST (the orders' own timezone).
const tz = 'Asia/Kolkata'
const day = new Intl.DateTimeFormat('en-IN', { timeZone: tz, weekday: 'short', day: 'numeric', month: 'short' })
const time = new Intl.DateTimeFormat('en-IN', { timeZone: tz, hour: 'numeric', minute: '2-digit', hour12: true })
const dateOnly = new Intl.DateTimeFormat('en-IN', { timeZone: tz, day: 'numeric', month: 'short' })

const lower = (s: string) => s.replace(/\s?(AM|PM|am|pm)$/, (m) => m.toLowerCase().replace(' ', ' '))

export const fmtTime = (iso: string) => lower(time.format(new Date(iso)))
export const fmtDay = (iso: string) => day.format(new Date(iso)).replace(',', '')
export const fmtDate = (iso: string) => dateOnly.format(new Date(iso))
export const fmtDayTime = (iso: string) => `${fmtDay(iso)}, ${fmtTime(iso)}`

/** "Today, 2:02 pm" / "Yesterday, 2:02 pm" / "Wed 24 Dec, 2:02 pm", relative to the engine's clock. */
export function fmtWhen(iso: string, nowIso: string): string {
  const d = new Date(iso)
  const now = new Date(nowIso)
  const key = (x: Date) => dateOnly.format(x)
  if (key(d) === key(now)) return `Today, ${fmtTime(iso)}`
  if (key(d) === key(new Date(now.getTime() - 86_400_000))) return `Yesterday, ${fmtTime(iso)}`
  return fmtDayTime(iso)
}

export function fmtLeft(dueIso: string, nowIso: string): string {
  const ms = new Date(dueIso).getTime() - new Date(nowIso).getTime()
  if (ms <= 0) return 'time is up'
  const min = Math.round(ms / 60_000)
  if (min < 60) return `${min} min`
  const h = Math.floor(min / 60)
  if (h < 48) return `${h} h ${min % 60 ? `${min % 60} min` : ''}`.trim()
  return `${Math.floor(h / 24)} days`
}

export const rupees = (n: number | null | undefined) => (n == null ? '' : `₹${n.toLocaleString('en-IN')}`)
