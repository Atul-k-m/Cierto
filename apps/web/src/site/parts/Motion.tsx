import { animate, motion, useInView, useReducedMotion, type TargetAndTransition } from 'motion/react'
import { useEffect, useRef, useState } from 'react'

const EASE = [0.16, 1, 0.3, 1] as const

type Kind = 'rise' | 'wipe' | 'left' | 'right' | 'scale'
const FROM: Record<Kind, TargetAndTransition> = {
  rise: { opacity: 0.2, y: 28 },
  wipe: { clipPath: 'inset(0 100% 0 0)' },
  left: { opacity: 0.2, x: -36 },
  right: { opacity: 0.2, x: 36 },
  scale: { opacity: 0.2, scale: 0.96 },
}
const TO: Record<Kind, TargetAndTransition> = {
  rise: { opacity: 1, y: 0 },
  wipe: { clipPath: 'inset(0 0% 0 0)' },
  left: { opacity: 1, x: 0 },
  right: { opacity: 1, x: 0 },
  scale: { opacity: 1, scale: 1 },
}

/** One authored entrance per element, chosen by the section: rise, a left-to-right wipe along the grid, or a slide. */
export function Reveal({ children, delay = 0, className, kind = 'rise', as = 'div', style }: {
  children: React.ReactNode; delay?: number; className?: string; kind?: Kind; as?: 'div' | 'li' | 'section'; style?: React.CSSProperties
}) {
  const reduce = useReducedMotion()
  const Tag = motion[as]
  return (
    <Tag className={className} style={style} initial={reduce ? false : FROM[kind]} whileInView={TO[kind]} viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: kind === 'wipe' ? 1.1 : 0.9, ease: EASE, delay }}>
      {children}
    </Tag>
  )
}

/** A number that counts up the first time it is seen. */
export function CountUp({ to, decimals = 0, suffix = '' }: { to: number; decimals?: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const seen = useInView(ref, { once: true, margin: '-40px' })
  const reduce = useReducedMotion()
  const [v, setV] = useState(reduce ? to : 0)
  useEffect(() => {
    if (!seen || reduce) return
    const c = animate(0, to, { duration: 1.6, ease: EASE, onUpdate: setV })
    return () => c.stop()
  }, [seen, to, reduce])
  return <span ref={ref}><span aria-hidden="true">{v.toFixed(decimals)}{suffix}</span><span className="sr-only">{to.toFixed(decimals)}{suffix}</span></span>
}

/** A time or number that rolls from its previous value to the next one. */
export function Roll({ value, className }: { value: string; className?: string }) {
  const prev = useRef(value)
  const [shown, setShown] = useState(value)
  const reduce = useReducedMotion()
  useEffect(() => {
    const from = prev.current
    prev.current = value
    const a = /^(\d{1,2}):(\d{2})$/.exec(from), b = /^(\d{1,2}):(\d{2})$/.exec(value)
    if (reduce || !a || !b) { setShown(value); return }
    const m0 = +a[1] * 60 + +a[2], m1 = +b[1] * 60 + +b[2]
    const c = animate(m0, m1, {
      duration: 0.9, ease: EASE,
      onUpdate: (m) => { const r = Math.round(m); setShown(`${Math.floor(r / 60)}:${String(r % 60).padStart(2, '0')}`) },
    })
    return () => c.stop()
  }, [value, reduce])
  return <b className={className}>{shown}</b>
}
