import { useEffect, useRef } from 'react'

// The one effect on the site: drifting noise, ordered-dithered into square dots of a single colour.
// Cheap by construction: a tileable noise field is computed once and sampled per frame; the canvas holds one pixel
// per dot and CSS scales it up (pixelated) with a dot mask, so a full-width field costs a few thousand lookups a frame.
const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map((v) => v / 16)
const N = 128
let FIELD: Float32Array | null = null

function field() {
  if (FIELD) return FIELD
  const P = 16
  const h = (i: number, j: number) => { const s = Math.sin(((i % P) + P) % P * 127.1 + (((j % P) + P) % P) * 311.7) * 43758.5453; return s - Math.floor(s) }
  const vn = (x: number, y: number) => {
    const i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j, u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy)
    return (h(i, j) * (1 - u) + h(i + 1, j) * u) * (1 - v) + (h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u) * v
  }
  FIELD = new Float32Array(N * N)
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    let s = 0, a = 0.5, f = P / N
    for (let o = 0; o < 4; o++) { s += a * vn(x * f, y * f); f *= 2; a *= 0.5 }
    FIELD[y * N + x] = s
  }
  return FIELD
}
function sample(F: Float32Array, x: number, y: number) {
  const i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j
  const i0 = ((i % N) + N) % N, j0 = ((j % N) + N) % N, i1 = (i0 + 1) % N, j1 = (j0 + 1) % N
  const a = F[j0 * N + i0], b = F[j0 * N + i1], c = F[j1 * N + i0], d = F[j1 * N + i1]
  return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
}

export function Mist({ color = [58, 43, 255], cell = 3, scale = 220, bias = 0, rise = 0.35, speed = 1, alpha = 1, className = 'mist' }: {
  color?: [number, number, number]; cell?: number; scale?: number; bias?: number; rise?: number; speed?: number; alpha?: number; className?: string
}) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const c = ref.current
    if (!c) return
    const ctx = c.getContext('2d')!
    const F = field()
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
    let raf = 0, visible = true, last = 0
    const t0 = performance.now()
    let cols = 0, rows = 0, img: ImageData | null = null
    const size = () => {
      const r = c.getBoundingClientRect()
      cols = Math.max(1, Math.round(r.width / cell)); rows = Math.max(1, Math.round(r.height / cell))
      c.width = cols; c.height = rows
      c.style.setProperty('--cw', `${r.width / cols}px`); c.style.setProperty('--ch', `${r.height / rows}px`)
      img = ctx.createImageData(cols, rows)
    }
    const k = N / (scale / cell) / 4 // field texels per dot
    const draw = (now: number) => {
      if (!img) return
      const t = ((now - t0) / 1000) * speed
      const d = img.data
      const ox1 = t * 1.6, oy1 = -t * 0.9, ox2 = -t * 1.1, oy2 = t * 0.7
      for (let y = 0; y < rows; y++) {
        const vy = y / rows
        for (let x = 0; x < cols; x++) {
          let f = 0.62 * sample(F, x * k + ox1, y * k * 1.25 + oy1) + 0.38 * sample(F, x * k * 1.9 + ox2 + 40, y * k * 2.2 + oy2 + 17)
          f = (f - 0.4) * 2.4 + vy * rise + bias
          const p = (y * cols + x) * 4
          if (f > BAYER[(y & 3) * 4 + (x & 3)]) {
            d[p] = color[0]; d[p + 1] = color[1]; d[p + 2] = color[2]; d[p + 3] = Math.min(1, 0.35 + f * 0.55) * alpha * 255
          } else d[p + 3] = 0
        }
      }
      ctx.putImageData(img, 0, 0)
    }
    const loop = (now: number) => {
      raf = requestAnimationFrame(loop)
      if (!visible || now - last < 80) return
      last = now
      draw(now)
    }
    size(); draw(performance.now())
    const ro = new ResizeObserver(() => { size(); draw(performance.now()) })
    ro.observe(c)
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting })
    io.observe(c)
    if (!reduce) raf = requestAnimationFrame(loop)
    return () => { cancelAnimationFrame(raf); ro.disconnect(); io.disconnect() }
  }, [cell, scale, bias, rise, speed, alpha, color[0], color[1], color[2]])
  return <canvas ref={ref} className={`dither ${className}`} aria-hidden="true" />
}
