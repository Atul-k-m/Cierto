import { Check, Copy } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { HighlighterCore, ThemeRegistration } from 'shiki/core'

// Code that reads like code: an editor bar with file tabs and language, real syntax colours, line numbers, copy.
const THEME: ThemeRegistration = {
  name: 'cierto-night', type: 'dark',
  colors: { 'editor.background': '#0f1320', 'editor.foreground': '#d7dbe4' },
  tokenColors: [
    { scope: ['comment', 'punctuation.definition.comment'], settings: { foreground: '#6b7385', fontStyle: 'italic' } },
    { scope: ['keyword', 'storage', 'storage.type', 'keyword.control', 'keyword.operator.new', 'variable.language'], settings: { foreground: '#a9a2ff' } },
    { scope: ['string', 'string.quoted', 'punctuation.definition.string'], settings: { foreground: '#8fe3c0' } },
    { scope: ['constant.numeric', 'constant.language', 'constant.other', 'support.constant'], settings: { foreground: '#ffc978' } },
    { scope: ['entity.name.function', 'support.function', 'meta.function-call entity.name.function'], settings: { foreground: '#7cc4ff' } },
    { scope: ['variable.other.property', 'support.type.property-name', 'meta.object-literal.key', 'entity.other.attribute-name', 'variable.other.object.property'], settings: { foreground: '#ffa6c9' } },
    { scope: ['entity.name.tag', 'entity.name.tag.yaml', 'support.class.component'], settings: { foreground: '#a9a2ff' } },
    { scope: ['entity.name.type', 'support.type', 'entity.name.class'], settings: { foreground: '#ffd5a8' } },
    { scope: ['punctuation', 'meta.brace', 'keyword.operator'], settings: { foreground: '#8c93a2' } },
    { scope: ['variable.parameter', 'variable.other.readwrite'], settings: { foreground: '#e6e8ee' } },
    { scope: ['support.function.builtin.shell', 'entity.name.command'], settings: { foreground: '#7cc4ff' } },
  ],
}

let HL: Promise<HighlighterCore> | null = null
function highlighter() {
  if (!HL) HL = (async () => {
    const [{ createHighlighterCore }, { createJavaScriptRegexEngine }] = await Promise.all([import('shiki/core'), import('shiki/engine/javascript')])
    return createHighlighterCore({
      themes: [THEME],
      langs: [import('shiki/langs/javascript.mjs'), import('shiki/langs/typescript.mjs'), import('shiki/langs/tsx.mjs'), import('shiki/langs/bash.mjs'),
        import('shiki/langs/yaml.mjs'), import('shiki/langs/json.mjs'), import('shiki/langs/html.mjs'), import('shiki/langs/python.mjs')],
      engine: createJavaScriptRegexEngine(),
    })
  })()
  return HL
}

const ALIAS: Record<string, string> = { js: 'javascript', ts: 'typescript', sh: 'bash', shell: 'bash', curl: 'bash', console: 'bash', yml: 'yaml', jsx: 'tsx', py: 'python', http: 'bash', text: 'text', '': 'text' }
const norm = (l?: string) => { const k = (l ?? '').toLowerCase(); return ALIAS[k] ?? k }

/** True once the element is within a screen of the viewport: the highlighter (and its grammars) load only then. */
function useNear(ref: React.RefObject<HTMLElement | null>) {
  const [near, setNear] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el || near) return
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { setNear(true); io.disconnect() } }, { rootMargin: '600px 0px' })
    io.observe(el)
    return () => io.disconnect()
  }, [ref, near])
  return near
}

function useHighlighted(code: string, lang: string, near: boolean) {
  const [html, setHtml] = useState<string | null>(null)
  useEffect(() => {
    let alive = true
    const L = norm(lang)
    if (L === 'text') { setHtml(null); return }
    if (!near) return
    highlighter().then((h) => {
      if (!alive) return
      const langs = h.getLoadedLanguages()
      setHtml(h.codeToHtml(code, { lang: langs.includes(L) ? L : 'bash', theme: 'cierto-night' }))
    }).catch(() => {})
    return () => { alive = false }
  }, [code, lang, near])
  return html
}

export interface Snippet { label: string; code: string; lang: string; file?: string }

export function CodeBlock({ tabs, className = '' }: { tabs: Snippet[]; className?: string }) {
  const [i, setI] = useState(0)
  const [copied, setCopied] = useState(false)
  const t = tabs[Math.min(i, tabs.length - 1)]
  const box = useRef<HTMLDivElement>(null)
  const html = useHighlighted(t.code.replace(/\n+$/, ''), t.lang, useNear(box))
  const copy = () => { navigator.clipboard?.writeText(t.code).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1400) }) }
  return (
    <div className={`codeblock ${className}`} ref={box}>
      <div className="cb-bar">
        <span className="cb-dots" aria-hidden="true"><i /><i /><i /></span>
        {tabs.length > 1 ? (
          <div className="cb-tabs" role="tablist" aria-label="Code examples">
            {tabs.map((x, k) => <button key={x.label} role="tab" aria-selected={k === i} onClick={() => setI(k)}>{x.label}</button>)}
          </div>
        ) : <span className="cb-file">{t.file ?? t.label}</span>}
        <span className="cb-lang">{norm(t.lang) === 'text' ? 'text' : norm(t.lang)}</span>
        <button className="cb-copy" onClick={copy} aria-label="Copy code">{copied ? <Check size={14} /> : <Copy size={14} />}<span>{copied ? 'Copied' : 'Copy'}</span></button>
      </div>
      {html ? <div className="cb-body" dangerouslySetInnerHTML={{ __html: html }} />
        : <div className="cb-body"><pre className="shiki"><code>{t.code.replace(/\n+$/, '').split('\n').map((l, k) => <span className="line" key={k}>{l}{'\n'}</span>)}</code></pre></div>}
    </div>
  )
}
