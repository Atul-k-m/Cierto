import { ArrowRight, Check, ChevronDown, FileText, MessageSquare, RotateCcw, Send, Webhook, Wrench } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { SessionSummary } from '../../shared/demo'
import { fmtDay, fmtTime, fmtWhen } from '../../widget/format'
import { CodeBlock } from '../parts/Code'

// One engine inside three apps. Pick an app and a problem, move the clock, ask like a shopper.
// Two columns only: the phone, and one panel. No nested scrolling; every answer is one short card.
type Host = 'smytten' | 'swish' | 'zomato'
const APPS: Record<Host, { brand: string; kind: string; src: string; slot: string; variant: string; mode: string; code: string; lang: string }> = {
  smytten: { brand: 'Smytten', kind: 'D2C parcels · days', src: '/hosts/smytten.html', slot: 'Inside each card on My Orders', variant: 'orders-row', mode: 'Drop-in Web Component',
    lang: 'html', code: '<cierto-order\n  order="SMY-4821360"\n  variant="orders-row"\n  theme="smytten">\n</cierto-order>' },
  zomato: { brand: 'Zomato', kind: 'Food delivery · minutes', src: '/hosts/zomato.html', slot: 'The live-tracking card under the map', variant: 'tracking-card', mode: 'Headless view model',
    lang: 'ts', code: "const view = await cierto.headless\n  .order('ZMT-7729381044').get()\n\n// render view.headline, view.eta and\n// view.actions in Zomato's own card" },
  swish: { brand: 'Swish', kind: '10-min food · minutes', src: '/hosts/swish.html', slot: 'The whole after-delivery screen', variant: 'after-delivered', mode: 'Drop-in Web Component',
    lang: 'html', code: '<cierto-order\n  order="SWH-40193877"\n  variant="after-delivered"\n  theme="swish">\n</cierto-order>' },
}
const QUESTIONS = ['Where is my order?', 'Why is it late?', 'Mera order kab aayega?', 'Delivered but not received', 'Talk to a person']
type Order = SessionSummary['orders'][number] & { cause?: string }
type Summary = SessionSummary & { causes?: { id: string; label: string; orders: string[] }[] }
interface AskReply {
  answer: string; intent?: string; cause?: string | null; stale?: boolean
  promise?: { now?: string | null; latest_by?: string | null; fallback?: { at?: string | null; text: string } | null } | null
  sources?: { name: string; age_seconds?: number }[]; actions?: { id: string; primary: boolean; label: string }[]
}
interface Turn { q: string; reply: AskReply | null; error?: string }

const age = (s?: number) => s == null ? '' : s < 90 ? 'just now' : s < 5400 ? `${Math.round(s / 60)} min ago` : s < 172800 ? `${Math.round(s / 3600)} h ago` : `${Math.round(s / 86400)} d ago`
const when = (iso: string, now: string) => /T23:59/.test(iso) ? fmtDay(iso) : fmtWhen(iso, now)
function splitAnswer(text: string) {
  const parts = text.match(/[^.!?]+[.!?]+(\s|$)/g)?.map((x) => x.trim()) ?? [text]
  return { head: parts[0], rest: parts.slice(1) }
}

function useDemo() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [busy, setBusy] = useState(false)
  const start = useCallback(async () => { setSummary(null); setSummary(await fetch('/v1/demo/sessions', { method: 'POST' }).then((r) => r.json())) }, [])
  useEffect(() => { start().catch(() => {}) }, [start])
  useEffect(() => {
    if (!summary) return
    // The host app in the iframe can change the session too; poll it, but only while this tab is visible.
    const t = window.setInterval(() => { if (!document.hidden) fetch(`/v1/demo/sessions/${summary.id}`).then((r) => r.json()).then(setSummary).catch(() => {}) }, 2000)
    return () => window.clearInterval(t)
  }, [summary?.id])
  const advance = async (beat: string) => {
    if (!summary) return
    setBusy(true)
    try { setSummary(await fetch(`/v1/demo/sessions/${summary.id}/advance`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ beat }) }).then((r) => r.json())) }
    finally { setBusy(false) }
  }
  return { summary, busy, advance, restart: start }
}

export function Demos() {
  const [host, setHost] = useState<Host>('smytten')
  useEffect(() => { // ?app= picks the host after hydration, so the prerendered page stays one static HTML file
    const app = new URLSearchParams(location.search).get('app')
    if (app === 'swish' || app === 'zomato') setHost(app)
  }, [])
  const { summary, busy, advance, restart } = useDemo()
  const orders = (summary?.orders ?? []).filter((o) => o.host === host) as Order[]
  const [key, setKey] = useState<string | null>(null)
  const order = orders.find((o) => o.key === key) ?? orders[0]
  const [tab, setTab] = useState<'ask' | 'case' | 'hooks' | 'wiring'>('ask')
  const a = APPS[host]
  const label = (o: Order) => summary?.causes?.find((c) => c.orders.includes(o.key))?.label ?? o.cause?.replace(/_/g, ' ') ?? o.title
  const choose = (h: Host) => { setHost(h); setKey(null); const u = new URL(location.href); u.searchParams.set('app', h); history.replaceState(null, '', u) }
  const next = summary?.beats.find((b) => !b.reached)
  const done = summary?.beats.filter((b) => b.reached).length ?? 0
  return (
    <main id="main" className="demos">
      <header className="demos-head frame">
        <div>
          <h1 className="display">Cierto, inside the app you run</h1>
          <p className="lead">Pick an app and a problem, move the clock, ask like a shopper.</p>
        </div>
        <div className="app-switch" role="tablist" aria-label="Host app">
          {(Object.keys(APPS) as Host[]).map((k) => (
            <button key={k} role="tab" aria-selected={host === k} onClick={() => choose(k)}><span className="app-name">{APPS[k].brand}</span><span className="app-kind">{APPS[k].kind}</span></button>
          ))}
        </div>
      </header>

      <div className="frame demo2">
        <figure className="d2-phone">
          <AnimatePresence mode="wait">
            <motion.div key={host} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: .45, ease: [.16, 1, .3, 1] }}>
              <Screen src={summary ? `${a.src}?session=${summary.id}` : null} title={`${a.brand} concept demo with Cierto inside`} />
            </motion.div>
          </AnimatePresence>
          <figcaption>Concept replica · not affiliated with {a.brand}</figcaption>
        </figure>

        <div className="d2-side">
          <div className="d2-block">
            <p className="d2-label">1 · Pick a problem</p>
            <div className="d2-causes" role="tablist" aria-label="Problem">
              {orders.map((o) => (
                <button key={o.key} role="tab" aria-selected={order?.key === o.key} onClick={() => setKey(o.key)}>{label(o)}</button>
              ))}
            </div>
          </div>

          <div className="d2-block">
            <div className="d2-clockrow">
              <p className="d2-label">2 · Move the clock</p>
              <span className="d2-now num">{summary ? `${fmtDay(summary.now)}, ${fmtTime(summary.now)}` : '…'}</span>
            </div>
            <div className="d2-track" aria-hidden="true">{summary?.beats.map((b) => <i key={b.id} className={b.reached ? 'on' : ''} />)}</div>
            <div className="d2-clockrow">
              {next ? <button className="btn sm" disabled={busy} onClick={() => advance(next.id)}>{next.label} · {next.at.slice(0, 10) !== summary!.beats[0].at.slice(0, 10) ? fmtDay(next.at) : fmtTime(next.at)} <ArrowRight size={15} aria-hidden="true" /></button>
                : <span className="d2-muted">End of the story.</span>}
              <span className="d2-muted num">{done}/{summary?.beats.length ?? 0}</span>
              <button className="text-btn" onClick={() => { setKey(null); restart() }}><RotateCcw size={13} aria-hidden="true" />Restart</button>
            </div>
          </div>

          <section className="d2-panel" aria-label="Cierto">
            <div className="panel-tabs" role="tablist">
              {([['ask', MessageSquare, 'Ask'], ['case', FileText, 'Case'], ['hooks', Webhook, 'Webhooks'], ['wiring', Wrench, 'Wiring']] as const).map(([id, I, l]) => (
                <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}><I size={15} aria-hidden="true" />{l}</button>
              ))}
            </div>
            <div className="d2-body">
              {tab === 'ask' && summary && order && <Ask key={order.key} session={summary.id} order={order} now={summary.now} />}
              {tab === 'case' && summary && order && <Case session={summary.id} order={order} now={summary.now} />}
              {tab === 'hooks' && summary && <Hooks session={summary.id} order={order?.key} />}
              {tab === 'wiring' && (
                <div className="wiring">
                  <dl><div><dt>Where</dt><dd>{a.slot}</dd></div><div><dt>How</dt><dd>{a.mode} · <code>{a.variant}</code></dd></div></dl>
                  <CodeBlock tabs={[{ label: a.mode, file: host === 'zomato' ? 'tracking-card.ts' : 'order-card.html', lang: a.lang, code: a.code }]} />
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </main>
  )
}

function Ask({ session, order, now }: { session: string; order: Order; now: string }) {
  const [turns, setTurns] = useState<Turn[]>([])
  const [text, setText] = useState('')
  const [wait, setWait] = useState(false)
  const ask = async (question: string) => {
    if (!question.trim() || wait) return
    setText(''); setWait(true); setPending(question)
    const locale = /\b(kab|kaha|kahan|kya|nahi|mera|aayega|kyun)\b/i.test(question) ? 'hi-Latn-IN' : 'en-IN'
    try {
      const r = await fetch(`/v1/demo/sessions/${session}/orders/${order.key}/ask`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ question, locale }) })
      const reply: AskReply | null = r.ok ? await r.json() : null
      setTurns((t) => [{ q: question, reply, error: reply ? undefined : 'No answer from the engine.' }, ...t].slice(0, 4))
    } catch { setTurns((t) => [{ q: question, reply: null, error: 'The demo engine is not reachable.' }, ...t]) }
    finally { setWait(false); setPending(null) }
  }
  const [pending, setPending] = useState<string | null>(null)
  const [latest, ...older] = turns
  return (
    <div className="ask2">
      <form className="ask-input" onSubmit={(e) => { e.preventDefault(); ask(text) }}>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder={`Ask about ${order.order_ref}… (English or Hinglish)`} aria-label="Ask about this order" />
        <button type="submit" aria-label="Send" disabled={wait || !text.trim()}><Send size={16} /></button>
      </form>
      <div className="ask-chips">{QUESTIONS.map((x) => <button key={x} onClick={() => ask(x === 'Delivered but not received' ? 'It says delivered but I didn’t get it' : x)} disabled={wait}>{x}</button>)}</div>
      {latest || pending ? (
        <motion.div layout transition={{ layout: { duration: .45, ease: [.16, 1, .3, 1] } }} className={`ans-slot ${pending ? 'is-wait' : ''}`}>
          {pending && <div className="ans-progress" aria-hidden="true"><i /></div>}
          {latest ? <Answer key={turns.length} turn={latest} now={now} pendingQ={pending} />
            : <article className="ans"><p className="ans-q">“{pending}”</p><span className="who think"><i />CIERTO</span><p className="d2-muted">Reading the order's timeline…</p></article>}
        </motion.div>
      ) : <p className="d2-muted">Answers come only from this order's data: courier scans, rider GPS, payments and the promise made at checkout.</p>}
      {older.length > 0 && (
        <details className="ask-hist">
          <summary><ChevronDown size={14} aria-hidden="true" />Earlier questions ({older.length})</summary>
          <ul>{older.map((t, i) => <li key={i}><b>{t.q}</b><span>{t.reply ? splitAnswer(t.reply.answer).head : t.error}</span></li>)}</ul>
        </details>
      )}
    </div>
  )
}

function Answer({ turn, now, pendingQ }: { turn: Turn; now: string; pendingQ?: string | null }) {
  const [more, setMore] = useState(false)
  const r = turn.reply
  if (!r) return <motion.div className="ans" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}><p className="d2-muted">{turn.error}</p></motion.div>
  const { head, rest } = splitAnswer(r.answer)
  const p = r.promise
  const same = p?.now && p?.latest_by && p.now === p.latest_by
  return (
    <motion.article className="ans" initial={{ opacity: 0 }} animate={{ opacity: pendingQ ? 0.45 : 1 }} transition={{ duration: .3 }}>
      <p className="ans-q">“{pendingQ ?? turn.q}”</p>
      <span className={`who ${pendingQ ? 'think' : ''}`}><i />CIERTO{r.stale && !pendingQ && <em>· data is stale</em>}{(r as AskReply & { rephrased?: boolean }).rephrased && !pendingQ && <em className="ai">· worded by AI, facts checked</em>}</span>
      <p className="ans-head">{head}</p>
      {rest.length > 0 && (more ? <p className="ans-rest">{rest.join(' ')}</p> : <button className="text-btn" onClick={() => setMore(true)}>Why · {rest.length} more {rest.length === 1 ? 'line' : 'lines'}</button>)}
      {p && (p.now || p.latest_by || p.fallback) && (
        <dl className="ans-promise">
          {p.now && <div><dt>{same ? 'Due' : 'Now expected'}</dt><dd className="num">{when(p.now, now)}</dd></div>}
          {p.latest_by && !same && <div><dt>Latest by</dt><dd className="num">{when(p.latest_by, now)}</dd></div>}
          {p.fallback && <div className="fb"><dt>If missed</dt><dd>{p.fallback.text}</dd></div>}
        </dl>
      )}
      <div className="ans-foot">
        {r.actions?.slice(0, 2).map((x) => <span key={x.id} className={`act ${x.primary ? 'p' : ''}`}>{x.label}</span>)}
        {r.sources?.slice(0, 2).map((s) => <span key={s.name} className="src">{s.name}{s.age_seconds != null && ` · ${age(s.age_seconds)}`}</span>)}
      </div>
    </motion.article>
  )
}

interface CaseData {
  case_id?: string | null
  cause?: { id: string; text: string } | null
  timeline?: { at: string; who?: string; asserted_by?: string; text: string }[]
  resolution?: { decision: string; needs_approval: boolean; steps: { at: string; actor: string; text: string }[]; case_id?: string | null; approval_reason?: string | null } | null
}

function Case({ session, order, now }: { session: string; order: Order; now: string }) {
  const [d, setD] = useState<CaseData | null>(null)
  const load = useCallback(() => {
    fetch(`/v1/demo/sessions/${session}/orders/${order.key}/case`).then((r) => (r.ok ? r.json() : null)).then((x) => x && setD(x)).catch(() => {})
  }, [session, order.key])
  useEffect(() => { load(); const t = window.setInterval(load, 2000); return () => window.clearInterval(t) }, [load])
  const approve = async () => { await fetch(`/v1/demo/sessions/${session}/orders/${order.key}/approve`, { method: 'POST' }); load() }
  if (!d) return <p className="d2-muted">Loading the case…</p>
  const r = d.resolution
  return (
    <div className="case3">
      {d.cause && <p className="case3-cause"><b>Cause</b>{d.cause.text}</p>}
      {r ? (
        <div className="case3-res">
          <div className="case3-top"><b>{r.case_id ?? d.case_id ?? 'Case'}</b><span className={`chip ${r.needs_approval ? 'human' : 'auto'}`}>{r.needs_approval ? 'Needs approval' : 'Inside policy'}</span></div>
          <ol>{r.steps.slice(0, 5).map((s, i) => <li key={i}><Check size={14} aria-hidden="true" /><span>{s.text}</span></li>)}</ol>
          {r.needs_approval && <button className="btn sm" onClick={approve}>Approve remedy</button>}
        </div>
      ) : <p className="d2-muted">No case yet. Move the clock, or tap “No” in the phone.</p>}
      <ol className="case3-tl">{(d.timeline ?? []).slice(-5).reverse().map((t, i) => <li key={i}><time className="num">{fmtWhen(t.at, now)}</time><span>{t.text}</span></li>)}</ol>
    </div>
  )
}

function Hooks({ session, order }: { session: string; order?: string }) {
  const [rows, setRows] = useState<{ type?: string; event?: string; at?: string; data?: unknown }[] | null>(null)
  const [open, setOpen] = useState(0)
  useEffect(() => {
    const load = () => fetch(`/v1/demo/sessions/${session}/webhooks${order ? `?order=${order}` : ''}`).then((r) => (r.ok ? r.json() : [])).then((x) => setRows(Array.isArray(x) ? x : x.webhooks ?? x.events ?? [])).catch(() => setRows([]))
    load(); const t = window.setInterval(load, 2000); return () => window.clearInterval(t)
  }, [session, order])
  if (!rows) return <p className="d2-muted">Loading…</p>
  if (!rows.length) return <p className="d2-muted">No webhooks yet. They fire when a case opens, a remedy is proposed or approved, or proof changes.</p>
  const list = rows.slice(0, 6)
  return (
    <div className="hooks2">
      <ul>{list.map((h, i) => <li key={i}><button aria-pressed={open === i} onClick={() => setOpen(i)}><code>{h.type ?? h.event}</code>{h.at && <time>{fmtTime(h.at)}</time>}</button></li>)}</ul>
      {list[open] && <CodeBlock tabs={[{ label: 'payload', file: `POST /your/webhook`, lang: 'json', code: JSON.stringify(list[open].data ?? list[open], null, 2).slice(0, 1400) }]} />}
    </div>
  )
}

function Screen({ src, title }: { src: string | null; title: string }) {
  const box = useRef<HTMLDivElement>(null)
  const [scale, setScale] = useState(0.86)
  useLayoutEffect(() => {
    const el = box.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => setScale(e.contentRect.width / 390))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return (
    <div className="device">
      <div className="screen" ref={box} style={{ height: 844 * scale }}>
        {src && <iframe key={src} title={title} src={src} style={{ transform: `scale(${scale})` }} />}
      </div>
    </div>
  )
}
