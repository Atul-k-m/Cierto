import { motion, useInView, useReducedMotion } from 'motion/react'
import { useRef } from 'react'

// Charts drawn in ink and the one accent only. Bars grow once when seen.
const EASE = [0.16, 1, 0.3, 1] as const

function useSeen() {
  const ref = useRef<HTMLDivElement>(null)
  // Vertical margin only: on phones a chart's wipe starts at its left edge, inside any side margin, and would never fire.
  const seen = useInView(ref, { once: true, margin: '-60px 0px' })
  const reduce = useReducedMotion()
  return { ref, on: seen || !!reduce }
}

export function HBars({ rows, max, tone = 'acc' }: { rows: { label: string; value: number; note?: string }[]; max?: number; tone?: 'acc' | 'ink' }) {
  const { ref, on } = useSeen()
  const top = max ?? Math.max(...rows.map((r) => r.value))
  return (
    <div className="hbars" ref={ref}>
      {rows.map((r, i) => (
        <div className="hbar" key={r.label}>
          <span>{r.label}</span>
          <span className="hbar-track">
            <motion.span className={`hbar-fill ${i === 0 ? '' : tone === 'ink' ? 'ink' : 'mid'}`} initial={{ scaleX: 0 }}
              animate={{ scaleX: on ? r.value / top : 0 }} transition={{ duration: 1.2, ease: EASE, delay: i * 0.07 }} style={{ width: '100%' }} />
          </span>
          <span className="hbar-val">{r.value.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  )
}

const TONES = ['#3a2bff', '#0b0f17', '#9a93ff']

/** One row per category, one bar per brand. */
export function Grouped({ rows, series }: { rows: { label: string; values: (number | null)[] }[]; series: string[] }) {
  const { ref, on } = useSeen()
  const top = Math.max(...rows.flatMap((r) => r.values.map((v) => v ?? 0)))
  return (
    <div ref={ref}>
      <div className="legend" style={{ marginBottom: 16 }}>{series.map((s, i) => <span key={s}><i style={{ background: TONES[i] }} />{s}</span>)}</div>
      <div className="grouped">
        {rows.map((r, ri) => (
          <div className="g-row" key={r.label}>
            <span className="g-label">{r.label}</span>
            <span className="g-bars">
              {r.values.map((v, i) => (
                <span className="g-bar" key={i}>
                  <motion.i style={{ background: TONES[i] }} initial={{ scaleX: 0 }} animate={{ scaleX: on ? (v ?? 0) / top : 0 }}
                    transition={{ duration: 1.1, ease: EASE, delay: ri * 0.06 + i * 0.05 }} />
                  <em>{v == null ? '–' : `${v.toFixed(0)}%`}</em>
                </span>
              ))}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

/** Monthly share line: y-axis in percent, the peak called out in the chart itself. */
export function Trend({ points, height = 180, annotate = false }: { points: { month: string; wismo: number | null }[]; height?: number; annotate?: boolean }) {
  const { ref, on } = useSeen()
  const pts = points.filter((p) => p.wismo != null) as { month: string; wismo: number }[]
  if (pts.length < 2) return <p className="chart-foot">Not enough months with full coverage to draw a trend.</p>
  const W = 1000, H = height, L = 52, R = 24, T = 28, B = 34
  const top = Math.ceil((Math.max(...pts.map((p) => p.wismo)) * 1.15) / 10) * 10
  const x = (i: number) => L + (i * (W - L - R)) / (pts.length - 1)
  const y = (v: number) => H - B - (v / top) * (H - T - B)
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(p.wismo).toFixed(1)}`).join(' ')
  const area = `${d} L${x(pts.length - 1)} ${H - B} L${x(0)} ${H - B} Z`
  const peak = pts.reduce((m, p, i) => (p.wismo > pts[m].wismo ? i : m), 0)
  const ticks = [0, top / 2, top]
  const mono = 'JetBrains Mono Variable, monospace'
  const lbl = (m: string) => new Date(m.slice(0, 7) + '-01').toLocaleDateString('en-IN', { month: 'short', year: '2-digit' })
  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="trend" role="img" aria-label={`WISMO share of 1–2 star reviews by month, peaking at ${pts[peak].wismo}% in ${lbl(pts[peak].month)}`}>
        {ticks.map((t) => (
          <g key={t}><line x1={L} x2={W - R} y1={y(t)} y2={y(t)} stroke="rgb(11 15 23 / .1)" />
            <text x={L - 10} y={y(t) + 4} fontSize="12" fontFamily={mono} fill="#555c6a" textAnchor="end">{t}%</text></g>
        ))}
        <motion.path d={area} fill="#3a2bff" initial={{ opacity: 0 }} animate={{ opacity: on ? 0.08 : 0 }} transition={{ duration: 1.2 }} />
        <motion.path d={d} fill="none" stroke="#3a2bff" strokeWidth="3" initial={{ pathLength: 0 }} animate={{ pathLength: on ? 1 : 0 }} transition={{ duration: 1.8, ease: EASE }} />
        {pts.map((p, i) => <circle key={p.month} cx={x(i)} cy={y(p.wismo)} r={i === peak && annotate ? 6 : 3} fill={i === peak && annotate ? '#3a2bff' : '#0b0f17'} />)}
        {pts.map((p, i) => (i % Math.ceil(pts.length / 8) === 0 || i === pts.length - 1) && (
          <text key={`t${i}`} x={x(i)} y={H - 10} fontSize="12" fontFamily={mono} fill="#555c6a" textAnchor="middle">{lbl(p.month)}</text>
        ))}
        {annotate && (
          <motion.g initial={{ opacity: 0 }} animate={{ opacity: on ? 1 : 0 }} transition={{ delay: 1.4, duration: .6 }}>
            <line x1={x(peak)} x2={x(peak)} y1={y(pts[peak].wismo) - 10} y2={T - 6} stroke="#3a2bff" strokeDasharray="3 4" />
            <text x={x(peak) + (peak > pts.length / 2 ? -10 : 10)} y={T + 4} fontSize="14" fontWeight="600" fontFamily="Inter Tight Variable, sans-serif" fill="#3a2bff"
              textAnchor={peak > pts.length / 2 ? 'end' : 'start'}>{lbl(pts[peak].month)}: {pts[peak].wismo}% of 1–2★ reviews</text>
          </motion.g>
        )}
      </svg>
    </div>
  )
}
