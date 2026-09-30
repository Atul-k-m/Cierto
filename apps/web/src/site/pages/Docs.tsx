import { ArrowLeft, ArrowRight, BookOpen, Clock, Code2, Compass, Info } from 'lucide-react'
import { marked, type Token, type Tokens } from 'marked'
import { useEffect, useMemo, useState } from 'react'
import { docs } from '../docs'
import { CodeBlock } from '../parts/Code'
import { Cols } from '../parts/Chrome'

// Docs read in segments: a grouped sidebar, each H2 as its own numbered panel, real code blocks, and an
// "On this page" rail that follows the reader.
const GROUPS: { title: string; icon: React.ElementType; slugs: string[] }[] = [
  { title: 'Get started', icon: Compass, slugs: ['quickstart'] },
  { title: 'Guides', icon: BookOpen, slugs: ['integrate-smytten-like', 'integrate-zomato-like'] },
  { title: 'Reference', icon: Code2, slugs: ['api-reference', 'config-reference', 'webhooks'] },
]

const slugify = (s: string) => s.toLowerCase().replace(/<[^>]+>/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
const plain = (s: string) => s.replace(/`([^`]+)`/g, '$1').replace(/\*\*([^*]+)\*\*/g, '$1')

interface Seg { id: string; title: string; tokens: Token[] }

function split(body: string) {
  const tokens = marked.lexer(body)
  let title = ''
  const intro: Token[] = []
  const segs: Seg[] = []
  for (const t of tokens) {
    if (t.type === 'heading' && (t as Tokens.Heading).depth === 1 && !title) { title = (t as Tokens.Heading).text; continue }
    if (t.type === 'heading' && (t as Tokens.Heading).depth === 2) { const text = (t as Tokens.Heading).text; segs.push({ id: slugify(text), title: text.replace(/^\d+\.\s*/, ''), tokens: [] }); continue }
    if (segs.length) segs[segs.length - 1].tokens.push(t)
    else intro.push(t)
  }
  return { title, intro, segs }
}

function Block({ t }: { t: Token }) {
  if (t.type === 'code') {
    const c = t as Tokens.Code
    const lang = c.lang?.split(/\s+/)[0] ?? ''
    return <CodeBlock tabs={[{ label: lang || 'code', lang, code: c.text, file: lang === 'bash' || lang === 'sh' ? 'terminal' : undefined }]} />
  }
  if (t.type === 'blockquote') {
    const html = marked.parser((t as Tokens.Blockquote).tokens)
    return <aside className="callout"><Info size={16} aria-hidden="true" /><div dangerouslySetInnerHTML={{ __html: html }} /></aside>
  }
  if (t.type === 'heading' && (t as Tokens.Heading).depth === 3) {
    const h = t as Tokens.Heading
    return <h3 id={slugify(h.text)} dangerouslySetInnerHTML={{ __html: marked.parseInline(h.text) as string }} />
  }
  if (t.type === 'table') return <div className="table-wrap" dangerouslySetInnerHTML={{ __html: marked.parser([t]) }} />
  if (t.type === 'space') return null
  return <div className="doc-md" dangerouslySetInnerHTML={{ __html: marked.parser([t]) }} />
}

export function DocsPage({ slug }: { slug?: string }) {
  const current = docs.find((d) => d.slug === (slug ?? 'quickstart')) ?? docs[0]
  const { title, intro, segs } = useMemo(() => split(current?.body ?? ''), [current?.slug])
  const [active, setActive] = useState(segs[0]?.id)
  useEffect(() => {
    const els = segs.map((s) => document.getElementById(s.id)).filter(Boolean) as HTMLElement[]
    const io = new IntersectionObserver((es) => {
      const v = es.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]
      if (v) setActive(v.target.id)
    }, { rootMargin: '-90px 0px -60% 0px' })
    els.forEach((e) => io.observe(e))
    return () => io.disconnect()
  }, [current?.slug])
  const order = GROUPS.flatMap((g) => g.slugs).filter((s) => docs.some((d) => d.slug === s))
  const at = order.indexOf(current?.slug ?? '')
  const prev = at > 0 ? docs.find((d) => d.slug === order[at - 1]) : null
  const next = at >= 0 && at < order.length - 1 ? docs.find((d) => d.slug === order[at + 1]) : null
  const minutes = Math.max(2, Math.round((current?.body.split(/\s+/).length ?? 0) / 220))
  const group = GROUPS.find((g) => g.slugs.includes(current?.slug ?? ''))
  if (!current) return <main id="main" className="frame" style={{ padding: 96 }}><p className="lead">The SDK docs haven't been generated yet.</p></main>
  return (
    <main id="main" className="docs-shell">
      <div className="frame"><Cols />
        <div className="docs3">
          <nav className="dnav" aria-label="Documentation">
            {GROUPS.map((g) => (
              <div key={g.title} className="dnav-group">
                <p className="dnav-title"><g.icon size={14} aria-hidden="true" />{g.title}</p>
                {g.slugs.map((s) => { const d = docs.find((x) => x.slug === s); return d && (
                  <a key={s} href={`/docs/${s}`} aria-current={s === current.slug ? 'page' : undefined}>{plain(split(d.body).title || d.meta.title)}</a>
                ) })}
              </div>
            ))}
          </nav>

          <article className="dmain">
            <header className="dhead">
              <p className="dcrumb">{group?.title ?? 'Docs'}</p>
              <h1 className="display">{plain(title || current.meta.title)}</h1>
              <p className="dmeta"><Clock size={14} aria-hidden="true" />{minutes} min read · {segs.length} sections</p>
              <div className="dintro">{intro.map((t, k) => <Block key={k} t={t} />)}</div>
            </header>
            {segs.map((s, k) => (
              <section className="dseg" id={s.id} key={s.id}>
                <div className="dseg-head"><span className="dseg-n num">{String(k + 1).padStart(2, '0')}</span><h2 dangerouslySetInnerHTML={{ __html: marked.parseInline(s.title) as string }} /></div>
                <div className="dseg-body">{s.tokens.map((t, j) => <Block key={j} t={t} />)}</div>
              </section>
            ))}
            <nav className="dpager" aria-label="More docs">
              {prev ? <a href={`/docs/${prev.slug}`}><span>Previous</span><b><ArrowLeft size={15} aria-hidden="true" />{plain(split(prev.body).title || prev.meta.title)}</b></a> : <span />}
              {next && <a className="nx" href={`/docs/${next.slug}`}><span>Next</span><b>{plain(split(next.body).title || next.meta.title)}<ArrowRight size={15} aria-hidden="true" /></b></a>}
            </nav>
          </article>

          <aside className="dtoc" aria-label="On this page">
            <p className="dnav-title">On this page</p>
            {segs.map((s) => <a key={s.id} href={`#${s.id}`} aria-current={active === s.id ? 'true' : undefined}>{plain(s.title)}</a>)}
          </aside>
        </div>
      </div>
    </main>
  )
}
