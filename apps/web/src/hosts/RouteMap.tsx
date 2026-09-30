// Authored street map for the food-delivery replicas: irregular blocks formed by angled roads
// of different widths, a named arterial, a park and a canal. The route follows the drawn streets.
import type { ReactNode } from 'react'

type Pt = [number, number]
// Along road E, then the arterial, then road C north, then road D east to home.
const ROUTE: Pt[] = [[79, 262], [129, 200], [229, 180], [234, 80], [323, 75]]
const ORIGIN = ROUTE[0]
const HOME = ROUTE[ROUTE.length - 1]

function along(t: number): Pt {
  const segs = ROUTE.slice(1).map((p, i) => [ROUTE[i], p, Math.hypot(p[0] - ROUTE[i][0], p[1] - ROUTE[i][1])] as const)
  const total = segs.reduce((s, [, , len]) => s + len, 0)
  let d = Math.min(1, Math.max(0, t)) * total
  for (const [a, b, len] of segs) {
    if (d <= len) return [a[0] + ((b[0] - a[0]) * d) / len, a[1] + ((b[1] - a[1]) * d) / len]
    d -= len
  }
  return HOME
}

export interface MapPalette {
  ground: string; plot: string; street: string; arterial: string; park: string; water: string; route: string; label: string
}

const pct = ([x, y]: Pt) => ({ left: `${(x / 390) * 100}%`, top: `${(y / 300) * 100}%` })

export function RouteMap({ progress, palette, rider, origin, home, height = 300, arterial, area, showRider = true }: {
  progress: number; palette: MapPalette; rider: ReactNode; origin: ReactNode; home: ReactNode; height?: number
  arterial: string; area: string; showRider?: boolean
}) {
  const done = along(progress)
  const s = { stroke: palette.street, fill: 'none', strokeLinecap: 'round' as const }
  return (
    <div className="route-map" style={{ position: 'relative', height, background: palette.ground, overflow: 'hidden' }}>
      <svg viewBox="0 0 390 300" preserveAspectRatio="xMidYMid slice" width="100%" height="100%" aria-hidden="true">
        {/* plots: slightly lighter parcels give the blocks texture */}
        <path d="M150 210l62-10 6 60-60 8zM20 20l80-6 4 60-78 8zM252 196l40-5 4 34-40 6zM140 34l78-6 6 44-80 6zM330 110l52-6 8 40-56 8z" fill={palette.plot} />
        <path d="M262 196 380 182 392 302 268 302z" fill={palette.park} />
        <path d="M-6 170c56-12 86 10 128-4" stroke={palette.water} strokeWidth="7" fill="none" />
        {/* minor lanes */}
        <g {...s} strokeWidth="4">
          <path d="M-10 150 118 140M132 126 230 118M230 252 400 236M60 40 118 36M132 30 236 26M250 30 330 24M246 138 400 124M20 110 120 104M150 238 222 232M332 170 400 164M180 270 176 310" />
        </g>
        {/* local roads */}
        <g {...s} strokeWidth="9">
          <path d="M118 -10 132 310M238 -10 222 310M-10 96 400 70" />
        </g>
        <g {...s} strokeWidth="7">
          <path d="M40 310 170 150M300 310 330 0" />
        </g>
        {/* the arterial */}
        <path d="M-10 228C80 214 170 196 250 176S360 146 400 138" stroke={palette.arterial} strokeWidth="15" fill="none" strokeLinecap="round" />
        <path d="M-10 228C80 214 170 196 250 176S360 146 400 138" stroke={palette.street} strokeWidth="11" fill="none" strokeLinecap="round" />
        <text x="150" y="189" transform="rotate(-9 150 189)" fontSize="9" letterSpacing=".04em" fill={palette.label}>{arterial}</text>
        <text x="14" y="128" fontSize="10" fill={palette.label}>{area}</text>
        {/* route: planned faint, travelled solid */}
        <polyline points={ROUTE.map((p) => p.join(',')).join(' ')} fill="none" stroke={palette.route} strokeOpacity=".35" strokeWidth="5"
          strokeLinecap="round" strokeLinejoin="round" />
        <polyline points={routeUpTo(progress).map((p) => p.join(',')).join(' ')} fill="none" stroke={palette.route} strokeWidth="5"
          strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="map-pin" style={pct(ORIGIN)}>{origin}</span>
      <span className="map-pin" style={pct(HOME)}>{home}</span>
      {showRider && <span className="map-rider" style={pct(done)}>{rider}</span>}
    </div>
  )
}

function routeUpTo(t: number): Pt[] {
  const segs = ROUTE.slice(1).map((p, i) => [ROUTE[i], p, Math.hypot(p[0] - ROUTE[i][0], p[1] - ROUTE[i][1])] as const)
  const total = segs.reduce((s, [, , len]) => s + len, 0)
  let d = Math.min(1, Math.max(0, t)) * total
  const out: Pt[] = [ROUTE[0]]
  for (const [a, b, len] of segs) {
    if (d >= len) { out.push(b); d -= len; continue }
    out.push([a[0] + ((b[0] - a[0]) * d) / len, a[1] + ((b[1] - a[1]) * d) / len])
    break
  }
  return out
}
