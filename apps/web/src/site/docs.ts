import { parse } from './content'

// The SDK docs (docs/sdk/*.md), bundled with the docs page only.
const sdk = import.meta.glob('../../../../docs/sdk/*.md', { query: '?raw', import: 'default', eager: true }) as Record<string, string>

export const DOC_ORDER = ['quickstart', 'integrate-smytten-like', 'integrate-zomato-like', 'config-reference', 'api-reference', 'webhooks']
export const docs = Object.entries(sdk).map(([p, raw]) => parse(p, raw))
  .sort((a, b) => (DOC_ORDER.indexOf(a.slug) + 1 || 99) - (DOC_ORDER.indexOf(b.slug) + 1 || 99))
