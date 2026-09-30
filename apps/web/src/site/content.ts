import { marked } from 'marked'

// Site content is plain markdown with a small header block, bundled at build time.
export interface Doc { slug: string; meta: Record<string, string>; html: string; body: string }

const site = import.meta.glob('./content/**/*.md', { query: '?raw', import: 'default', eager: true }) as Record<string, string>

export function parse(path: string, source: string): Doc {
  const raw = source.split(String.fromCharCode(13)).join('')
  const slug = path.split('/').pop()!.replace(/\.md$/, '')
  const m = raw.match(/^---\n([\s\S]*?)\n---\n?/)
  const meta: Record<string, string> = {}
  if (m) for (const line of m[1].split('\n')) {
    const i = line.indexOf(':')
    if (i > 0) meta[line.slice(0, i).trim()] = line.slice(i + 1).trim()
  }
  const body = m ? raw.slice(m[0].length) : raw
  if (!meta.title) meta.title = body.match(/^#\s+(.+)$/m)?.[1] ?? slug
  const html = marked.parse(m ? body : body.replace(/^#\s+.+\n/, ''), { async: false }) as string
  return { slug, meta, html, body }
}

export const builtBy = Object.entries(site).map(([p, raw]) => parse(p, raw)).find((d) => d.slug === 'built-by')!

export const fmtPostDate = (iso: string) =>
  new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(iso))
