import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { Roll } from './Motion'

// Six real WISMO causes, each answered the way Cierto answers: grounded in named sources, with a promise and a fallback.
type Kind = 'stuck' | 'traffic' | 'batched' | 'address' | 'silent' | 'unproven'
interface Scene {
  kind: Kind; tab: string; brand: string; order: string; at: string
  q: string; a: string; eta: [string, string, string]; etaLabels?: [string, string, string]; src: string
}

export const SCENES: Scene[] = [
  { kind: 'stuck', tab: 'Rider stuck', brand: 'Swish', order: 'SWH-40193877', at: '2:06 PM',
    q: "where is my order?? it's been 15 min",
    a: "**Anubhav has been stopped for 4 minutes** at the Agara junction; the rider app shows heavy traffic on Outer Ring Road. You're his **next and only drop**. New estimate 2:14 pm. If he isn't moving by 2:10 we'll tell you, and your late credit applies automatically.",
    eta: ['2:03', '2:14', '2:20'], src: 'Rider GPS 40 s ago · Swish dispatch · Maps traffic' },
  { kind: 'traffic', tab: 'Traffic', brand: 'Zomato', order: 'ZMT-7729381044', at: '1:31 PM',
    q: 'order kab aayega? bahut late ho gaya',
    a: "Traffic on Hosur Road added **9 minutes**. Rahul is moving again and is **2.1 km away**. New estimate 1:42 pm, and it won't be later than 1:50. We'll only message you again if that changes.",
    eta: ['1:33', '1:42', '1:50'], src: 'Rider GPS 12 s ago · Zomato ETA service · Maps traffic' },
  { kind: 'batched', tab: 'Batched order', brand: 'Zomato', order: 'ZMT-7729381090', at: '1:24 PM',
    q: 'why is the rider going the other way?',
    a: "Rahul is dropping **one other order first, 600 m from you**, on the way. **You're next.** That adds about 4 minutes: new estimate 1:38 pm. Your order has been in his insulated bag since 1:19.",
    eta: ['1:34', '1:38', '1:45'], src: 'Dispatch stop sequence · Rider GPS 20 s ago' },
  { kind: 'address', tab: 'Bad address', brand: 'Smytten', order: 'SMY-4815521', at: '11:02 AM',
    q: 'delivery guy called me, he cant find my house',
    a: "Your map pin is **1.2 km from the address you typed** (Wakad pin, Hinjewadi Phase 1 address). Delhivery's rider is near the pin. **Tap the correct spot** or add a landmark before 12:30 pm, and delivery stays on today.",
    eta: ['Today', 'Today', '12:30 fix'], etaLabels: ['Promised', 'Still possible', 'Confirm by'], src: 'Address text vs pin check · Delhivery rider location' },
  { kind: 'silent', tab: 'Courier silent', brand: 'Smytten', order: 'SMY-4817702', at: 'MON 10:40 AM',
    q: 'tracking not updated for 3 days???',
    a: "Delhivery **hasn't scanned your parcel since Fri 10:40 am** at the Bhiwandi hub. That's unusual on this lane, where scans usually come every 14 hours. We've asked Delhivery to trace it. **If there's no scan by Tue 6 pm, your refund or replacement starts automatically.**",
    eta: ['Mon 22', 'Wed 24', 'Tue 6 pm'], etaLabels: ['Promised', 'Now expected', 'Auto-remedy'], src: 'Delhivery scans · lane history · trace request D-7734' },
  { kind: 'unproven', tab: 'Delivered, not received', brand: 'Smytten', order: 'SMY-4821360', at: '2:05 PM',
    q: 'it says delivered but i didnt get anything',
    a: "Delhivery marked it delivered at 2:02 pm, but **no OTP was entered and no photo was taken**, so it isn't proven. We've asked Delhivery to recheck with the rider. **If they can't prove it by Fri 2:05 pm, your ₹599 refund starts automatically.**",
    eta: ['24 Dec', 'Unproven', 'Fri 2:05'], etaLabels: ['Promised', 'Delivery', 'Refund by'], src: 'Delhivery POD (no OTP, no photo) · shopper report' },
]

function rich(text: string, upto: number) {
  const words = text.split(' ')
  const out: React.ReactNode[] = []
  let bold = false
  // Every word is laid out from the start; words not yet "typed" are only hidden, so nothing reflows as they appear.
  words.forEach((w, i) => {
    let s = w
    const open = s.startsWith('**'); if (open) { bold = true; s = s.slice(2) }
    const close = s.includes('**'); if (close) s = s.replace('**', '')
    const off = i >= upto ? 'tw-off' : undefined
    out.push(bold ? <b key={i} className={off}>{s + ' '}</b> : <span key={i} className={off}>{s + ' '}</span>)
    if (close) bold = false
  })
  return out
}

function Route({ kind, run }: { kind: Kind; run: boolean }) {
  const t = { duration: 1.4, ease: [0.16, 1, 0.3, 1] as const }
  const path = 'M24 80 C 120 80, 150 26, 250 38 S 400 70, 470 24'
  const done = kind === 'stuck' ? 0.5 : kind === 'traffic' ? 0.68 : 0.55
  if (kind === 'address') return (
    <svg viewBox="0 0 494 104" aria-hidden="true">
      <path d="M40 70 L 190 70" stroke="#c9cbe0" strokeWidth="3" strokeDasharray="2 7" strokeLinecap="round" fill="none" />
      <motion.path d="M190 58 C 260 20, 360 20, 430 52" stroke="#3a2bff" strokeWidth="2" strokeDasharray="5 6" fill="none" initial={{ pathLength: 0 }} animate={{ pathLength: run ? 1 : 0 }} transition={t} />
      <circle cx="190" cy="70" r="7" fill="#0b0f17" /><text x="152" y="96" fontFamily="JetBrains Mono Variable, monospace" fontSize="9.5" fill="#555c6a">MAP PIN · WAKAD</text>
      <rect x="422" y="44" width="16" height="16" fill="#3a2bff" /><text x="360" y="96" fontFamily="JetBrains Mono Variable, monospace" fontSize="9.5" fill="#555c6a">TYPED · HINJEWADI</text>
      <text x="282" y="18" fontFamily="JetBrains Mono Variable, monospace" fontSize="10" fill="#3a2bff">1.2 KM APART</text>
    </svg>
  )
  if (kind === 'silent') return (
    <svg viewBox="0 0 494 104" aria-hidden="true">
      <line x1="24" y1="52" x2="470" y2="52" stroke="#e1e2ea" strokeWidth="2" />
      {[24, 90, 150, 206].map((x, i) => <circle key={i} cx={x} cy="52" r="6" fill="#0b0f17" />)}
      <motion.line x1="206" y1="52" x2="470" y2="52" stroke="#3a2bff" strokeWidth="2" strokeDasharray="3 6" initial={{ pathLength: 0 }} animate={{ pathLength: run ? 1 : 0 }} transition={t} />
      <text x="170" y="84" fontFamily="JetBrains Mono Variable, monospace" fontSize="9.5" fill="#555c6a">LAST SCAN · BHIWANDI · FRI</text>
      <text x="330" y="36" fontFamily="JetBrains Mono Variable, monospace" fontSize="10" fill="#3a2bff">NO SCAN · 72 H</text>
    </svg>
  )
  if (kind === 'unproven') return (
    <svg viewBox="0 0 494 104" aria-hidden="true">
      {['DOOR OTP', 'PHOTO', 'CALL', 'SHOPPER'].map((l, i) => (
        <g key={l} transform={`translate(${24 + i * 118} 26)`}>
          <motion.rect width="104" height="52" fill={i === 3 ? '#ecebff' : '#fff'} stroke={i === 3 ? '#3a2bff' : '#d8d9e2'} initial={{ opacity: 0, y: 8 }} animate={{ opacity: run ? 1 : 0, y: run ? 0 : 8 }} transition={{ ...t, delay: i * 0.12 }} />
          <text x="10" y="20" fontFamily="JetBrains Mono Variable, monospace" fontSize="9.5" fill="#555c6a">{l}</text>
          <text x="10" y="40" fontFamily="Inter Tight Variable, sans-serif" fontSize="14" fontWeight="600" fill={i === 3 ? '#3a2bff' : '#b3243f'}>{i === 3 ? 'Asked' : 'None'}</text>
        </g>
      ))}
    </svg>
  )
  return (
    <svg viewBox="0 0 494 104" aria-hidden="true">
      <path d={path} fill="none" stroke="#c9cbe0" strokeWidth="3" strokeDasharray="2 7" strokeLinecap="round" />
      <motion.path d={path} fill="none" stroke="#3a2bff" strokeWidth="3" strokeLinecap="round" initial={{ pathLength: 0 }} animate={{ pathLength: run ? done : 0 }} transition={t} />
      <circle cx="24" cy="80" r="6" fill="#0b0f17" />
      <rect x="458" y="12" width="24" height="24" fill="#0b0f17" />
      {kind === 'batched' && <><rect x="344" y="50" width="16" height="16" fill="none" stroke="#3a2bff" strokeWidth="2" /><text x="300" y="86" fontFamily="JetBrains Mono Variable, monospace" fontSize="9.5" fill="#3a2bff">OTHER DROP · 600 M</text></>}
      {kind === 'stuck' && <motion.circle cx="250" cy="38" r="14" fill="#3a2bff" initial={{ opacity: 0 }} animate={{ opacity: run ? [0.1, 0.3, 0.1] : 0 }} transition={{ duration: 1.6, repeat: Infinity }} />}
      <text x="30" y="98" fontFamily="JetBrains Mono Variable, monospace" fontSize="9.5" fill="#555c6a">{kind === 'stuck' ? 'KITCHEN · HSR' : 'RESTAURANT'}</text>
      <text x="398" y="98" fontFamily="JetBrains Mono Variable, monospace" fontSize="9.5" fill="#555c6a">YOU</text>
      {kind === 'stuck' && <text x="266" y="30" fontFamily="JetBrains Mono Variable, monospace" fontSize="10" fill="#3a2bff">STOPPED 4:12</text>}
      {kind === 'traffic' && <text x="300" y="30" fontFamily="JetBrains Mono Variable, monospace" fontSize="10" fill="#3a2bff">+9 MIN · HOSUR RD</text>}
    </svg>
  )
}

const HOLD = 6500

export function Answer() {
  const reduce = useReducedMotion()
  const [idx, setIdx] = useState(0)
  const [typed, setTyped] = useState(0)
  const [words, setWords] = useState(0)
  const [auto, setAuto] = useState(true)
  const [tick, setTick] = useState(0)
  const s = SCENES[idx]
  const total = s.a.split(' ').length
  const typing = typed < s.q.length
  const answered = words >= total
  const timer = useRef(0)

  useEffect(() => {
    if (reduce) { setTyped(s.q.length); setWords(total); return }
    setTyped(0); setWords(0)
    let q = 0, w = 0
    const iv = window.setInterval(() => {
      if (q < s.q.length) { q += 1; setTyped(q); return }
      if (q === s.q.length && w === 0) { q += 1; return } // a beat of thinking
      if (w < total) { w += 1; setWords(w) }
    }, 28)
    return () => window.clearInterval(iv)
  }, [idx])

  useEffect(() => {
    if (!auto || !answered) return
    const start = performance.now()
    const iv = window.setInterval(() => setTick(Math.min(1, (performance.now() - start) / HOLD)), 50)
    timer.current = window.setTimeout(() => { setIdx((i) => (i + 1) % SCENES.length); setTick(0) }, HOLD)
    return () => { window.clearTimeout(timer.current); window.clearInterval(iv) }
  }, [auto, answered, idx])

  const pick = (i: number) => { setAuto(false); setTick(0); setIdx(i) }
  const labels = s.etaLabels ?? ['Promised', 'Now expected', 'Latest by']
  return (
    <div className="card-stack">
      <div className="answer" aria-live="polite">
        <div className="a-head"><span className="label"><b>{s.brand}</b> · order {s.order}</span><span className="label">{s.at}</span></div>
        {/* Every scene's full text sits invisibly in the same cell, so typing never grows the card or moves the page. */}
        <div className="a-q"><div className="stack">
          {SCENES.map((x) => <p key={x.kind} className="ghost" aria-hidden="true">{x.q}</p>)}
          <AnimatePresence mode="wait"><motion.p key={idx} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: .3 }}>
            {s.q.slice(0, typed)}{typing && <span className="caret" />}<span className="tw-off">{s.q.slice(typed)}</span>
          </motion.p></AnimatePresence>
        </div></div>
        <div className="a-body">
          <span className={`who ${!typing && words === 0 ? 'think' : ''}`}><i />CIERTO</span>
          <div className="stack">
            {SCENES.map((x) => <p key={x.kind} className="ghost" aria-hidden="true">{rich(x.a, Infinity)}</p>)}
            <p>{rich(s.a, words)}</p>
          </div>
        </div>
        <div className="route"><Route key={idx} kind={s.kind} run={words > 6} /></div>
        <div className="eta">
          {s.eta.map((v, i) => (
            <div key={i}><span className="label">{labels[i]}</span><Roll value={v} className={i === 1 ? 'acc' : ''} /></div>
          ))}
        </div>
        <div className="a-src"><span className="label">Source · {s.src}</span></div>
      </div>
      <div className="causes" role="tablist" aria-label="WISMO causes">
        {SCENES.map((c, i) => (
          <button key={c.kind} role="tab" aria-selected={i === idx} onClick={() => pick(i)}>
            {c.tab}{i === idx && auto && <span className="bar" style={{ width: `${tick * 100}%` }} />}
          </button>
        ))}
      </div>
    </div>
  )
}
