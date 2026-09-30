// Shape of the engine's order view (engine/src/wismo/view.py).

export type Tone = 'calm' | 'check' | 'attention' | 'urgent' | 'resolved'

export type OrderState =
  | 'placed' | 'packed' | 'preparing' | 'rider_assigned' | 'on_the_way' | 'out_for_delivery'
  | 'delivery_claimed' | 'delivery_disputed' | 'delivered'
  | 'delayed' | 'attempt_failed'
  | 'cancelled' | 'returning' | 'refund_not_started' | 'refund_on_its_way' | 'refund_overdue' | 'refunded'
  | 'payment_issue'

export interface Clock { kind: string; due_at: string; state: 'open' | 'breached' }

export type Locale = 'en-IN' | 'hi-Latn-IN'

export type CauseId =
  | 'rider_stalled' | 'traffic_delay' | 'batched' | 'eta_revised' | 'address_mismatch' | 'courier_silent' | 'phone_mismatch'
  | 'delivered_not_received' | 'late' | 'eta_slipping' | 'stuck_out_for_delivery' | 'failed_attempt'
  | 'refund_overdue' | 'refund_not_started' | 'payment_without_order'

export type ActionId = 'confirm_received' | 'report_not_received' | 'talk_to_person' | 'report_missing_item' | 'fix_address' | 'copy_reference'

/** What Cierto decided and did (engine/src/wismo/resolver.py). The view carries it once the shopper reports a problem. */
export interface Resolution {
  decision: 'investigate_and_refund' | 'refund_now' | 'reattempt' | 'reship' | 'escalate_human' | 'none'
  remedy: {
    kind: 'refund' | 'partial_refund' | 'reship' | 'reattempt' | 'refund_trace' | 'human_review' | 'none'
    amount_inr: number | null
    eta: string | null          // when it happens (or happened, once executed)
    reference: string | null
  }
  needs_approval: boolean
  steps: { at: string; actor: 'cierto' | 'courier' | 'host' | 'bank' | 'agent'; text: string }[]
  shopper_message: string
  agent_summary: string
  case_id: string | null
}

export interface OrderView {
  order_ref: string
  tenant: string
  brand: string
  vertical: 'parcel' | 'quick'
  now: string
  title: string | null
  items: string[]
  amount_inr: number | null
  placed_at: string | null
  extras: { restaurant?: string; kitchen?: string; rider?: string; area?: string }
  carrier: string | null
  state: OrderState
  tone: Tone
  reasons: string[]
  proof: {
    state: 'none' | 'claimed' | 'verified' | 'disputed'
    verified_by: string | null
    claimed_at: string | null
    otp: 'used' | 'not_used' | 'unknown'
    call: 'logged' | 'none' | 'unknown'
    photo: 'yes' | 'none' | 'unknown'
  }
  /** `due` is the committed time (the latest-by after a revision); `expected` is the current estimate. */
  eta: {
    due: string; shown: string; state: string; history: { due: string; shown: string }[]
    expected: string; latest_by: string; reason: string | null; delay_minutes: number | null
  } | null
  clocks: Clock[]
  holder: { party: string; name: string } | null
  issue: { id: string; opened_at: string; reply_by: string; resolve_by: string } | null
  refund: { stage: string; amount_inr: number | null; reference: string | null; initiated_at: string | null; credited_at: string | null } | null
  phone_mismatch: boolean
  last_scan: { at: string; where: string | null } | null
  /** Why the order is where it is, in plain words (in the requested locale), with the facts behind it. */
  cause: { id: CauseId; text: string; facts: Record<string, string | number | null> } | null
  notices: { at: string; rule: string; message: string; holder: string | null }[]
  actions: { id: ActionId; primary: boolean }[]
  timeline: { at: string; who: string; text: string; notice: boolean }[]
  resolution: Resolution | null
}

/** Demo sessions return the host's order card; the SDK API returns { id, tenant, brand }. The widget reads only `view`. */
export interface OrderEnvelope {
  order: { key: string; host?: string; variant?: string; tenant: string; order_ref?: string; brand: string; sources?: string[]; title?: string; id?: string }
  view: OrderView | null
}

/** Where a widget gets its order from: the demo API (attributes) or the SDK (a publishable key and a client secret). */
export interface OrderSource {
  load(locale: Locale): Promise<OrderEnvelope | null>
  act(action: ActionId, locale: Locale): Promise<OrderEnvelope | null>
  intervalMs?: number
}

/** POST /v1/orders/{id}/ask (and the demo equivalent): a grounded answer to a shopper's question. */
export interface Answer {
  object: 'order_answer'
  intent: 'where' | 'when' | 'late' | 'refund' | 'not_received' | 'address' | 'cancel' | 'human'
  answer: string
  cause: CauseId | null
  promise: { now: string | null; latest_by: string | null; fallback: { at: string | null; text: string } | null } | null
  sources: { name: string; age_seconds: number }[]
  stale: boolean
  actions: { id: ActionId; primary: boolean; label: string }[]
  rephrased: boolean
}
