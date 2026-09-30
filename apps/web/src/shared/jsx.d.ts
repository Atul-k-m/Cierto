import type { DetailedHTMLProps, HTMLAttributes } from 'react'

type WismoOrderProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
  session?: string
  order?: string
  variant?: 'orders-row' | 'tracking-card' | 'after-delivered'
  theme?: string
  api?: string
  locale?: 'en-IN' | 'hi-Latn-IN'
}

declare module 'react' {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace JSX {
    interface IntrinsicElements {
      'cierto-order': WismoOrderProps
      'wismo-order': WismoOrderProps
      'pakka-order': WismoOrderProps
    }
  }
}
