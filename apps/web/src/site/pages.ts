import type { ComponentType } from 'react'

// Every page is its own chunk. The server prerenders each route and marks #root with data-page (and data-slug),
// so the client loads exactly that chunk and hydrates; `match` is only the dev-server fallback.
export type PageKey = 'home' | 'demos' | 'case-studies' | 'case-study' | 'docs' | 'privacy' | 'built-by' | 'not-found'
export type PageProps = { slug?: string }

export const PAGES: Record<PageKey, () => Promise<ComponentType<PageProps>>> = {
  home: () => import('./pages/Home').then((m) => m.Home),
  demos: () => import('./pages/Demos').then((m) => m.Demos),
  'case-studies': () => import('./pages/Pages').then((m) => m.CaseStudies),
  'case-study': () => import('./pages/Pages').then((m) => m.CaseStudy as ComponentType<PageProps>),
  docs: () => import('./pages/Docs').then((m) => m.DocsPage),
  privacy: () => import('./pages/Privacy').then((m) => m.Privacy),
  'built-by': () => import('./pages/Pages').then((m) => m.BuiltBy),
  'not-found': () => import('./pages/NotFound').then((m) => m.NotFound),
}

export const STUDY_SLUGS = ['smytten', 'swish', 'zomato'] as const

export const normPath = (p: string) => p.replace(/\/+$/, '') || '/'

export function match(path: string): { page: PageKey; slug?: string } {
  const fixed: Record<string, PageKey> = { '/': 'home', '/demos': 'demos', '/case-studies': 'case-studies', '/docs': 'docs', '/privacy': 'privacy', '/built-by': 'built-by' }
  if (fixed[path]) return { page: fixed[path] }
  const [, section, slug, extra] = path.split('/')
  if (!extra && section === 'case-studies' && (STUDY_SLUGS as readonly string[]).includes(slug)) return { page: 'case-study', slug }
  if (!extra && section === 'docs' && slug) return { page: 'docs', slug }
  return { page: 'not-found' }
}
