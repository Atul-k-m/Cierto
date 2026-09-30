import { StrictMode } from 'react'
import { renderToString } from 'react-dom/server'
import { App } from './App'
import { PAGES } from './pages'
import type { Route } from './meta'

// Build-time only: render one route to HTML for scripts/prerender.mjs.
export async function render(r: Route) {
  const Page = await PAGES[r.page]()
  return renderToString(<StrictMode><App path={r.path}><Page slug={r.slug} /></App></StrictMode>)
}

export { routes, notFound, headTags, sitemap, robots, llms, llmsFull, markdownTwins } from './meta'
