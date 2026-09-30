// After `vite build` (client) and `vite build --ssr` (dist-ssr): write one real HTML file per route, a 404 page,
// sitemap.xml, robots.txt, llms.txt, llms-full.txt and markdown twins, then precompress the hashed assets.
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { brotliCompressSync, constants, gzipSync } from 'node:zlib'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const dist = join(root, 'dist'), ssr = join(root, 'dist-ssr')
const entry = readdirSync(ssr).find((f) => /^entry-server\.m?js$/.test(f))
const m = await import(pathToFileURL(join(ssr, entry)).href)
const template = readFileSync(join(dist, 'index.html'), 'utf8')

// The display face, preloaded so the headline (the LCP) never paints in a fallback; body text swaps in when ready.
const fonts = readdirSync(join(dist, 'assets')).filter((f) => /^archivo-latin-wdth-normal-.*\.woff2$/.test(f))
const preload = fonts.map((f) => `<link rel="preload" href="/assets/${f}" as="font" type="font/woff2" crossorigin />`).join('\n    ')

// Each page's chunk and everything it imports, preloaded in parallel instead of discovered one import at a time.
const manifest = JSON.parse(readFileSync(join(dist, '.vite', 'manifest.json'), 'utf8'))
const SRC = { home: 'Home', demos: 'Demos', 'case-studies': 'Pages', 'case-study': 'Pages', docs: 'Docs', privacy: 'Privacy', 'built-by': 'Pages', 'not-found': 'NotFound' }
function chunks(key, seen = new Set()) {
  const c = manifest[key]
  if (!c || seen.has(c.file)) return seen
  seen.add(c.file)
  for (const i of c.imports ?? []) chunks(i, seen)
  return seen
}
const entryFiles = chunks('index.html')
const modulepreload = (page) => [...chunks(`src/site/pages/${SRC[page]}.tsx`)].filter((f) => !entryFiles.has(f))
  .map((f) => `<link rel="modulepreload" crossorigin href="/${f}" />`).join('\n    ')

const write = (rel, body) => { const f = join(dist, rel); mkdirSync(dirname(f), { recursive: true }); writeFileSync(f, body) }
const attr = (r) => ` data-page="${r.page}"${r.slug ? ` data-slug="${r.slug}"` : ''}`

async function page(r, file) {
  const html = await m.render(r)
  const out = template
    .replace(/<title>[\s\S]*?<\/title>\s*/, '')
    .replace(/<meta name="description"[^>]*>\s*/, '')
    .replace('<!--head-->', `${preload}\n    ${m.headTags(r)}`)
    // after the stylesheet Vite puts at the end of <head>: CSS is requested first, the page's chunks right behind it
    .replace('</head>', `  ${modulepreload(r.page)}\n  </head>`)
    .replace('<div id="root"></div>', `<div id="root"${attr(r)}>${html}</div>`)
  if (out.includes('<div id="root"></div>')) throw new Error('template has no empty #root')
  write(file, out)
}

for (const r of m.routes) await page(r, r.path === '/' ? 'index.html' : `${r.path.slice(1)}/index.html`)
await page(m.notFound, '404.html')
write('sitemap.xml', m.sitemap())
write('robots.txt', m.robots())
write('llms.txt', m.llms())
write('llms-full.txt', m.llmsFull())
for (const [rel, body] of Object.entries(m.markdownTwins())) write(rel, body)

// Hashed assets never change, so compress them once here; the server picks .br or .gz by Accept-Encoding.
let n = 0
for (const f of readdirSync(join(dist, 'assets'))) {
  if (!/\.(js|css|svg|json)$/.test(f)) continue
  const p = join(dist, 'assets', f), buf = readFileSync(p)
  if (statSync(p).size < 1024) continue
  writeFileSync(p + '.br', brotliCompressSync(buf, { params: { [constants.BROTLI_PARAM_QUALITY]: 11, [constants.BROTLI_PARAM_SIZE_HINT]: buf.length } }))
  writeFileSync(p + '.gz', gzipSync(buf, { level: 9 }))
  n++
}
if (existsSync(ssr)) rmSync(ssr, { recursive: true, force: true })
rmSync(join(dist, '.vite'), { recursive: true, force: true })
console.log(`prerendered ${m.routes.length + 1} pages, ${Object.keys(m.markdownTwins()).length} markdown twins, compressed ${n} assets`)
