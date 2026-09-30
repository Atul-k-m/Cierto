import { ArrowRight } from 'lucide-react'
import { motion } from 'motion/react'
import { builtBy } from '../content'
import insights from '../data/insights.json'
import { HBars, Trend } from '../parts/Charts'
import { Cols, More } from '../parts/Chrome'
import { Mist } from '../parts/Mist'
import { Reveal } from '../parts/Motion'
import { PageHead } from '../parts/PageHead'
import { STUDIES, type Slug } from '../data/studies'

const EASE = [0.16, 1, 0.3, 1] as const

const head = (slug: Slug) => insights.compare.headline.find((h) => h.brand.toLowerCase() === slug)!

function StudyCard({ slug, i }: { slug: Slug; i: number }) {
  const s = STUDIES[slug], h = head(slug)
  const top = insights.brands[slug].categories.filter((c) => c.group === 'WISMO').sort((a, z) => (z.wismo ?? 0) - (a.wismo ?? 0)).slice(0, 3)
  return (
    <motion.a className="case-card" href={`/case-studies/${slug}`} initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 1, ease: EASE, delay: i * .1 }}>
      <Mist className="" cell={3} scale={140} bias={-.1} rise={.5} alpha={.9} />
      <div className="top"><span className="label">Case {String(i + 1).padStart(2, '0')}</span><span className="label">Read →</span></div>
      <h3>{s.name}</h3><p className="kind">{s.kind}</p>
      <div className="meter"><span className="label"><span>WISMO share of 1–2★</span><span>{h.wismo_low}%</span></span>
        <div className="segs">{Array.from({ length: 10 }, (_, k) => <i key={k} className={k < Math.round((h.wismo_low ?? 0) / 5) ? 'on' : ''} />)}</div></div>
      <ul>{top.map((t) => <li key={t.name}><span>{t.name}</span><span>{t.wismo}%</span></li>)}</ul>
    </motion.a>
  )
}

export function CaseStudies() {
  return (
    <main id="main">
      <PageHead title={<>Three apps.<br />Three shapes of WISMO.</>}
        lead={`We pulled ${insights.compare.headline.reduce((a, b) => a + (b.reviews ?? 0), 0).toLocaleString('en-IN')} recent app reviews plus complaint-board posts, classified every WISMO mention, and asked what Cierto would change. These are concept studies: not customers, not affiliated.`} />
      <div className="night"><section className="sec"><div className="frame"><Cols /><div className="sec-in">
        <div className="deck" style={{ marginTop: 0 }}>{(Object.keys(STUDIES) as Slug[]).map((slug, i) => <StudyCard key={slug} slug={slug} i={i} />)}</div>
      </div></div></section></div>
      <Method />
    </main>
  )
}

function Method() {
  const p = insights.compare.precision
  return (
    <section className="sec"><div className="frame"><Cols /><div className="sec-in">
      <Reveal className="sec-head">
        <h2 className="h2">Counted, not guessed. Lower bounds, not claims.</h2>
        <p className="lead">Reviews from Google Play and the App Store (India), plus consumer complaint boards, pulled 30 Sep 2026. A rule-based, explainable classifier in English and Hinglish tags each WISMO cause.</p>
      </Reveal>
      <div className="contract">
        <Reveal><b>Holdout precision</b><p>{p.map((x) => `${x.brand} ${x.v2}%`).join(' · ')} on a hand-labelled sample never used for tuning.</p></Reveal>
        <Reveal delay={.06}><b>Skewed on purpose</b><p>App reviews over-represent angry shoppers, so read the shares as “how the unhappy describe it”, not as order failure rates.</p></Reveal>
        <Reveal delay={.12}><b>Reproducible</b><p><code>python -m wismo_mining run --brands smytten,swish,zomato</code> rebuilds every number on these pages. Adding a brand is a config change.</p></Reveal>
      </div>
    </div></div></section>
  )
}

export function CaseStudy({ slug }: { slug: Slug }) {
  const s = STUDIES[slug]
  const b = insights.brands[slug]
  const h = head(slug)
  const sup = insights.compare.support.find((x) => x.brand.toLowerCase() === slug)!
  const wismoCats = b.categories.filter((c) => c.group === 'WISMO' && (c.wismo ?? 0) > 0).sort((a, z) => (z.wismo ?? 0) - (a.wismo ?? 0))
  const cross = b.categories.filter((c) => c.group !== 'WISMO' && (c.wismo ?? 0) > 0).sort((a, z) => (z.wismo ?? 0) - (a.wismo ?? 0)).slice(0, 5)
  const trend = ((b as { trend?: { month: string; wismo: number | null }[] }).trend ?? []).filter((t) => !/partial/.test(t.month))
  const quotes = s.quoteCats.flatMap((cat) => ((b.quotes as Record<string, { text: string; meta: string; url: string | null }[]>)[cat] ?? []).slice(0, 1).map((q) => ({ ...q, cat })))
  const others = (Object.keys(STUDIES) as Slug[]).filter((x) => x !== slug)
  return (
    <main id="main">
      <PageHead back={{ href: '/case-studies', label: 'All case studies' }} title={s.name} lead={s.line}>
        <p className="page-note">{s.kind} · concept study built from public reviews · not a customer, not affiliated</p>
      </PageHead>

      <section className="sec"><div className="frame"><Cols /><div className="sec-in">
        <Reveal className="chart focal" kind="wipe">
          <div className="focal-head">
            <p className="focal-num num">{h.wismo_low}<small>%</small></p>
            <div><h2 className="h3">of {s.name}'s 1–2★ reviews are about an order</h2>
              <p>{h.wismo_all}% of all {h.reviews?.toLocaleString('en-IN')} recent reviews · {sup.also_support}% of WISMO complaints also describe a support failure</p></div>
          </div>
          <HBars rows={wismoCats.map((c) => ({ label: c.name, value: c.wismo ?? 0 }))} max={100} />
          <p className="chart-foot">Share of {s.name}'s WISMO reviews mentioning each cause; a review can name several. n = {h.low_n?.toLocaleString('en-IN')} 1–2★ reviews.</p>
        </Reveal>
      </div></div></section>

      <section className="sec"><div className="frame"><Cols /><div className="sec-in">
        <Reveal className="sec-head"><h2 className="h2">What the data says</h2></Reveal>
        {trend.length >= 3 ? (
          <Reveal className="chart focal" kind="wipe">
            <div className="chart-head"><div><h3>WISMO share of 1–2★ reviews, by month</h3><p>Google Play, months with full coverage</p></div></div>
            <Trend points={trend} height={300} annotate />
          </Reveal>
        ) : null}
        <div className={`contract ${s.takeaways.length === 4 ? 'four' : ''}`}>{s.takeaways.map((t, i) => <Reveal key={i} delay={i * .08}><p>{t}</p></Reveal>)}</div>
        <Reveal className="chart" kind="wipe" style={{ marginTop: 48 }}>
          <div className="chart-head"><div><h3>Alongside WISMO</h3><p>What else the same reviews complain about</p></div></div>
          <HBars rows={cross.map((c) => ({ label: c.name, value: c.wismo ?? 0 }))} tone="ink" max={100} />
        </Reveal>
      </div></div></section>

      <div className="night"><section className="sec"><div className="frame"><Cols /><div className="sec-in">
        <Reveal className="sec-head"><h2 className="h2">Shoppers, verbatim</h2></Reveal>
        <div className="quotes">
          {quotes.map((q, i) => (
            <Reveal className="quote" key={i} kind="right" delay={i * .1}>
              <span className="label">{q.cat}</span>
              <blockquote>“{q.text}”</blockquote>
              <p className="label">{q.meta}{q.url && <> · <a href={q.url} target="_blank" rel="noreferrer">source</a></>}</p>
            </Reveal>
          ))}
        </div>
      </div></div></section></div>

      <section className="sec"><div className="frame"><Cols /><div className="sec-in">
        <Reveal className="sec-head"><h2 className="h2">From the review to the fix</h2></Reveal>
        <div className="plays">
          <div className="play play-head"><span className="label">Cause</span><span className="label">Today</span><span className="label">With Cierto</span></div>
          {s.plays.map((p, i) => (
            <Reveal className="play" kind="wipe" key={p.cause} delay={i * .1}><b>{p.cause}</b><span>{p.now}</span><span className="fix">{p.cierto}</span></Reveal>
          ))}
        </div>
        <div className="next">
          <a className="btn" href={`/demos?app=${slug}`}>See it in the {s.name} demo <ArrowRight size={16} aria-hidden="true" /></a>
          {others.map((o) => <More key={o} href={`/case-studies/${o}`}>{STUDIES[o].name} case study</More>)}
        </div>
      </div></div></section>
    </main>
  )
}

export function BuiltBy() {
  return (
    <main id="main">
      <PageHead title="Built by" lead={builtBy.meta.summary} />
      <section className="sec"><div className="frame"><Cols /><div className="sec-in" style={{ paddingTop: 56 }}>
        <article className="prose" dangerouslySetInnerHTML={{ __html: builtBy.html }} />
      </div></div></section>
    </main>
  )
}
