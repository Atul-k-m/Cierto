// Demo plumbing shared by the hosts and the site. In a real integration each host
// reads its own order data from its own backend; here the demo API stands in for all of them.
import { useEffect, useState } from 'react'
import type { OrderEnvelope, OrderView } from '../widget/types'

export interface SessionSummary {
  id: string
  now: string
  beats: { id: string; label: string; at: string; primary?: boolean; reached: boolean }[]
  orders: { key: string; host: string; variant: string; tenant: string; order_ref: string; brand: string;
    sources: string[]; title: string; state: string | null; proof: string | null; tone: string | null }[]
  feed: { at: string; order: string; host: string; rule: string; kind: string; holder: string; message: string }[]
}

export const sessionParam = () => new URLSearchParams(location.search).get('session')

/** The site passes ?session=…; opened on its own, a host starts its own session. */
export function useSession(): string | null {
  const [id, setId] = useState<string | null>(sessionParam())
  useEffect(() => {
    if (id) return
    fetch('/v1/demo/sessions', { method: 'POST' }).then((r) => r.json()).then((s: SessionSummary) => {
      const url = new URL(location.href)
      url.searchParams.set('session', s.id)
      history.replaceState(null, '', url)
      setId(s.id)
    })
  }, [id])
  return id
}

/** The host's own view of one order (stands in for the host's backend). */
export function useOrder(session: string | null, key: string): OrderView | null {
  const [view, setView] = useState<OrderView | null>(null)
  useEffect(() => {
    if (!session) return
    let alive = true
    const load = () => fetch(`/v1/demo/sessions/${session}/orders/${key}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((env: OrderEnvelope | null) => { if (alive && env) setView(env.view) })
      .catch(() => {})
    load()
    const t = window.setInterval(() => { if (!document.hidden) load() }, 2000)
    return () => { alive = false; window.clearInterval(t) }
  }, [session, key])
  return view
}

export const minutesUntil = (iso: string, nowIso: string) =>
  Math.max(0, Math.round((new Date(iso).getTime() - new Date(nowIso).getTime()) / 60_000))
