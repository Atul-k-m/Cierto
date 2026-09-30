// <cierto-order>: framework-free Web Component. Two ways to feed it:
//   demo:  <cierto-order session="…" order="…" variant="orders-row|tracking-card|after-delivered" theme="smytten" locale="hi-Latn-IN">
//   SDK:   cierto.order('ord_…').mount('#el') sets `source` (publishable key + client secret) and `appearance`.
// <wismo-order> and <pakka-order> stay registered as aliases so the host demos and older pages keep working.
// It polls the order view, renders in the host's tokens, and emits (bubbling, composed):
//   cierto:change (detail: the view), cierto:resolution ({ orderId, resolution }) when Cierto's decision changes,
//   cierto:action ({ orderId, action }, cancelable: call preventDefault() to handle it yourself), cierto:error,
//   and wismo:change for older hosts.
import { Camera, Clock3, Copy, createElement, FileClock, Headset, KeyRound, Phone, PhoneOff, type IconNode } from 'lucide'
import { ACTION_LABELS, describe, describeResolution, type Described, type DescribedResolution } from './copy'
import { styles } from './styles'
import { cleanVariables, themeCss, type AppearanceVariables } from './tokens'
import type { ActionId, Locale, OrderEnvelope, OrderSource, OrderView } from './types'

const icon = (node: IconNode, size = 18) => {
  const el = createElement(node)
  el.setAttribute('width', String(size))
  el.setAttribute('height', String(size))
  el.setAttribute('stroke-width', '1.75')
  el.setAttribute('aria-hidden', 'true')
  return el.outerHTML
}
const FACT_ICONS = { otp: KeyRound, call: Phone, photo: Camera, phone: PhoneOff }
const esc = (s: string) => s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`)

export type Variant = 'orders-row' | 'tracking-card' | 'after-delivered'
export interface Appearance { theme?: string; variables?: Record<string, string> }

export class CiertoOrder extends HTMLElement {
  static observedAttributes = ['session', 'order', 'variant', 'theme', 'api', 'locale']
  #root: ShadowRoot | null = null
  #timer: number | undefined
  #json = ''
  #resolutionJson = 'null'
  #state = ''
  #view: OrderView | null = null
  #busy = false
  #copied = false
  #stepsOpen = false
  #lastError = ''
  #source: OrderSource | null = null
  #vars: AppearanceVariables = {}

  /** Set by the SDK: where the view comes from and where actions go. */
  set source(source: OrderSource | null) { this.#source = source; this.#restart() }
  get source() { return this.#source }

  /** { theme, variables }: variables override single tokens (colorAction → --w-color-action). */
  set appearance(a: Appearance | null) {
    if (a?.theme) this.setAttribute('theme', a.theme)
    this.#vars = cleanVariables(a?.variables)
    this.#render(false)
  }

  get view(): OrderView | null { return this.#view }

  connectedCallback() {
    if (!this.#root) {
      this.#root = this.attachShadow({ mode: 'open' })
      this.#root.addEventListener('click', (e) => this.#onClick(e))
      this.#root.addEventListener('toggle', (e) => {
        if ((e.target as HTMLElement).classList?.contains('steps')) this.#stepsOpen = (e.target as HTMLDetailsElement).open
      }, true)
    }
    this.#restart()
  }

  disconnectedCallback() { window.clearInterval(this.#timer) }

  attributeChangedCallback() { if (this.#root) { this.#json = ''; this.#refresh() } }

  #restart() {
    window.clearInterval(this.#timer)
    if (!this.isConnected || !this.#root) return
    this.#json = ''
    this.#refresh()
    this.#timer = window.setInterval(() => this.#refresh(), this.#source?.intervalMs ?? 1000)
  }

  get #locale(): Locale { return this.getAttribute('locale') === 'hi-Latn-IN' ? 'hi-Latn-IN' : 'en-IN' }

  get #variant(): Variant { return (this.getAttribute('variant') as Variant) ?? 'tracking-card' }

  get #demoUrl() {
    const base = this.getAttribute('api') ?? ''
    return `${base}/v1/demo/sessions/${this.getAttribute('session')}/orders/${this.getAttribute('order')}`
  }

  async #load(): Promise<OrderEnvelope | null> {
    if (this.#source) return this.#source.load(this.#locale)
    if (!this.getAttribute('session') || !this.getAttribute('order')) return null
    const res = await fetch(`${this.#demoUrl}?locale=${this.#locale}`)
    return res.ok ? res.json() : null
  }

  async #act(action: ActionId): Promise<OrderEnvelope | null> {
    if (this.#source) return this.#source.act(action, this.#locale)
    const res = await fetch(`${this.#demoUrl}/actions`, {
      method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ action, locale: this.#locale }),
    })
    return res.ok ? res.json() : null
  }

  async #refresh() {
    try {
      const env = await this.#load()
      this.#lastError = ''
      if (env) this.#accept(env)
    } catch (err) {
      // Keep the last good view; the next poll retries. Report each distinct failure once.
      const message = err instanceof Error ? err.message : String(err)
      if (message !== this.#lastError) {
        this.#lastError = message
        this.#emit('cierto:error', { orderId: this.#view?.order_ref ?? null, message })
      }
    }
  }

  #accept(env: OrderEnvelope) {
    const json = JSON.stringify(env.view)
    if (json === this.#json) return
    this.#json = json
    this.#view = env.view
    const changed = !!this.#state && env.view?.state !== this.#state
    this.#state = env.view?.state ?? ''
    this.#render(changed)
    if (!env.view) return
    this.#emit('cierto:change', env.view)
    this.#emit('wismo:change', env.view)
    const resolution = JSON.stringify(env.view.resolution ?? null)
    if (resolution !== this.#resolutionJson) {
      this.#resolutionJson = resolution
      if (env.view.resolution) this.#emit('cierto:resolution', { orderId: env.view.order_ref, resolution: env.view.resolution })
    }
  }

  #emit(type: string, detail: unknown, cancelable = false): boolean {
    return this.dispatchEvent(new CustomEvent(type, { detail, bubbles: true, composed: true, cancelable }))
  }

  async #onClick(e: Event) {
    const btn = (e.target as HTMLElement).closest<HTMLButtonElement>('button[data-action]')
    if (!btn || this.#busy) return
    const action = btn.dataset.action as ActionId
    if (action === 'copy_reference') {
      await navigator.clipboard?.writeText(btn.dataset.ref ?? this.#view?.refund?.reference ?? '').catch(() => {})
      this.#copied = true
      this.#render(false)
      window.setTimeout(() => { this.#copied = false; this.#render(false) }, 1600)
      return
    }
    if (!this.#emit('cierto:action', { orderId: this.#view?.order_ref ?? null, action }, true)) return
    this.#busy = true
    this.#render(false)
    try {
      const env = await this.#act(action)
      if (env) { this.#json = ''; this.#accept(env) }
    } catch (err) {
      this.#emit('cierto:error', { orderId: this.#view?.order_ref ?? null, message: err instanceof Error ? err.message : String(err) })
    } finally {
      this.#busy = false
      this.#render(false)
    }
  }

  #render(changed: boolean) {
    const root = this.#root
    if (!root) return
    const v = this.#view
    const theme = this.getAttribute('theme') ?? 'neutral'
    const loading = this.#locale === 'hi-Latn-IN' ? 'Order load ho raha hai…' : 'Loading order…'
    const body = v ? this.#body(v, describe(v, this.#locale), describeResolution(v, this.#locale)) : `<p class="detail">${loading}</p>`
    root.innerHTML = `<style>${themeCss(theme, this.#vars)}${styles}</style>${body}`
    if (changed) root.querySelector('.w')?.classList.add('changed')
  }

  #resolution(r: DescribedResolution): string {
    const hi = this.#locale === 'hi-Latn-IN'
    const remedy = r.remedy ? `<div class="remedy ${r.remedy.tone}"><p class="remedy-title">${esc(r.remedy.title)}</p>${
      r.remedy.detail ? `<p class="remedy-detail">${esc(r.remedy.detail)}</p>` : ''}</div>` : ''
    const caseLine = r.caseLine ? `<p class="case">${icon(FileClock, 15)}<span>${esc(r.caseLine)}</span></p>` : ''
    const steps = r.steps.length ? `<details class="steps"${this.#stepsOpen ? ' open' : ''}><summary>${esc(r.stepsLabel)}</summary><ol>${
      r.steps.map((s) => `<li><time>${esc(s.when)}</time><span class="who">${esc(s.who)}</span><span>${esc(s.text)}</span></li>`).join('')
    }</ol></details>` : ''
    return `<section class="res" aria-label="${hi ? 'Aage kya hoga' : 'What happens next'}"><p class="res-msg" aria-live="polite">${
      esc(r.message)}</p>${remedy}${caseLine}${steps}</section>`
  }

  #body(v: OrderView, d: Described, r: DescribedResolution | null): string {
    const variant = this.#variant
    const labels = ACTION_LABELS(v, this.#locale)
    const disabled = this.#busy ? ' disabled' : ''
    const mainActions = v.actions.filter((a) => a.id === 'confirm_received' || a.id === 'report_not_received' || a.id === 'fix_address')
    const withPerson = v.resolution?.decision === 'escalate_human'
    const talk = !withPerson && v.actions.some((a) => a.id === 'talk_to_person')
    const copy = v.actions.some((a) => a.id === 'copy_reference')

    const badge = `<span class="badge ${d.badge.tone}">${esc(d.badge.text)}</span>`
    const clock = d.clock ? `<p class="clock${d.clock.urgent ? ' urgent' : ''}">${icon(Clock3, 15)}<span>${esc(d.clock.text)}</span></p>` : ''
    const history = d.history.length ? `<p class="was"><span>Earlier promised:</span>${d.history.map((h) => `<s>${esc(h)}</s>`).join('')}</p>` : ''
    const facts = d.facts.length
      ? `<ul class="${variant === 'after-delivered' ? 'proof' : 'facts'}" aria-label="Proof of delivery">${d.facts.map((f) =>
        `<li class="${f.kind}">${icon(FACT_ICONS[f.icon], variant === 'after-delivered' ? 22 : 15)}<span>${esc(f.text)}</span></li>`).join('')}</ul>` : ''
    const buttons = mainActions.length
      ? `<div class="actions">${mainActions.map((a) => `<button type="button" class="btn ${a.primary ? 'primary' : 'secondary'}" data-action="${a.id}"${disabled}>${esc(labels[a.id])}</button>`).join('')}</div>` : ''
    const question = d.question ? `<p class="question">${esc(d.question)}</p>` : ''
    const holder = d.holder ? `<p class="holder">${esc(d.holder)}</p>` : ''
    const ref = d.reference ? `<div class="ref"><span>Bank reference <code>${esc(d.reference.replace(/^RRN\s*/, ''))}</code></span>${copy ? `<button type="button" class="link" data-action="copy_reference">${icon(Copy, 15)}${this.#copied ? 'Copied' : 'Copy'}</button>` : ''}</div>` : ''
    const talkBtn = talk ? `<button type="button" class="link" data-action="talk_to_person"${disabled}>${icon(Headset, 16)}${esc(labels.talk_to_person)}</button>` : ''
    const headline = `<p class="headline" aria-live="polite">${esc(d.headline)}</p>`
    const detail = d.detail ? `<p class="detail">${esc(d.detail)}</p>` : ''
    const res = r ? this.#resolution(r) : ''
    const label = `aria-label="${esc(v.brand)} order ${esc(v.order_ref)}"`

    if (variant === 'orders-row') {
      return `<div class="w row" role="group" ${label}>${badge}${headline}${detail}${history}${
        v.state === 'delivery_claimed' || v.state === 'delivery_disputed' ? facts : ''}${holder}${ref}${question}${buttons}${res}${clock}${talkBtn}</div>`
    }
    if (variant === 'after-delivered' && (v.proof.state !== 'none')) {
      const ask = d.question ? `<div class="ask">${question}${buttons}${clock}</div>` : clock
      return `<div class="w screen" role="group" ${label}>${badge}${headline}${detail}${facts}${ask}${res}${holder}${talkBtn}</div>`
    }
    return `<div class="w card" role="group" ${label}>${badge}${headline}${detail}${history}${facts}${holder}${ref}${question}${buttons}${res}${clock}${talkBtn}</div>`
  }
}

/** Register <cierto-order>, plus <wismo-order> and <pakka-order> as aliases. Safe to call more than once. */
export function defineElements(): void {
  if (!customElements.get('cierto-order')) customElements.define('cierto-order', CiertoOrder)
  if (!customElements.get('wismo-order')) customElements.define('wismo-order', class WismoOrder extends CiertoOrder {})
  if (!customElements.get('pakka-order')) customElements.define('pakka-order', class PakkaOrder extends CiertoOrder {})
}

defineElements()

export { CiertoOrder as WismoOrder }

declare global {
  interface HTMLElementTagNameMap { 'cierto-order': CiertoOrder; 'wismo-order': CiertoOrder; 'pakka-order': CiertoOrder }
}
