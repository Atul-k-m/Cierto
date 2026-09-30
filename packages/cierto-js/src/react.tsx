// React wrapper over the <cierto-order> element and the headless client.
//
//   const cierto = Cierto.init({ publishableKey, fetchClientSecret })
//   <CiertoProvider cierto={cierto}>
//     <CiertoOrder orderId="ord_test_unproven" variant="tracking-card" />
//   </CiertoProvider>
//
// Only types come from the SDK here, so this bundle stays tiny and React stays external.
import { createContext, useContext, useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react'
import type { ActionId, Appearance, CiertoClient, Locale, OrderView, Resolution, Variant } from './index'

const CiertoContext = createContext<CiertoClient | null>(null)

export function CiertoProvider({ cierto, children }: { cierto: CiertoClient; children?: ReactNode }) {
  return <CiertoContext.Provider value={cierto}>{children}</CiertoContext.Provider>
}

export function useCierto(explicit?: CiertoClient | null): CiertoClient {
  const fromContext = useContext(CiertoContext)
  const cierto = explicit ?? fromContext
  if (!cierto) throw new Error('[cierto] wrap your tree in <CiertoProvider cierto={Cierto.init(...)}> or pass cierto={...}')
  return cierto
}

export interface CiertoOrderProps {
  orderId: string
  variant?: Variant
  locale?: Locale
  appearance?: Appearance
  cierto?: CiertoClient
  onResolution?: (resolution: Resolution) => void
  className?: string
  style?: CSSProperties
}

/** The drop-in widget for one order. Remounts when the order or variant changes; updates locale and appearance in place. */
export function CiertoOrder({ orderId, variant = 'tracking-card', locale, appearance, cierto, onResolution, className, style }: CiertoOrderProps) {
  const client = useCierto(cierto)
  const ref = useRef<HTMLDivElement>(null)
  const mounted = useRef<ReturnType<ReturnType<CiertoClient['order']>['mount']> | null>(null)
  const onResolutionRef = useRef(onResolution)
  onResolutionRef.current = onResolution

  useEffect(() => {
    if (!ref.current) return
    const m = client.order(orderId).mount(ref.current, { variant, locale, appearance })
    mounted.current = m
    const off = client.on('resolution', (e) => { if (e.orderId === orderId) onResolutionRef.current?.(e.resolution) })
    return () => { off(); m.unmount(); mounted.current = null }
    // appearance and locale are applied by the effect below without remounting
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, orderId, variant])

  const appearanceKey = JSON.stringify(appearance ?? null)
  useEffect(() => { mounted.current?.update({ locale, appearance }) }, [locale, appearanceKey])   // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={ref} className={className} style={style} />
}

/** Headless: the order's view model, kept fresh by polling, plus an action function. Render it in your own design system. */
export function useCiertoOrder(orderId: string, options: { cierto?: CiertoClient; intervalMs?: number } = {}) {
  const client = useCierto(options.cierto)
  const [view, setView] = useState<OrderView | null>(null)
  const [error, setError] = useState<Error | null>(null)
  useEffect(() => {
    setView(null)
    const off = client.on('error', (e) => { if (e.orderId === orderId) setError(new Error(e.message)) })
    const unsubscribe = client.headless.order(orderId).subscribe((v) => { setView(v); setError(null) }, { intervalMs: options.intervalMs })
    return () => { off(); unsubscribe() }
  }, [client, orderId, options.intervalMs])
  const act = async (action: ActionId, extra?: { items?: string[]; photo?: boolean; landmark?: string }) => {
    const next = await client.headless.order(orderId).act(action, extra)
    setView(next)
    return next
  }
  const ask = (question: string) => client.headless.order(orderId).ask(question)
  return { view, resolution: view?.resolution ?? null, error, act, ask }
}
