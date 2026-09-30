import { StrictMode } from 'react'
import { createRoot, hydrateRoot } from 'react-dom/client'
import { App } from './App'
import { PAGES, match, normPath, type PageKey } from './pages'
import './site.css'

const root = document.getElementById('root')!
const path = normPath(location.pathname)
const m = root.dataset.page ? { page: root.dataset.page as PageKey, slug: root.dataset.slug } : match(path)

PAGES[m.page]().then((Page) => {
  const el = <StrictMode><App path={path}><Page slug={m.slug} /></App></StrictMode>
  if (root.hasChildNodes()) hydrateRoot(root, el)
  else createRoot(root).render(el)
})
