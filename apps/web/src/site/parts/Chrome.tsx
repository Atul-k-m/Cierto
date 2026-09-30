import { ArrowRight, Menu, X } from 'lucide-react'
import { useEffect, useState } from 'react'

const LINKS = [
  { href: '/#product', label: 'Product' },
  { href: '/demos', label: 'Demos' },
  { href: '/case-studies', label: 'Case studies' },
  { href: '/docs', label: 'Docs' },
]

export function Logo() {
  return <a className="logo" href="/" aria-label="Cierto home"><i aria-hidden="true" />Cierto</a>
}

export function Nav({ path }: { path: string }) {
  const [open, setOpen] = useState(false)
  const here = path
  useEffect(() => { document.body.style.overflow = open ? 'hidden' : '' }, [open])
  return (
    <header className="nav">
      <div className="nav-in">
        <Logo />
        <nav className="nav-links" aria-label="Main">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} aria-current={l.href !== '/#product' && here.startsWith(l.href) ? 'page' : undefined}>{l.label}</a>
          ))}
        </nav>
        <span className="sp" />
        <a className="btn sm" href="/demos">Try it live <ArrowRight size={16} aria-hidden="true" /></a>
        <button className="burger" aria-label={open ? 'Close menu' : 'Open menu'} aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>
      {open && (
        <div className="sheet" role="dialog" aria-label="Menu">
          {LINKS.map((l) => <a key={l.href} href={l.href} onClick={() => setOpen(false)}>{l.label}</a>)}
          <a className="btn" href="/demos">Try it live <ArrowRight size={16} aria-hidden="true" /></a>
        </div>
      )}
    </header>
  )
}

const FOOT: { h: string; links: [string, string][] }[] = [
  { h: 'Product', links: [['How it answers', '/#product'], ['The SDK', '/#sdk'], ['Policy and guards', '/#policy'], ['Questions', '/#faq'], ['Live demo', '/demos']] },
  { h: 'Evidence', links: [['All case studies', '/case-studies'], ['Smytten', '/case-studies/smytten'], ['Swish', '/case-studies/swish'], ['Zomato', '/case-studies/zomato']] },
  { h: 'Build', links: [['Quickstart', '/docs/quickstart'], ['D2C parcel guide', '/docs/integrate-smytten-like'], ['Food delivery guide', '/docs/integrate-zomato-like'], ['API reference', '/docs/api-reference'], ['Webhooks', '/docs/webhooks']] },
  { h: 'About', links: [['Built by', '/built-by'], ['Privacy', '/privacy'], ['llms.txt', '/llms.txt'], ['Sitemap', '/sitemap.xml']] },
]

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-in">
        <div className="footer-brand">
          <Logo />
          <p>The AI layer for “where is my order?”. Every answer grounded, every promise kept, inside your policy.</p>
          <a className="btn sm footer-cta" href="/demos">Try it live <ArrowRight size={16} aria-hidden="true" /></a>
        </div>
        {FOOT.map((c) => (
          <nav key={c.h} aria-label={c.h}><h2>{c.h}</h2><ul>{c.links.map(([l, h]) => <li key={h}><a href={h}>{l}</a></li>)}</ul></nav>
        ))}
      </div>
      <div className="footer-base">
        <p className="footer-note">Cierto is a working proof of concept. Smytten, Swish and Zomato appear only in labelled case studies and demos built from public reviews; Cierto is not affiliated with them and has no access to their data.</p>
        <p className="footer-legal"><span>© 2026 Cierto</span><span>No cookies. No trackers.</span><a href="/privacy">Privacy</a></p>
      </div>
    </footer>
  )
}

export function More({ href, children }: { href: string; children: React.ReactNode }) {
  return <a className="more" href={href}>{children}<ArrowRight size={15} aria-hidden="true" /></a>
}

export function Cols() {
  return <div className="cols" aria-hidden="true">{Array.from({ length: 12 }, (_, i) => <i key={i} />)}</div>
}
