import { builtBy } from './content'
import { FAQ } from './data/faq'
import insights from './data/insights.json'
import { docs } from './docs'
import type { PageKey } from './pages'
import { STUDIES } from './data/studies'

// Build-time only (the prerender bundle): every route's head, structured data, sitemap, robots and the
// llms.txt family. Absolute URLs use the __SITE_URL__ token; the server swaps in the real origin at response time.
const SITE = '__SITE_URL__'
const NAME = 'Cierto'
const UPDATED = '2026-09-30'
type Slug = keyof typeof STUDIES

export interface Route {
  path: string; page: PageKey; slug?: string
  title: string; description: string; og: string
  canonical?: string; noindex?: boolean; priority?: number
  jsonld: Record<string, unknown>[]
}

const H = insights.compare.headline
const REVIEWS = H.reduce((a, b) => a + (b.reviews ?? 0), 0)
const brandHead = (slug: string) => H.find((h) => h.brand.toLowerCase() === slug)!

const plain = (md: string) => md.replace(/`([^`]+)`/g, '$1').replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1')
  .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\s+/g, ' ').trim()
function clip(s: string, n = 158) {
  if (s.length <= n) return s
  const cut = s.slice(0, n - 1)
  return cut.slice(0, cut.lastIndexOf(' ')).replace(/[,;:.\s]+$/, '') + '…'
}
function docInfo(body: string) {
  const title = plain(body.match(/^#\s+(.+)$/m)?.[1] ?? '')
  const para = body.replace(/^#\s+.+$/m, '').split(/\n\s*\n/).map((p) => p.trim()).find((p) => p && !/^[#>|`\-*]/.test(p)) ?? ''
  return { title, description: clip(plain(para)) }
}

const ORG = { '@type': 'Organization', '@id': `${SITE}/#org`, name: NAME, url: `${SITE}/`, logo: `${SITE}/icon-512.png`,
  description: 'Cierto builds the AI layer for “where is my order?”: grounded answers from live order data, and fixes inside the business’s own policy.' }
const crumbs = (items: [string, string][]) => ({
  '@type': 'BreadcrumbList',
  itemListElement: items.map(([name, path], i) => ({ '@type': 'ListItem', position: i + 1, name, item: `${SITE}${path}` })),
})
const page = (path: string, name: string, description: string) =>
  ({ '@type': 'WebPage', '@id': `${SITE}${path}#page`, url: `${SITE}${path}`, name, description, isPartOf: { '@id': `${SITE}/#site` }, dateModified: UPDATED })

const HOME_DESC = 'Cierto is an AI SDK for “where is my order?”. It answers every order question from live courier, rider and payment data, names the real cause of a delay, and fixes problems inside your policy.'

export const routes: Route[] = [
  {
    path: '/', page: 'home', priority: 1, og: '/og/home.png',
    title: 'Cierto · Where is my order? Answered.',
    description: HOME_DESC,
    jsonld: [
      ORG,
      { '@type': 'WebSite', '@id': `${SITE}/#site`, url: `${SITE}/`, name: NAME, publisher: { '@id': `${SITE}/#org` }, inLanguage: 'en-IN' },
      { '@type': 'SoftwareApplication', name: `${NAME} SDK`, applicationCategory: 'BusinessApplication', operatingSystem: 'Web',
        description: HOME_DESC, url: `${SITE}/`, publisher: { '@id': `${SITE}/#org` },
        featureList: ['Grounded order answers with sources and freshness', 'Cause detection: stuck rider, traffic, batched orders, bad address, silent courier, delivered but not received',
          'Policy-gated refunds, credits and cancellations', 'English and Hinglish', 'Web Component, React, headless JSON, server events, signed webhooks'] },
      { '@type': 'FAQPage', mainEntity: FAQ.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })) },
    ],
  },
  {
    path: '/demos', page: 'demos', priority: .9, og: '/og/demos.png',
    title: 'Live demo · Cierto inside three delivery apps',
    description: 'Pick an app and a problem (a stuck rider, traffic, a batched order, a bad address, a silent courier), move the clock and ask like a shopper, in English or Hinglish.',
    jsonld: [page('/demos', 'Cierto live demo', 'Cierto answering order questions inside three concept apps.')],
  },
  {
    path: '/case-studies', page: 'case-studies', priority: .8, og: '/og/case-studies.png',
    title: 'WISMO case studies from public reviews · Cierto',
    description: clip(`${REVIEWS.toLocaleString('en-IN')} app reviews of Smytten, Swish and Zomato, classified cause by cause: what shoppers mean by “where is my order?” and what would fix it.`),
    jsonld: [{ '@type': 'CollectionPage', '@id': `${SITE}/case-studies#page`, url: `${SITE}/case-studies`, name: 'WISMO case studies',
      hasPart: (Object.keys(STUDIES) as Slug[]).map((s) => ({ '@type': 'Article', headline: `${STUDIES[s].name}: WISMO case study`, url: `${SITE}/case-studies/${s}` })) },
      crumbs([['Home', '/'], ['Case studies', '/case-studies']])],
  },
  ...(Object.keys(STUDIES) as Slug[]).map((slug): Route => {
    const s = STUDIES[slug], h = brandHead(slug)
    const description = clip(`${h.wismo_low}% of ${s.name}'s 1–2★ reviews are about an order. ${s.line}`)
    return {
      path: `/case-studies/${slug}`, page: 'case-study', slug, priority: .7, og: `/og/case-study-${slug}.png`,
      title: `${s.name}: where-is-my-order complaints, mined · Cierto`, description,
      jsonld: [{ '@type': 'Article', headline: `${s.name}: WISMO case study`, description, datePublished: UPDATED, dateModified: UPDATED,
        author: { '@id': `${SITE}/#org` }, publisher: { '@id': `${SITE}/#org` }, image: `${SITE}/og/case-study-${slug}.png`,
        mainEntityOfPage: `${SITE}/case-studies/${slug}`, about: 'Where is my order (WISMO) complaints', isAccessibleForFree: true },
      crumbs([['Home', '/'], ['Case studies', '/case-studies'], [s.name, `/case-studies/${slug}`]])],
    }
  }),
  {
    path: '/docs', page: 'docs', canonical: '/docs/quickstart', og: '/og/docs.png',
    title: 'Docs · Cierto', description: 'Integrate Cierto in an afternoon: quickstart, integration guides, configuration, API reference and webhooks.', jsonld: [],
  },
  ...docs.map((d): Route => {
    const info = docInfo(d.body)
    return {
      path: `/docs/${d.slug}`, page: 'docs', slug: d.slug, priority: d.slug === 'quickstart' ? .9 : .6, og: '/og/docs.png',
      title: `${info.title} · Cierto docs`, description: info.description,
      jsonld: [{ '@type': 'TechArticle', headline: info.title, description: info.description, url: `${SITE}/docs/${d.slug}`,
        dateModified: UPDATED, author: { '@id': `${SITE}/#org` }, publisher: { '@id': `${SITE}/#org` }, proficiencyLevel: 'Expert',
        encoding: { '@type': 'MediaObject', contentUrl: `${SITE}/docs/${d.slug}.md`, encodingFormat: 'text/markdown' } },
      crumbs([['Home', '/'], ['Docs', '/docs/quickstart'], [info.title, `/docs/${d.slug}`]])],
    }
  }),
  {
    path: '/privacy', page: 'privacy', priority: .3, og: '/og/privacy.png',
    title: 'Privacy · Cierto', description: 'What this site and its live demo keep, for how long, and who else sees it. No cookies, no analytics, no trackers.',
    jsonld: [page('/privacy', 'Privacy', 'What this site and its live demo keep.')],
  },
  {
    path: '/built-by', page: 'built-by', priority: .4, og: '/og/home.png',
    title: 'Built by · Cierto', description: clip(builtBy.meta.summary ?? 'How Cierto was built, end to end.'),
    jsonld: [page('/built-by', 'Built by', builtBy.meta.summary ?? '')],
  },
]

export const notFound: Route = {
  path: '/404', page: 'not-found', noindex: true, og: '/og/home.png',
  title: 'Not found · Cierto', description: 'This page does not exist.', jsonld: [],
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

export function headTags(r: Route) {
  const url = `${SITE}${r.canonical ?? r.path}`
  const img = `${SITE}${r.og}`
  const ld = r.jsonld.length ? `<script type="application/ld+json">${JSON.stringify({ '@context': 'https://schema.org', '@graph': r.jsonld }).replace(/</g, '\\u003c')}</script>` : ''
  return [
    `<title>${esc(r.title)}</title>`,
    `<meta name="description" content="${esc(r.description)}" />`,
    r.noindex ? '<meta name="robots" content="noindex" />' : `<link rel="canonical" href="${url}" />`,
    '<meta property="og:site_name" content="Cierto" />',
    `<meta property="og:type" content="${r.page === 'case-study' || (r.page === 'docs' && r.slug) ? 'article' : 'website'}" />`,
    `<meta property="og:title" content="${esc(r.title)}" />`,
    `<meta property="og:description" content="${esc(r.description)}" />`,
    `<meta property="og:url" content="${url}" />`,
    `<meta property="og:image" content="${img}" />`,
    '<meta property="og:image:width" content="1200" />',
    '<meta property="og:image:height" content="630" />',
    `<meta property="og:image:alt" content="${esc(r.title)}" />`,
    '<meta property="og:locale" content="en_IN" />',
    '<meta name="twitter:card" content="summary_large_image" />',
    `<meta name="twitter:title" content="${esc(r.title)}" />`,
    `<meta name="twitter:description" content="${esc(r.description)}" />`,
    `<meta name="twitter:image" content="${img}" />`,
    ...(r.page === 'docs' && r.slug ? [`<link rel="alternate" type="text/markdown" href="${SITE}/docs/${r.slug}.md" />`] : []),
    ...(r.page === 'case-study' ? [`<link rel="alternate" type="text/markdown" href="${SITE}${r.path}.md" />`] : []),
    ld,
  ].filter(Boolean).join('\n    ')
}

export function sitemap() {
  const urls = routes.filter((r) => !r.canonical && !r.noindex)
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map((r) => `  <url><loc>${SITE}${r.path === '/' ? '/' : r.path}</loc><lastmod>${UPDATED}</lastmod><priority>${(r.priority ?? .5).toFixed(1)}</priority></url>`).join('\n')}
</urlset>
`
}

// Search and answer engines are welcome, including AI crawlers: the point of the site is to be cited correctly.
export function robots() {
  return `# Cierto: every page is public. Search engines and AI assistants are welcome to read and cite it.
User-agent: *
Allow: /
Disallow: /v1/
Disallow: /hosts/

Sitemap: ${SITE}/sitemap.xml

# Plain-text guides for AI assistants: ${SITE}/llms.txt and ${SITE}/llms-full.txt
`
}

function studyMarkdown(slug: Slug) {
  const s = STUDIES[slug], h = brandHead(slug), b = insights.brands[slug]
  const cats = b.categories.filter((c) => c.group === 'WISMO' && (c.wismo ?? 0) > 0).sort((a, z) => (z.wismo ?? 0) - (a.wismo ?? 0))
  return `# ${s.name}: where-is-my-order complaints, mined from public reviews

${s.line}

- **Reviews analysed:** ${(h.reviews ?? 0).toLocaleString('en-IN')} (Google Play, App Store India) plus ${h.posts ?? 0} complaint-board posts, pulled ${UPDATED}.
- **WISMO share of 1–2★ reviews:** ${h.wismo_low}% (a lower bound; rule-based classifier, hand-checked holdout precision 87–93%).
- **Business shape:** ${s.kind}.

## What the reviews complain about (share of ${s.name}'s WISMO reviews)

| Cause | Share |
|---|---|
${cats.map((c) => `| ${c.name} | ${c.wismo}% |`).join('\n')}

## Takeaways

${s.takeaways.map((t) => `- ${t}`).join('\n')}

## From the review to the fix

| Cause | Today | With Cierto |
|---|---|---|
${s.plays.map((p) => `| ${p.cause} | ${p.now} | ${p.cierto} |`).join('\n')}

This is a concept study built from public reviews. Cierto is not affiliated with ${s.name} and has no access to its data.

Source page: ${SITE}/case-studies/${slug}
`
}

/** Markdown twins served next to the HTML pages: /docs/<slug>.md and /case-studies/<slug>.md. */
export function markdownTwins(): Record<string, string> {
  const out: Record<string, string> = {}
  for (const d of docs) out[`docs/${d.slug}.md`] = d.body.trim() + `\n\nSource page: ${SITE}/docs/${d.slug}\n`
  for (const slug of Object.keys(STUDIES) as Slug[]) out[`case-studies/${slug}.md`] = studyMarkdown(slug)
  return out
}

const SUMMARY = `> Cierto is an AI SDK for “where is my order?” (WISMO). It answers every order question from live courier, rider and payment data (status, ETA, delays, a stuck rider, traffic, batched orders, bad addresses, silent couriers and “delivered but not received”) and resolves problems inside a policy the business writes. It is a working proof of concept, not a hosted commercial service.`

export function llms() {
  const docLines = docs.map((d) => { const i = docInfo(d.body); return `- [${i.title}](${SITE}/docs/${d.slug}.md): ${i.description}` })
  return `# Cierto

${SUMMARY}

Key facts:

- Every answer states a cause, a new time, a latest-by time, what happens automatically if that is missed, and its sources with how old they are. If the data is stale, the answer says so.
- Money decisions (refunds, credits, cancellations, reattempts) follow a deterministic, versioned policy with a cap; above the cap a person approves. The language model only rewords answers, and a check rejects any rewording that changes a number, time or date.
- Integration takes about an afternoon: install (5 min), send events (1–2 h), show the answer (30 min). Surfaces: Web Component, React, headless JSON view, server events API, signed webhooks (Standard Webhooks). React Native, Android, iOS and Flutter are designed, not built.
- Languages: English and Hinglish.
- Research: ${REVIEWS.toLocaleString('en-IN')} public app reviews of Smytten, Swish and Zomato classified by cause; WISMO is ${H.map((h) => `${h.brand} ${h.wismo_low}%`).join(', ')} of 1–2★ reviews.
- Cierto is not affiliated with Smytten, Swish or Zomato and uses none of their data.

## Docs

${docLines.join('\n')}

## Case studies

${(Object.keys(STUDIES) as Slug[]).map((s) => `- [${STUDIES[s].name}](${SITE}/case-studies/${s}.md): ${STUDIES[s].line}`).join('\n')}

## Product

- [Home](${SITE}/): what Cierto does, the six causes it explains, the policy model and the SDK.
- [Live demo](${SITE}/demos): Cierto answering inside three concept apps on a virtual clock.

## Optional

- [Everything above in one file](${SITE}/llms-full.txt)
- [Built by](${SITE}/built-by): how and why the proof of concept was built.
- [Privacy](${SITE}/privacy)
`
}

export function llmsFull() {
  const faq = FAQ.map((f) => `### ${f.q}\n\n${f.a}`).join('\n\n')
  const twins = markdownTwins()
  return `# Cierto: full reference

${SUMMARY}

## Frequently asked questions

${faq}

${Object.keys(STUDIES).map((s) => twins[`case-studies/${s}.md`].replace(/^# /, '## ')).join('\n\n')}

${docs.map((d) => d.body.trim()).join('\n\n---\n\n')}
`
}
