// Cierto browser SDK.
//
//   const cierto = Cierto.init({ publishableKey: 'pk_test_…', fetchClientSecret: async ({ orderId }) => …, locale: 'en-IN' })
//   cierto.order('ord_test_unproven').mount('#cierto', { variant: 'tracking-card' })
//   cierto.on('resolution', (r) => …)
//   const view = await cierto.headless.order('ord_…').get()
//   const answer = await cierto.headless.order('ord_…').ask('where is my order?')
//
// The browser holds only a publishable key and, per order, a 15-minute client secret minted by the
// host's server (POST /v1/customer_sessions with the secret key). The SDK asks for a new one through
// fetchClientSecret whenever the old one expires. Authority (refund caps, approvals) stays server side.
import { CiertoOrder, defineElements, type Appearance, type Variant } from '../../../apps/web/src/widget/element'
import type { ActionId, Answer, Locale, OrderEnvelope, OrderSource, OrderView, Resolution } from '../../../apps/web/src/widget/types'

export type { ActionId, Answer, Appearance, Locale, OrderView, Resolution, Variant }
export { CiertoOrder, defineElements }

export const version = '0.1.0'

export interface CiertoOptions {
  /** pk_test_… from GET /v1/dev/keys (dev) or your dashboard. Never a secret key. */
  publishableKey: string
  /** Ask your server for a client secret for this order. Your server calls POST /v1/customer_sessions. */
  fetchClientSecret: (context: { orderId: string }) => Promise<string>
  locale?: Locale
  appearance?: Appearance
  /** Where the Cierto API lives. Defaults to the origin that served cierto.js, else the page's own origin. */
  baseUrl?: string
  /** How often mounted widgets and subscriptions poll, in ms (default 3000). */
  pollIntervalMs?: number
}

export interface MountOptions { variant?: Variant; locale?: Locale; appearance?: Appearance }

export interface MountedOrder {
  element: CiertoOrder
  update(options: MountOptions): void
  unmount(): void
}

export interface ActionEvent { orderId: string; action: ActionId }
export interface ResolutionEvent { orderId: string; resolution: Resolution }
export interface ErrorEvent { orderId: string | null; code?: string; message: string }

interface EventMap {
  resolution: ResolutionEvent
  action: ActionEvent        // return false from a handler to handle the action yourself
  change: OrderView
  error: ErrorEvent
}
type Handler<K extends keyof EventMap> = (event: EventMap[K]) => unknown

export interface HeadlessOrder {
  /** The display-ready view model (state, tone, proof, clocks, actions, resolution…). */
  get(): Promise<OrderView>
  /** Take a shopper action: confirm_received | report_not_received | talk_to_person | report_missing_item | fix_address. */
  act(action: ActionId, extra?: { items?: string[]; photo?: boolean; landmark?: string }): Promise<OrderView>
  /** Ask a question in the shopper's words; the answer is composed only from the order's data. */
  ask(question: string): Promise<Answer>
  /** Poll for changes; the callback runs with each new view. Returns an unsubscribe function. */
  subscribe(callback: (view: OrderView) => void, options?: { intervalMs?: number }): () => void
}

export class CiertoError extends Error {
  constructor(readonly status: number, readonly code: string, message: string) {
    super(message)
    this.name = 'CiertoError'
  }
}

// When loaded by <script src=".../sdk/cierto.js">, talk to the server that served it.
const scriptOrigin = typeof document !== 'undefined' && document.currentScript instanceof HTMLScriptElement
  && document.currentScript.src ? new URL(document.currentScript.src).origin : ''

const SECRET_TTL_MS = 14 * 60_000   // sessions last 15 minutes; refresh a minute early

export class CiertoClient {
  readonly #opts: CiertoOptions
  readonly #base: string
  #locale: Locale
  #appearance: Appearance | undefined
  #secrets = new Map<string, { value: Promise<string>; at: number }>()
  #handlers: { [K in keyof EventMap]: Set<Handler<K>> } = { resolution: new Set(), action: new Set(), change: new Set(), error: new Set() }
  #mounted = new Set<MountedOrder & { options: MountOptions }>()
  #defaults: Promise<Appearance | null> | null = null

  constructor(options: CiertoOptions) {
    if (!options?.publishableKey?.startsWith('pk_')) {
      if (options?.publishableKey?.startsWith('sk_')) throw new Error('[cierto] never put a secret key in the browser; use your publishable key (pk_…)')
      throw new Error('[cierto] publishableKey must be a publishable key (pk_test_…)')
    }
    if (typeof options.fetchClientSecret !== 'function') {
      throw new Error('[cierto] fetchClientSecret is required: an async function that returns a client secret from your server')
    }
    this.#opts = options
    this.#base = (options.baseUrl ?? scriptOrigin).replace(/\/$/, '')
    this.#locale = options.locale ?? 'en-IN'
    this.#appearance = options.appearance
  }

  /** Subscribe to SDK events. Returns an unsubscribe function. */
  on<K extends keyof EventMap>(event: K, handler: Handler<K>): () => void {
    this.#handlers[event].add(handler)
    return () => this.#handlers[event].delete(handler)
  }

  /** Change locale or appearance for every mounted widget. */
  update(changes: { locale?: Locale; appearance?: Appearance }): void {
    if (changes.locale) this.#locale = changes.locale
    if (changes.appearance) this.#appearance = changes.appearance
    for (const m of this.#mounted) m.update(m.options)
  }

  order(orderId: string) {
    return {
      mount: (target: string | HTMLElement, options: MountOptions = {}) => this.#mount(orderId, target, options),
      ...this.headless.order(orderId),
    }
  }

  readonly headless = {
    order: (orderId: string): HeadlessOrder => ({
      get: async () => (await this.#view(orderId, this.#locale)).view!,
      act: async (action, extra) => {
        if (this.#emit('action', { orderId, action }) === false) throw new CiertoError(0, 'action_cancelled', 'an action handler returned false')
        const env = await this.#act(orderId, action, this.#locale, extra)
        this.#observe(orderId, env.view)
        return env.view!
      },
      ask: (question) => this.#request<Answer>(orderId, `/v1/orders/${encodeURIComponent(orderId)}/ask`, {
        method: 'POST', body: JSON.stringify({ question, locale: this.#locale }),
      }),
      subscribe: (callback, options = {}) => {
        let alive = true
        let last = ''
        const tick = async () => {
          try {
            const view = (await this.#view(orderId, this.#locale)).view
            const json = JSON.stringify(view)
            if (alive && view && json !== last) {
              last = json
              callback(view)
              this.#observe(orderId, view)
            }
          } catch (err) { this.#fail(orderId, err) }
        }
        tick()
        const timer = setInterval(tick, options.intervalMs ?? this.#opts.pollIntervalMs ?? 3000)
        return () => { alive = false; clearInterval(timer) }
      },
    }),
  }

  // ---- mounting ----

  #mount(orderId: string, target: string | HTMLElement, options: MountOptions): MountedOrder {
    const host = typeof target === 'string' ? document.querySelector<HTMLElement>(target) : target
    if (!host) throw new Error(`[cierto] mount target ${String(target)} not found`)
    defineElements()
    const el = document.createElement('cierto-order') as CiertoOrder
    const source: OrderSource = {
      load: (locale) => this.#view(orderId, locale),
      act: (action, locale) => this.#act(orderId, action, locale),
      intervalMs: this.#opts.pollIntervalMs ?? 3000,
    }
    const forward = (type: string, fn: (e: CustomEvent) => void) => {
      const listener = (e: Event) => fn(e as CustomEvent)
      el.addEventListener(type, listener)
      return () => el.removeEventListener(type, listener)
    }
    const offs = [
      forward('cierto:resolution', (e) => this.#emit('resolution', e.detail)),
      forward('cierto:change', (e) => this.#emit('change', e.detail)),
      forward('cierto:error', (e) => this.#emit('error', e.detail)),
      forward('cierto:action', (e) => { if (this.#emit('action', e.detail) === false) e.preventDefault() }),
    ]
    const mounted = {
      element: el,
      options,
      update: (next: MountOptions) => {
        mounted.options = { ...mounted.options, ...next }
        const o = mounted.options
        el.setAttribute('variant', o.variant ?? 'tracking-card')
        el.setAttribute('locale', o.locale ?? this.#locale)
        this.#applyAppearance(el, o.appearance)
      },
      unmount: () => {
        offs.forEach((off) => off())
        el.remove()
        this.#mounted.delete(mounted)
      },
    }
    mounted.update(options)
    el.source = source
    host.replaceChildren(el)
    this.#mounted.add(mounted)
    return mounted
  }

  /** Mount appearance over init appearance over the tenant's defaults (GET /v1/client_config). */
  #applyAppearance(el: CiertoOrder, own?: Appearance) {
    const local = { ...this.#appearance, ...own, variables: { ...this.#appearance?.variables, ...own?.variables } }
    el.appearance = { theme: local.theme ?? 'neutral', variables: local.variables }
    if (local.theme) return
    this.#defaults ??= fetch(`${this.#base}/v1/client_config`, { headers: { Authorization: `Bearer ${this.#opts.publishableKey}` } })
      .then((r) => (r.ok ? r.json() : null)).then((c) => c?.appearance ?? null).catch(() => null)
    this.#defaults.then((d) => {
      if (d) el.appearance = { theme: d.theme, variables: { ...d.variables, ...local.variables } }
    })
  }

  // ---- transport ----

  #secret(orderId: string, fresh: boolean): Promise<string> {
    const cached = this.#secrets.get(orderId)
    if (!fresh && cached && Date.now() - cached.at < SECRET_TTL_MS) return cached.value
    const value = Promise.resolve(this.#opts.fetchClientSecret({ orderId })).then((cs) => {
      if (typeof cs !== 'string' || !cs.startsWith('cs_')) throw new CiertoError(0, 'bad_client_secret', 'fetchClientSecret must resolve to a cs_… string')
      return cs
    })
    this.#secrets.set(orderId, { value, at: Date.now() })
    value.catch(() => this.#secrets.delete(orderId))
    return value
  }

  async #request<T = OrderEnvelope>(orderId: string, path: string, init: RequestInit = {}): Promise<T> {
    for (let attempt = 0; ; attempt++) {
      const cs = await this.#secret(orderId, attempt > 0)
      const res = await fetch(`${this.#base}${path}`, {
        ...init,
        headers: { Authorization: `Bearer ${this.#opts.publishableKey}`, 'Cierto-Client-Secret': cs, 'content-type': 'application/json' },
      })
      if (res.ok) return res.json()
      const body = await res.json().catch(() => null)
      const code: string = body?.error?.code ?? 'http_error'
      if (res.status === 401 && attempt === 0 && (code === 'client_secret_expired' || code === 'invalid_client_secret')) continue
      throw new CiertoError(res.status, code, body?.error?.message ?? `HTTP ${res.status}`)
    }
  }

  async #view(orderId: string, locale: Locale): Promise<OrderEnvelope> {
    const env = await this.#request(orderId, `/v1/orders/${encodeURIComponent(orderId)}/view?locale=${locale}`)
    return env
  }

  async #act(orderId: string, action: ActionId, locale: Locale, extra: { items?: string[]; photo?: boolean; landmark?: string } = {}): Promise<OrderEnvelope> {
    return this.#request(orderId, `/v1/orders/${encodeURIComponent(orderId)}/actions`, {
      method: 'POST', body: JSON.stringify({ action, locale, ...extra }),
    })
  }

  // ---- events ----

  #lastResolution = new Map<string, string>()

  /** Headless calls report resolutions and changes the same way mounted widgets do. */
  #observe(orderId: string, view: OrderView | null) {
    if (!view) return
    this.#emit('change', view)
    const json = JSON.stringify(view.resolution)
    if (view.resolution && this.#lastResolution.get(orderId) !== json) {
      this.#lastResolution.set(orderId, json)
      this.#emit('resolution', { orderId, resolution: view.resolution })
    }
  }

  #fail(orderId: string, err: unknown) {
    const e = err instanceof CiertoError ? err : null
    this.#emit('error', { orderId, code: e?.code, message: err instanceof Error ? err.message : String(err) })
  }

  #emit<K extends keyof EventMap>(event: K, payload: EventMap[K]): unknown {
    let result: unknown
    for (const handler of this.#handlers[event]) {
      try {
        if (handler(payload) === false) result = false
      } catch (err) { console.error(`[cierto] ${event} handler threw`, err) }
    }
    return result
  }
}

export function init(options: CiertoOptions): CiertoClient {
  return new CiertoClient(options)
}

/** For `<script src="/sdk/cierto.js">` the global is `Cierto`, so `Cierto.init(...)` works in both builds. */
export const Cierto = { init, version }
