import { ArrowRight, Plus } from 'lucide-react'
import { AnimatePresence, motion, useInView, useReducedMotion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { FAQ } from '../data/faq'
import insights from '../data/insights.json'
import { Answer } from '../parts/Answer'
import { Grouped } from '../parts/Charts'
import { Cols, More } from '../parts/Chrome'
import { CodeBlock } from '../parts/Code'
import { Mist } from '../parts/Mist'
import { Photo } from '../parts/Photo'
import { Reveal } from '../parts/Motion'

const EASE = [0.16, 1, 0.3, 1] as const
const H = insights.compare.headline
const byBrand = (b: string) => H.find((x) => x.brand.toLowerCase() === b)!
const SUPPORT = insights.compare.support
const cat = (b: 'smytten' | 'swish' | 'zomato', name: string) => insights.brands[b].categories.find((c) => c.name === name)?.wismo ?? 0
const HURTS = [
  { brand: 'Smytten', cause: 'Not received / where is it', value: cat('smytten', 'Not received / where is my order') },
  { brand: 'Swish', cause: 'Rider stuck or none assigned', value: cat('swish', 'Rider / parcel stuck, not moving') },
  { brand: 'Zomato', cause: 'Batched / multiple orders', value: cat('zomato', 'Multiple / batched orders') },
]

export function Home() {
  return (
    <main id="main">
      <Hero />
      <Marquees />
      <Problem />
      <PhotoBand base="street-cart" alt="A cycle cart stacked with parcels in city traffic" line="Every order is a promise made somewhere messy." note="Out on the road, the tracker is the only thing the shopper can see." />
      <Causes />
      <Sdk />
      <Grounded />
      <div className="night">
        <Policy />
        <Deck />
      </div>
      <Faq />
      <Close />
    </main>
  )
}

/* ---------- Hero ---------- */
function Hero() {
  // The entrance is CSS (.rise), so the headline animates as soon as the HTML and stylesheet arrive, not after hydration.
  const line = (text: string, i: number, cls = '') => (
    <span className="ln"><span className={`ln-rise ${cls}`} style={{ animationDelay: `${.1 + i * .09}s` }}>{text}</span></span>
  )
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="frame">
        <Cols />
        <div className="hero-in">
          <h1 id="hero-title" className="display hero-title">{line('Where is', 0)}{line('my order?', 1)}{line('Answered.', 2, 'acc')}</h1>
          <div className="hero-rest">
            <p className="lead enter d3">
              Cierto answers every order question from live courier, rider and payment data, and fixes what's wrong inside your policy,
              before the shopper has to ask.
            </p>
            <div className="ctas enter d4">
              <a className="btn" href="/docs/quickstart">Start integrating <ArrowRight size={16} aria-hidden="true" /></a>
              <a className="btn ghost" href="/demos">See it in 3 apps</a>
            </div>
          </div>
          <div className="stage">
            <Mist cell={3} scale={200} bias={.12} rise={.3} />
            <Answer />
          </div>
        </div>
      </div>
    </section>
  )
}

/* ---------- Marquees: who it's for, what it listens to ---------- */
const INDUSTRIES = ['D2C beauty & personal care', 'Food delivery', '10-minute quick commerce', 'Grocery', 'Pharmacy', 'Fashion & lifestyle', 'Electronics', 'Furniture & home', 'Courier aggregators', 'B2B distribution', 'Subscription boxes', 'Cloud kitchens']
const SOURCES = ['Courier scans', 'Rider GPS', 'Order management', 'Payment & refund status', 'Dispatch stop sequence', 'Address checks', 'Helpdesk tickets', 'WhatsApp replies', 'Maps traffic', 'Proof of delivery']

function Marquees() {
  const row = (items: string[], cls: string) => (
    <div className={`mq ${cls}`} aria-hidden="true">
      <div className="mq-track">{[...items, ...items].map((t, i) => <span key={i}>{t}<i /></span>)}</div>
    </div>
  )
  return (
    <section className="marquees" aria-label="Where Cierto fits">
      <p className="sr-only">Built for {INDUSTRIES.join(', ')}. Listens to {SOURCES.join(', ')}.</p>
      <div className="mq-label frame"><span>Built for any business that ships an order</span></div>
      {row(INDUSTRIES, 'big')}
      {row(SOURCES, 'small rev')}
    </section>
  )
}

function PhotoBand({ base, alt, line, note }: { base: string; alt: string; line: string; note: string }) {
  return (
    <section className="photoband" aria-label={alt}>
      <Photo base={base} alt={alt} sizes="100vw" width={1800} height={1012}
        motionProps={{ initial: { scale: 1.08 }, whileInView: { scale: 1 }, viewport: { once: false, amount: .2 }, transition: { duration: 1.6, ease: EASE } }} />
      <div className="frame photoband-in">
        <Reveal kind="wipe"><p className="pb-line">{line}</p></Reveal>
        <p className="pb-note">{note}</p>
      </div>
    </section>
  )
}

/* ---------- Problem: the data ---------- */
function Problem() {
  const hyp = insights.compare.hypotheses
  const rows = hyp.map((h) => ({ label: h.name.replace(' / unreachable', '').replace('Poor or vague "where is my order" answers', 'Vague WISMO answers'), values: h.values }))
  const total = H.reduce((a, b) => a + (b.reviews ?? 0), 0)
  return (
    <section className="sec" id="problem" aria-labelledby="problem-title">
      <div className="frame"><Cols />
        <div className="sec-in">
          <Reveal className="sec-head wide">
            <h2 className="h2" id="problem-title">Shoppers don't ask where. They ask why it's late.</h2>
            <p className="lead">{total.toLocaleString('en-IN')} recent app reviews and complaint posts for Smytten, Swish and Zomato, classified cause by cause.</p>
          </Reveal>
          <div className="problem-grid">
            <div className="stick">
            <Reveal className="chart" kind="wipe">
              <div className="chart-head"><div><h3>WISMO share of 1–2★ reviews</h3><p>How much of each app's anger is about an order</p></div></div>
              <div className="brandbars">
                {H.map((b, i) => (
                  <div className="brandbar" key={b.brand}>
                    <span className="bb-name">{b.brand}</span>
                    <span className="bb-track"><motion.i initial={{ scaleX: 0 }} whileInView={{ scaleX: (b.wismo_low ?? 0) / 30 }} viewport={{ once: true }} transition={{ duration: 1.3, ease: EASE, delay: .2 + i * .12 }} /></span>
                    <span className="bb-num num">{b.wismo_low}<small>%</small></span>
                  </div>
                ))}
              </div>
              <p className="chart-note"><b>{SUPPORT[0].dnr_support}%</b> of Smytten's “delivered, not received” complaints also hit a dead support loop. Zomato: {SUPPORT[2].dnr_support}%.</p>
            </Reveal>
            <Reveal className="chart hurts" kind="wipe" delay={.15}>
              <div className="chart-head"><div><h3>Where it hurts most</h3><p>Each app's most distinctive WISMO cause</p></div></div>
              <ul>
                {HURTS.map((x) => (
                  <li key={x.brand}><span className="h-brand">{x.brand}</span><span className="h-cause">{x.cause}</span><span className="h-num num">{x.value}%</span></li>
                ))}
              </ul>
              <a className="more" href="/case-studies">Read the case studies</a>
            </Reveal>
            </div>
            <Reveal className="chart" kind="wipe" delay={.1}>
              <div className="chart-head"><div><h3>What WISMO reviews complain about</h3><p>Share of each brand's WISMO reviews that mention the cause</p></div></div>
              <Grouped rows={rows} series={['Smytten', 'Swish', 'Zomato']} />
              <p className="chart-foot">Google Play, App Store and complaint boards, pulled 30 Sep 2026. Rule-based classifier, 87–93% holdout precision; shares are lower bounds. <a className="more" href="/case-studies">Method and quotes</a></p>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ---------- Six causes ---------- */
const stroke = { stroke: '#0b0f17', strokeWidth: 2, fill: 'none' }
const CAUSES = [
  { n: '01', h: 'Late and slipping', p: 'ETAs that drift without a word. The top complaint for every brand.',
    says: 'New estimate 1:42 pm, never later than 1:50. We only message again if that changes.',
    viz: <svg viewBox="0 0 300 120"><line x1="10" y1="96" x2="290" y2="96" stroke="#d6d7dd" /><rect x="40" y="40" width="150" height="14" fill="#ecebff" /><rect x="40" y="40" width="96" height="14" fill="#3a2bff" /><line x1="190" y1="30" x2="190" y2="66" stroke="#0b0f17" strokeDasharray="3 3" /><text x="40" y="30" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#555c6a">NOW 1:42</text><text x="196" y="30" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#0b0f17">LATEST 1:50</text><text x="40" y="84" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#555c6a">PROMISED 1:33 · +9 MIN TRAFFIC</text></svg> },
  { n: '02', h: 'Rider stuck', p: 'A dot that hasn’t moved. Waiting at the kitchen, a jam, or a problem.',
    says: 'Anubhav has been stopped 4 minutes at the Agara junction. You’re his next and only drop.',
    viz: <svg viewBox="0 0 300 120"><path d="M20 90 C 80 90, 110 40, 170 50" {...stroke} /><path d="M170 50 C 220 58, 250 30, 280 24" stroke="#c9cbe0" strokeWidth="2" strokeDasharray="2 6" fill="none" /><circle cx="170" cy="50" r="18" fill="#3a2bff" opacity=".12" /><circle cx="170" cy="50" r="6" fill="#3a2bff" /><text x="186" y="80" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#3a2bff">STOPPED 4:12</text></svg> },
  { n: '03', h: 'Batched orders', p: 'The rider turns the other way. Nobody says they’re dropping someone else first.',
    says: 'Rahul is dropping one other order 600 m from you first. You’re next: 1:38 pm.',
    viz: <svg viewBox="0 0 300 120"><path d="M20 90 L 120 60 L 190 86 L 280 30" {...stroke} /><rect x="182" y="78" width="16" height="16" fill="none" stroke="#3a2bff" strokeWidth="2" /><rect x="272" y="22" width="16" height="16" fill="#0b0f17" /><text x="150" y="112" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#3a2bff">STOP 1 · OTHER</text><text x="222" y="16" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#0b0f17">STOP 2 · YOU</text></svg> },
  { n: '04', h: 'Bad address', p: 'The pin says one place, the text another. The rider calls; the parcel goes back.',
    says: 'Your pin is 1.2 km from the address you typed. Tap the right spot before 12:30 to keep today’s delivery.',
    viz: <svg viewBox="0 0 300 120"><circle cx="70" cy="70" r="7" fill="#0b0f17" /><rect x="222" y="56" width="16" height="16" fill="#3a2bff" /><path d="M78 64 C 130 20, 190 20, 222 60" stroke="#3a2bff" strokeWidth="2" strokeDasharray="5 5" fill="none" /><text x="116" y="22" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#3a2bff">1.2 KM APART</text><text x="40" y="100" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#555c6a">PIN</text><text x="206" y="100" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#555c6a">TYPED</text></svg> },
  { n: '05', h: 'Silent courier', p: 'Three days, no scan. The tracker shows the last thing it knew as if it were now.',
    says: 'No scan since Fri at Bhiwandi. We’ve asked Delhivery to trace it; the remedy starts Tue 6 pm if not.',
    viz: <svg viewBox="0 0 300 120"><line x1="20" y1="60" x2="280" y2="60" stroke="#e1e2ea" strokeWidth="2" />{[20, 70, 110, 140].map((x) => <circle key={x} cx={x} cy="60" r="6" fill="#0b0f17" />)}<line x1="140" y1="60" x2="280" y2="60" stroke="#3a2bff" strokeWidth="2" strokeDasharray="3 6" /><text x="170" y="44" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#3a2bff">NO SCAN · 72 H</text><text x="100" y="88" fontSize="11" fontFamily="JetBrains Mono Variable, monospace" fill="#555c6a">LAST · BHIWANDI</text></svg> },
  { n: '06', h: 'Delivered, not received', p: 'A “delivered” with no OTP, photo or call, and a bot that repeats it back.',
    says: 'Marked delivered with no OTP or photo, so it isn’t proven. Refund starts Fri 2:05 pm unless Delhivery proves it.',
    viz: <svg viewBox="0 0 300 120">{['OTP', 'PHOTO', 'CALL', 'YOU'].map((l, i) => <g key={l} transform={`translate(${10 + i * 72} 34)`}><rect width="62" height="52" fill={i === 3 ? '#ecebff' : '#fff'} stroke={i === 3 ? '#3a2bff' : '#d8d9e2'} /><text x="8" y="20" fontSize="10" fontFamily="JetBrains Mono Variable, monospace" fill="#555c6a">{l}</text><text x="8" y="40" fontSize="13" fontWeight="600" fill={i === 3 ? '#3a2bff' : '#b3243f'}>{i === 3 ? 'Asked' : 'None'}</text></g>)}</svg> },
]

function Causes() {
  return (
    <section className="sec" id="product" aria-labelledby="causes-title">
      <div className="frame"><Cols />
        <div className="sec-in">
          <Reveal className="sec-head">
            <h2 className="h2" id="causes-title">Every “where is it?” has a reason. Cierto says it.</h2>
            <p className="lead">Not “your order is on the way”. The actual cause, from the actual data, with a new promise and what happens if it's missed.</p>
          </Reveal>
          <div className="cause-grid">
            {CAUSES.map((c, i) => (
              <Reveal className="cause" key={c.n} kind="wipe" delay={(i % 3) * .12 + Math.floor(i / 3) * .1}>
                <h3>{c.h}</h3>
                <p>{c.p}</p>
                <div className="viz" aria-hidden="true">{c.viz}</div>
                <p className="says"><b>CIERTO SAYS</b>{c.says}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

/* ---------- Grounded answer contract ---------- */
const INS = [['Courier scans', 'Delhivery · Shiprocket'], ['Rider GPS', 'your fleet app'], ['Orders & payments', 'OMS · UPI refunds'], ['Maps & traffic', 'ETA · geocoder']]
const OUTS = [['In-app widget', 'order card · tracker'], ['WhatsApp', 'proactive updates'], ['Chat & email', 'your helpdesk'], ['Support console', 'cases · approvals']]

function Grounded() {
  const reduce = useReducedMotion()
  return (
    <section className="sec on-mist" aria-labelledby="grounded-title">
      <Mist cell={3} scale={240} bias={-.18} rise={.55} alpha={.55} />
      <div className="frame"><Cols />
        <div className="sec-in">
          <Reveal className="sec-head center">
            <h2 className="h2" id="grounded-title">Only what the data says, everywhere they ask.</h2>
            <p className="lead">Cierto joins your order, courier, rider and payment feeds into one timeline, then answers the same way in every channel. If the data is stale, it says so.</p>
          </Reveal>
          <div className="flow">
            <div className="flow-col">{INS.map(([b, l], i) => <Reveal className="node" kind="left" key={b} delay={i * .08}><b>{b}</b><span className="label">{l}</span></Reveal>)}</div>
            <div className="core">
              <svg viewBox="0 0 100 100" aria-hidden="true">
                {[-30, -10, 10, 30].map((dy, i) => (
                  <g key={i}>
                    <path d={`M-20 ${50 + dy * 1.2} C 10 ${50 + dy}, 20 50, 30 50`} stroke="rgb(11 15 23 / .2)" fill="none" vectorEffect="non-scaling-stroke" />
                    <path d={`M70 50 C 80 50, 90 ${50 + dy}, 120 ${50 + dy * 1.2}`} stroke="rgb(11 15 23 / .2)" fill="none" vectorEffect="non-scaling-stroke" />
                    {!reduce && <motion.circle r="1.2" fill="#3a2bff" animate={{ cx: [-20, 30], cy: [50 + dy * 1.2, 50] }} transition={{ duration: 1.8, repeat: Infinity, delay: i * .45, ease: 'easeInOut' }} />}
                    {!reduce && <motion.circle r="1.2" fill="#3a2bff" animate={{ cx: [70, 120], cy: [50, 50 + dy * 1.2] }} transition={{ duration: 1.8, repeat: Infinity, delay: .9 + i * .45, ease: 'easeInOut' }} />}
                  </g>
                ))}
              </svg>
              <div className="core-in"><span className="label">One timeline</span><b>Cierto</b><span className="label">answers · acts · escalates</span></div>
            </div>
            <div className="flow-col">{OUTS.map(([b, l], i) => <Reveal className="node" kind="right" key={b} delay={.3 + i * .08}><b>{b}</b><span className="label">{l}</span></Reveal>)}</div>
          </div>
          <div className="contract">
            <Reveal><b>Grounded</b><p>Every answer names its source and how fresh it is. No invented dates, no “it's on the way” when nothing has moved.</p></Reveal>
            <Reveal delay={.06}><b>A promise, and a fallback</b><p>A new time, a latest-by, and what happens automatically if it's missed: a credit, a refund, or a person.</p></Reveal>
            <Reveal delay={.12}><b>Before they ask</b><p>Slips, stalls and address problems reach the shopper first, in your app or on WhatsApp, in English or Hinglish.</p></Reveal>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ---------- Policy (night) ---------- */
const POLICY_YAML = `# versioned, simulated before it ships
late:
  notify_after_min: 3
  credit_after_min: 10
rider_stalled:
  explain_after_min: 4
  offer_cancel_after_min: 10
refunds:
  auto_cap_inr: 500
  to: original_payment_method
escalate: [above_cap, second_contact]
language: [en-IN, hi-Latn-IN]
`

function Policy() {
  return (
    <section className="sec" id="policy" aria-labelledby="policy-title">
      <div className="frame"><Cols />
        <div className="sec-in">
          <Reveal className="sec-head">
            <h2 className="h2" id="policy-title">An agent that can act, only as far as you let it.</h2>
            <p className="lead">Credits, cancellations, reattempts and refunds follow rules you write and can test. The language model explains the decision; it never picks the amount.</p>
          </Reveal>
          <div className="policy">
            <Reveal kind="wipe"><CodeBlock tabs={[{ label: 'policies/swish.yaml', file: 'policies/swish.yaml', lang: 'yaml', code: POLICY_YAML }]} /></Reveal>
            <div className="decisions">
              {[
                ['SWH-40193877 · ₹228', 'Late 11 min: credit applied, shopper told why', 'Rider stalled in traffic, under the ₹500 cap, first contact.', 'auto', 'Automatic'],
                ['SMY-4790112 · ₹2,400', 'Refund proposed, waiting for approval', 'Above the cap. The evidence and a draft reply are attached for your team.', 'human', 'Approval'],
                ['ZMT-7729381044 · ₹412', 'Handed to a person with the whole case', 'Second contact in 20 minutes, so no more automation.', 'human', 'Human'],
              ].map(([o, h, p, c, l], k) => (
                <Reveal className="decision" kind="right" key={o} delay={.2 + k * .1}><div className="decision-top"><span className="label">{o}</span><span className={`chip ${c}`}>{l}</span></div><h3>{h}</h3><p>{p}</p></Reveal>
              ))}
            </div>
          </div>
          <div className="guards">
            {[['Never a vague answer', 'Every reply names a cause, a time and a source.'], ['Never above your cap', 'Bigger refunds wait for a person, with evidence.'],
              ['Never closes on a reply', 'A case ends on delivery, a refund reference or a reship.'], ['Never hides the human', '“Talk to a person” is always one tap away.']].map(([b, s]) => (
              <div key={b}><b>{b}</b><span>{s}</span></div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

/* ---------- Case deck (night) ---------- */
function Deck() {
  const cards = (['smytten', 'swish', 'zomato'] as const).map((slug) => {
    const b = insights.brands[slug]
    const h = byBrand(slug)
    const top = b.categories.filter((c) => c.group === 'WISMO').sort((a, z) => (z.wismo ?? 0) - (a.wismo ?? 0)).slice(0, 3)
    return { slug, name: h.brand, kind: slug === 'smytten' ? 'D2C · courier · days' : slug === 'swish' ? '10-min food · minutes' : 'Food delivery · minutes', low: h.wismo_low ?? 0, top }
  })
  return (
    <section className="sec" aria-labelledby="deck-title">
      <div className="frame"><Cols />
        <div className="sec-in">
          <Reveal className="sec-head wide">
            <h2 className="h2" id="deck-title">Three apps. Three shapes of WISMO. One engine.</h2>
            <p className="lead">Built from each app's own public reviews. Concept studies: not customers, not affiliated.</p>
          </Reveal>
          <div className="deck">
            {cards.map((c, i) => (
              <motion.a key={c.slug} className="case-card" href={`/case-studies/${c.slug}`} initial={{ opacity: 0, y: 40, rotate: i === 0 ? -1.5 : i === 2 ? 1.5 : 0 }}
                whileInView={{ opacity: 1, y: 0, rotate: 0 }} viewport={{ once: true, margin: '-80px 0px' }} transition={{ duration: 1, ease: EASE, delay: i * .1 }}>
                <Mist className="" cell={3} scale={140} bias={-.1} rise={.5} alpha={.9} />
                <div className="top"><span className="label">Case {String(i + 1).padStart(2, '0')}</span><span className="label">Read →</span></div>
                <h3>{c.name}</h3>
                <p className="kind">{c.kind}</p>
                <div className="meter"><span className="label"><span>WISMO share of 1–2★</span><span>{c.low}%</span></span>
                  <div className="segs">{Array.from({ length: 10 }, (_, k) => <i key={k} className={k < Math.round(c.low / 5) ? 'on' : ''} />)}</div></div>
                <ul>{c.top.map((t) => <li key={t.name}><span>{t.name}</span><span>{t.wismo}%</span></li>)}</ul>
              </motion.a>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

/* ---------- SDK: the easy part ---------- */
const STEPS = [
  { n: 'Install', t: '5 min', d: 'One package, or one script tag. Test keys work against four ready-made orders.', tabs: [
    { label: 'npm', lang: 'bash', code: 'npm install @cierto/js' },
    { label: 'script tag', lang: 'html', code: '<script src="https://js.cierto.dev/v1/cierto.js"></script>' },
  ] },
  { n: 'Send events', t: '1–2 hours', d: 'Forward what your courier, rider app and payment gateway already send you. Cierto keeps who said what.', tabs: [
    { label: 'Courier webhook', lang: 'ts', code: `// forward what your courier already sends you
app.post('/webhooks/courier', async (req, res) => {
  await cierto.events.create({
    order_ref: req.body.order_id,
    type: 'carrier.scan',
    asserted_by: 'carrier',
    data: { status: req.body.status, location: req.body.city },
  })
  res.sendStatus(200)
})` },
    { label: 'Rider GPS', lang: 'bash', code: `curl https://api.cierto.dev/v1/events \\
  -H "Authorization: Bearer sk_test_swish" \\
  -d '{ "order_ref": "SWH-40193877", "type": "rider.location",
        "data": { "lat": 12.923, "lng": 77.671 } }'` },
  ] },
  { n: 'Show the answer', t: '30 min', d: 'Drop the widget into your order card, or render the answer yourself from the headless view.', tabs: [
    { label: 'Web Component', lang: 'html', code: `<cierto-order order="SWH-40193877" variant="tracking-card"></cierto-order>
<script>
  Cierto.init({ publishableKey: 'pk_test_swish', fetchClientSecret,
    appearance: { theme: 'swish' }, locale: 'hi-Latn-IN' })
</script>` },
    { label: 'React', lang: 'tsx', code: `import { CiertoProvider, CiertoOrder } from '@cierto/js/react'

export function Tracking({ id }: { id: string }) {
  return (
    <CiertoProvider publishableKey="pk_test_swish" fetchClientSecret={getSecret}>
      <CiertoOrder orderId={id} variant="tracking-card" />
    </CiertoProvider>
  )
}` },
    { label: 'Headless', lang: 'ts', code: `const view = await cierto.headless.order('ZMT-7729381044').get()
view.headline   // "Rahul is dropping one other order first"
view.eta        // { now: "13:38", latest_by: "13:45" }
view.sources    // ["dispatch", "rider_gps@20s"]` },
  ] },
]
const PLATFORMS: [string, 'live' | 'next'][] = [['Web Component', 'live'], ['React', 'live'], ['Headless JSON', 'live'], ['Server events', 'live'], ['Signed webhooks', 'live'], ['WhatsApp via webhooks', 'live'], ['React Native', 'next'], ['Android', 'next'], ['iOS', 'next'], ['Flutter', 'next']]
const THEMES = [{ id: 'smytten', c: '#2f6fbd' }, { id: 'zomato', c: '#cb202d' }, { id: 'swish', c: '#1a7f4b' }, { id: 'neutral', c: '#1f2328' }]

/** The live widget and its demo session load only when the studio comes near the viewport. */
function useSession(near: boolean) {
  const [s, setS] = useState<string | null>(null)
  useEffect(() => {
    if (!near) return
    Promise.all([import('../../widget/element'), fetch('/v1/demo/sessions', { method: 'POST' }).then((r) => r.json())]).then(async ([, x]) => {
      await fetch(`/v1/demo/sessions/${x.id}/advance`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ beat: 'claimed' }) })
      setS(x.id)
    }).catch(() => {})
  }, [near])
  return s
}

/** Three steps on the left, one full-width code panel on the right that follows the chosen step. */
function Stepper() {
  const [i, setI] = useState(0)
  const st = STEPS[i]
  return (
    <Reveal className="stepper" kind="rise">
      <div className="stepper-list">
        <div role="tablist" aria-label="Integration steps">
          {STEPS.map((x, k) => (
            <button key={x.n} role="tab" id={`step-${k}`} aria-selected={k === i} aria-controls="step-code" onClick={() => setI(k)}>
              <span className="step3-n num">{k + 1}</span>
              <span className="stepper-copy"><b>{x.n}</b><span>{x.d}</span></span>
              <span className="step3-t">{x.t}</span>
            </button>
          ))}
        </div>
        <p className="stepper-total"><span>Typical total</span><b>An afternoon</b></p>
      </div>
      <div className="stepper-code" id="step-code" role="tabpanel" aria-labelledby={`step-${i}`}>
        <AnimatePresence mode="wait">
          <motion.div key={i} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }} transition={{ duration: .35, ease: EASE }}>
            <CodeBlock tabs={st.tabs} />
          </motion.div>
        </AnimatePresence>
      </div>
    </Reveal>
  )
}

function Sdk() {
  const studio = useRef<HTMLDivElement>(null)
  const session = useSession(useInView(studio, { once: true, margin: '400px 0px' }))
  const [theme, setTheme] = useState('swish')
  const order = theme === 'zomato' ? 'zomato' : theme === 'swish' ? 'swish' : 'smytten-delivered'
  return (
    <section className="sec sdk-sec" id="sdk" aria-labelledby="sdk-title">
      <div className="frame"><Cols />
        <div className="sec-in">
          <Reveal className="sec-head wide">
            <h2 className="h2" id="sdk-title">Integrate in an afternoon. Keep your app, your brand, your helpdesk.</h2>
            <p className="lead">Cierto is an SDK, not a new app for your shoppers. Send the events you already have, drop the answer into the screen you already own.</p>
          </Reveal>
          <Stepper />
          <div className="sdk-grid">
            <Reveal className="studio" kind="scale">
              <Mist cell={3} scale={180} bias={-.25} rise={.6} alpha={.45} />
              <div className="theme-pick" role="group" aria-label="Preview theme">
                {THEMES.map((t) => <button key={t.id} aria-pressed={theme === t.id} onClick={() => setTheme(t.id)}><i style={{ background: t.c }} />{t.id}</button>)}
              </div>
              <div className="studio-widget" ref={studio}>{session && <wismo-order session={session} order={order} variant="tracking-card" theme={theme} />}</div>
              <p className="studio-cap">Same engine, one token file per brand. Switch the theme.</p>
            </Reveal>
            <Reveal className="platforms" kind="right">
              <h3 className="h3">Runs where your shoppers already are</h3>
              <ul>{PLATFORMS.map(([n, st]) => <li key={n}><span>{n}</span><span className={`pill ${st}`}>{st === 'live' ? 'Available' : 'Designed, next'}</span></li>)}</ul>
              <More href="/docs/quickstart">Quickstart: live in five minutes</More>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ---------- Questions: plain answers, also published as FAQPage structured data ---------- */
function Faq() {
  return (
    <section className="sec" id="faq" aria-labelledby="faq-title">
      <div className="frame"><Cols />
        <div className="sec-in faq">
          <Reveal className="faq-head">
            <h2 className="h2" id="faq-title">Questions buyers ask first.</h2>
            <p className="lead">Short answers. The <a className="more" href="/docs/quickstart">docs</a> have the long ones.</p>
          </Reveal>
          <div className="faq-list">
            {FAQ.map((f, i) => (
              <details key={f.q} open={i === 0}>
                <summary><span className="faq-n num">{String(i + 1).padStart(2, '0')}</span><span className="faq-q">{f.q}</span><Plus className="faq-x" size={20} aria-hidden="true" /></summary>
                <p>{f.a}</p>
              </details>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function Close() {
  return (
    <section className="close" aria-labelledby="close-title">
      <Photo className="close-photo" base="courier-portrait-acc" alt="" sizes="(max-width: 900px) 100vw, 46vw" width={1800} height={1200} />
      <Mist color={[255, 255, 255]} cell={3} scale={200} bias={-.25} rise={.5} alpha={.3} />
      <div className="frame"><div className="close-in">
        <h2 id="close-title">Answer the next “where is my order?” before it's asked.</h2>
        <div className="ctas"><a className="btn" href="/docs/quickstart">Start integrating <ArrowRight size={16} aria-hidden="true" /></a><a className="btn ghost" href="/case-studies">Read the case studies</a></div>
      </div></div>
    </section>
  )
}
