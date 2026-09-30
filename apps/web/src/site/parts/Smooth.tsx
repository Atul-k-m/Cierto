import Lenis from 'lenis'
import { useEffect } from 'react'

/** Inertial scrolling for the whole site, with in-page anchors eased the same way. Off for reduced motion. */
export function useSmoothScroll() {
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const lenis = new Lenis({ lerp: 0.11, wheelMultiplier: 0.9, smoothWheel: true })
    let raf = 0
    const loop = (t: number) => { lenis.raf(t); raf = requestAnimationFrame(loop) }
    raf = requestAnimationFrame(loop)
    const onClick = (e: MouseEvent) => {
      const a = (e.target as HTMLElement).closest('a')
      if (!a) return
      const url = new URL(a.href, location.href)
      if (url.pathname !== location.pathname || !url.hash) return
      const el = document.querySelector(url.hash)
      if (!el) return
      e.preventDefault()
      lenis.scrollTo(el as HTMLElement, { offset: -72, duration: 1.2 })
      history.replaceState(null, '', url.hash)
    }
    document.addEventListener('click', onClick)
    if (location.hash) { const el = document.querySelector(location.hash); if (el) setTimeout(() => lenis.scrollTo(el as HTMLElement, { offset: -72, immediate: true }), 50) }
    return () => { cancelAnimationFrame(raf); document.removeEventListener('click', onClick); lenis.destroy() }
  }, [])
}
