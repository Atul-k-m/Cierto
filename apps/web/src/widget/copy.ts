// Everything the shopper reads. Plain words, no internal jargon, calm when something is wrong,
// never blaming the customer. English (India), plus Hinglish (hi-Latn-IN) for the badges, the
// delivery check, the dispute and the resolution; other details fall back to English.
import { fmtDate, fmtDay, fmtDayTime, fmtLeft, fmtTime, fmtWhen, rupees } from './format'
import type { Locale, OrderView, Resolution } from './types'

export type BadgeTone = 'calm' | 'check' | 'alert' | 'ok'

export interface Described {
  badge: { text: string; tone: BadgeTone }
  headline: string
  detail: string | null
  question: string | null
  facts: { text: string; kind: 'absent' | 'present' | 'unknown' | 'warn'; icon: 'otp' | 'call' | 'photo' | 'phone' }[]
  clock: { text: string; urgent: boolean } | null
  history: string[]          // superseded promises, shown struck through
  reference: string | null
  holder: string | null
}

const BADGES: Record<string, [string, BadgeTone]> = {
  placed: ['Order placed', 'calm'], packed: ['Packed', 'calm'], preparing: ['Being prepared', 'calm'],
  rider_assigned: ['Rider assigned', 'calm'], on_the_way: ['On the way', 'calm'], out_for_delivery: ['Out for delivery', 'calm'],
  delivery_claimed: ['Not confirmed', 'check'], delivery_disputed: ['Issue open', 'alert'], delivered: ['Delivered', 'ok'],
  delayed: ['Running late', 'check'], attempt_failed: ['Delivery attempt failed', 'check'],
  cancelled: ['Cancelled', 'calm'], returning: ['Being returned', 'check'], refund_not_started: ['Refund not started', 'alert'],
  refund_on_its_way: ['Refund on its way', 'calm'], refund_overdue: ['Refund overdue', 'alert'], refunded: ['Refunded', 'ok'],
  payment_issue: ['Payment without order', 'alert'],
}

const BADGES_HI: Record<string, string> = {
  placed: 'Order ho gaya', packed: 'Pack ho gaya', preparing: 'Ban raha hai', rider_assigned: 'Rider mil gaya',
  on_the_way: 'Raaste mein', out_for_delivery: 'Delivery ke liye nikla', delivery_claimed: 'Confirm nahi hua',
  delivery_disputed: 'Issue khula hai', delivered: 'Deliver ho gaya', delayed: 'Late ho raha hai',
  attempt_failed: 'Delivery nahi ho payi', cancelled: 'Cancel ho gaya', returning: 'Wapas ja raha hai',
  refund_not_started: 'Refund shuru nahi hua', refund_on_its_way: 'Refund raaste mein', refund_overdue: 'Refund late hai',
  refunded: 'Refund ho gaya', payment_issue: 'Payment kata, order nahi',
}

const hi = (locale: Locale) => locale === 'hi-Latn-IN'

export const ACTION_LABELS = (v: OrderView, locale: Locale = 'en-IN'): Record<string, string> => {
  const quick = v.vertical === 'quick'
  const late = v.state === 'delayed'
  if (hi(locale)) return {
    confirm_received: quick ? 'Haan, aa gaya' : 'Haan, mil gaya',
    report_not_received: late ? 'Abhi tak nahi aaya' : quick ? 'Nahi aaya' : 'Nahi mila',
    talk_to_person: 'Kisi insaan se baat karein',
    fix_address: 'Sahi jagah confirm karein',
    copy_reference: 'Reference copy karein',
  }
  return {
    confirm_received: quick ? 'Yes, it arrived' : 'Yes, I got it',
    report_not_received: late ? 'Still not here' : quick ? "No, it didn't" : "No, I didn't",
    talk_to_person: 'Talk to a person',
    fix_address: 'Confirm the right spot',
    copy_reference: 'Copy reference',
  }
}

function courier(v: OrderView): string {
  if (v.vertical === 'quick') return v.extras.rider ?? 'Your rider'
  return v.carrier ?? 'The courier'
}

function proofFacts(v: OrderView, locale: Locale): Described['facts'] {
  const h = hi(locale)
  const f: Described['facts'] = []
  const p = v.proof
  f.push(p.otp === 'used' ? { text: h ? 'OTP use hua' : 'OTP used', kind: 'present', icon: 'otp' }
    : p.otp === 'not_used' ? { text: h ? 'OTP use nahi hua' : 'No OTP used', kind: 'absent', icon: 'otp' }
    : { text: h ? 'OTP record nahi hua' : 'OTP not recorded', kind: 'unknown', icon: 'otp' })
  if (p.call !== 'unknown') f.push(p.call === 'logged' ? { text: h ? 'Courier ne call kiya' : 'Courier called you', kind: 'present', icon: 'call' }
    : { text: h ? 'Aapko call nahi aaya' : 'No call to you', kind: 'absent', icon: 'call' })
  f.push(p.photo === 'yes' ? { text: h ? 'Darwaaze ki photo' : 'Photo at your door', kind: 'present', icon: 'photo' }
    : { text: h ? 'Photo nahi' : 'No photo', kind: 'absent', icon: 'photo' })
  if (v.phone_mismatch) f.push({ text: h ? 'Parcel par doosra phone number tha' : 'Parcel had a different phone number', kind: 'warn', icon: 'phone' })
  return f
}

const clockOf = (v: OrderView, kind: string) => v.clocks.find((c) => c.kind === kind)
const minutesBetween = (from: string, to: string) => Math.max(0, Math.round((new Date(to).getTime() - new Date(from).getTime()) / 60_000))

export function describe(v: OrderView, locale: Locale = 'en-IN'): Described {
  const h = hi(locale)
  const [badgeText, badgeTone] = BADGES[v.state] ?? ['', 'calm']
  const d: Described = {
    badge: { text: (h && BADGES_HI[v.state]) || badgeText, tone: badgeTone }, headline: '', detail: null, question: null,
    facts: [], clock: null, history: [], reference: null, holder: null,
  }
  const latest = [...v.timeline].reverse().find((t) => !t.notice)
  const holder = v.holder ? (h ? `Kisko action lena hai: ${v.holder.name}` : `Who needs to act: ${v.holder.name}`) : null

  switch (v.state) {
    case 'delivery_claimed': {
      const at = v.proof.claimed_at!
      d.headline = h ? (v.vertical === 'quick' ? `${courier(v)} ne delivered mark kiya` : `${courier(v)} ke hisaab se deliver ho gaya`)
        : v.vertical === 'quick' ? `${courier(v)} marked it delivered` : `${courier(v)} says it was delivered`
      d.detail = fmtWhen(at, v.now)
      d.question = h ? (v.vertical === 'quick' ? 'Kya aapka khaana aa gaya?' : 'Kya aapko parcel mila?')
        : v.vertical === 'quick' ? 'Did your food arrive?' : 'Did you get your parcel?'
      d.facts = proofFacts(v, locale)
      const w = clockOf(v, 'report_window')
      if (w) d.clock = v.vertical === 'quick'
        ? { text: h ? `Problem report karne ke liye ${fmtLeft(w.due_at, v.now)} bache hain` : `${fmtLeft(w.due_at, v.now)} left to report a problem`, urgent: true }
        : { text: h ? `${fmtDayTime(w.due_at)} tak problem report karein` : `Report a problem by ${fmtDayTime(w.due_at)}`, urgent: false }
      break
    }
    case 'delivery_disputed':
      d.headline = h ? 'Aapne bataya ki order nahi aaya' : "You told us it didn't arrive"
      d.detail = v.issue ? `${h ? 'Report kiya' : 'Reported'} ${fmtWhen(v.issue.opened_at, v.now).toLowerCase().replace(/\b(mon|tue|wed|thu|fri|sat|sun|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b/g, (m) => m[0].toUpperCase() + m.slice(1))} · issue ${v.issue.id}` : (h ? 'Aapki report record ho gayi hai.' : 'Your report is recorded.')
      d.facts = proofFacts(v, locale)
      d.holder = v.resolution ? null : holder
      if (v.issue && !v.resolution) d.clock = { text: h ? `Jawab ${fmtDayTime(v.issue.reply_by)} tak` : `Reply due by ${fmtDayTime(v.issue.reply_by)}`, urgent: false }
      break
    case 'delivered':
      d.headline = v.proof.verified_by === 'otp' ? (h ? 'Aapke OTP se deliver hua' : 'Delivered with your OTP')
        : v.proof.verified_by === 'customer' ? (h ? 'Aapne delivery confirm ki' : 'You confirmed delivery')
        : v.proof.verified_by === 'photo_and_geofence' ? (h ? 'Deliver hua · darwaaze ki photo' : 'Delivered · photo at your door')
        : (h ? 'Deliver ho gaya' : 'Delivered')
      d.detail = v.proof.claimed_at ? fmtWhen(v.proof.claimed_at, v.now) : null
      break
    case 'delayed': {
      const parts: string[] = []
      if (v.vertical === 'quick' && v.eta && new Date(v.now) > new Date(v.eta.due)) {
        const late = minutesBetween(v.eta.due, v.now)
        d.headline = h ? `${late} min late ho raha hai` : `Running ${late} min late`
        parts.push(h ? `${fmtTime(v.eta.due)} tak aana tha` : `Promised by ${fmtTime(v.eta.due)}`)
        if (v.last_scan) parts.push(h ? `Rider ka ${minutesBetween(v.last_scan.at, v.now)} min se koi update nahi`
          : `No rider update for ${minutesBetween(v.last_scan.at, v.now)} min`)
      } else {
        d.headline = v.eta?.shown ?? (h ? 'Late ho raha hai' : 'Running late')
        if (v.reasons.includes('tracking_stalled') && v.last_scan) parts.push(`No tracking update since ${fmtWhen(v.last_scan.at, v.now)}`)
        if (v.reasons.includes('eta_slipping') && v.eta) parts.push(`Delivery date moved ${v.eta.history.length} times`)
        if (v.reasons.includes('eta_breached') && v.eta) parts.push(`It was due ${fmtDate(v.eta.due)}`)
        if (v.reasons.includes('out_for_delivery_overdue')) parts.push('Out for delivery since yesterday')
        if (v.eta) d.history = v.eta.history.map((x) => x.shown.replace(/^Arrives by\s*/i, ''))
      }
      d.detail = parts.join(' · ') || null
      d.holder = v.resolution ? null : holder
      break
    }
    case 'refund_overdue': {
      const due = clockOf(v, 'refund_credit')
      d.headline = `${rupees(v.refund?.amount_inr)} hasn't reached your account`
      d.detail = `Refund started ${fmtDate(v.refund!.initiated_at!)}${due ? `; it was due by ${fmtDate(due.due_at)}` : ''}.`
      d.reference = v.refund?.reference ?? null
      d.holder = v.holder?.party === 'bank' ? 'Your bank can trace it with this reference:' : holder
      break
    }
    case 'refund_on_its_way': {
      const due = clockOf(v, 'refund_credit')
      d.headline = `Refund of ${rupees(v.refund?.amount_inr)} is on its way`
      d.detail = due ? `Expected by ${fmtDate(due.due_at)}` : null
      d.reference = v.refund?.reference ?? null
      break
    }
    case 'refund_not_started':
      d.headline = 'Your refund hasn\'t started'
      d.detail = 'The order was cancelled and the refund is late to begin.'
      d.holder = holder
      break
    case 'refunded':
      d.headline = `${rupees(v.refund?.credited_at ? v.refund.amount_inr : null)} refunded`
      break
    case 'cancelled':
      d.headline = 'Order cancelled'
      break
    case 'attempt_failed':
      d.headline = 'The courier couldn\'t deliver'
      d.detail = latest?.text ?? null
      d.holder = holder
      break
    case 'payment_issue':
      d.headline = 'Payment taken, but no order'
      d.detail = 'The money should come back to you automatically within 5 days.'
      break
    default:
      d.headline = v.eta?.shown ?? 'Order placed'
      d.detail = latest?.text ?? null
      if (v.state === 'on_the_way' && v.vertical === 'quick' && v.extras.rider) d.detail = `${v.extras.rider} is on the way`
  }
  // The engine's cause line says why, from the data (rider stopped, traffic, a drop first, the pin, the silent courier).
  const live = ['placed', 'packed', 'preparing', 'rider_assigned', 'on_the_way', 'out_for_delivery', 'delayed']
  const explains = ['rider_stalled', 'traffic_delay', 'batched', 'eta_revised', 'address_mismatch']
  // A late order already has its own detail line (promised time, silent tracking); keep it unless the cause says more.
  if (v.cause && live.includes(v.state) && (v.state !== 'delayed' || explains.includes(v.cause.id))) {
    const eta = v.eta
    const cap = eta && eta.latest_by !== eta.expected
      ? (h ? ` · ${fmtTime(eta.latest_by)} se late nahi` : ` · no later than ${fmtTime(eta.latest_by)}`) : ''
    d.detail = v.cause.text + (v.vertical === 'quick' && ['traffic_delay', 'batched', 'eta_revised'].includes(v.cause.id) ? cap : '')
    if (v.cause.id === 'address_mismatch') d.holder = null
  }
  return d
}

export interface DescribedResolution {
  message: string
  remedy: { title: string; detail: string | null; tone: 'ok' | 'check' | 'calm' } | null
  caseLine: string | null
  stepsLabel: string
  steps: { when: string; who: string; text: string }[]
}

/** The resolution block: what Cierto is doing about it, with the remedy, the case clocks and the audit trail. */
export function describeResolution(v: OrderView, locale: Locale = 'en-IN'): DescribedResolution | null {
  const r: Resolution | null = v.resolution
  if (!r) return null
  if (r.decision === 'none' && (v.state === 'delivered' || v.state === 'refunded')) return null
  const h = hi(locale)
  const m = r.remedy
  const amount = rupees(m.amount_inr)
  const due = m.eta ? new Date(m.eta) : null
  const done = !!due && due <= new Date(v.now) && !r.needs_approval
  let remedy: DescribedResolution['remedy'] = null
  const ref = m.reference ? `Ref ${m.reference}` : null
  switch (m.kind) {
    case 'refund':
    case 'partial_refund':
      remedy = r.needs_approval
        ? { title: h ? `${amount} refund · ${v.brand} ke approval ka intezaar` : `Refund of ${amount} · waiting for ${v.brand} to approve`, detail: null, tone: 'check' }
        : done ? { title: h ? `${amount} refund ho gaya` : `${amount} refunded`, detail: ref, tone: 'ok' }
        : due ? { title: h ? `${amount} refund scheduled` : `Refund of ${amount} scheduled`,
          detail: h ? `${fmtDayTime(m.eta!)} ko, jab tak delivery ka proof na mile` : `Goes out ${fmtDayTime(m.eta!)} unless delivery is proven`, tone: 'calm' }
        : { title: h ? `${amount} refund` : `Refund of ${amount}`, detail: ref, tone: 'calm' }
      break
    case 'reship':
      remedy = r.needs_approval
        ? { title: h ? `Replacement · ${v.brand} ke approval ka intezaar` : `Replacement · waiting for ${v.brand} to approve`, detail: null, tone: 'check' }
        : { title: h ? `Replacement ${due ? `${fmtDay(m.eta!)} tak` : ''}`.trim() : `Replacement${due ? ` by ${fmtDay(m.eta!)}` : ''}`, detail: ref, tone: done ? 'ok' : 'calm' }
      break
    case 'reattempt':
      remedy = { title: h ? `Dobara delivery ${due ? `${fmtDayTime(m.eta!)} tak` : ''}`.trim() : `Reattempt${due ? ` by ${fmtDayTime(m.eta!)}` : ''}`,
        detail: m.reference ? `Ticket ${m.reference}` : null, tone: 'calm' }
      break
    case 'refund_trace':
      remedy = { title: h ? `${amount} bank ke saath trace ho raha hai` : `Tracing ${amount} with your bank`, detail: ref, tone: 'check' }
      break
    case 'human_review':
      remedy = { title: h ? (due ? `${fmtDayTime(m.eta!)} tak ek insaan jawab dega` : 'Ek insaan jaldi jawab dega')
        : (due ? `A person replies by ${fmtDayTime(m.eta!)}` : 'A person replies soon'), detail: null, tone: 'calm' }
      break
  }
  const issue = v.issue
  const caseLine = r.case_id
    ? `Case ${r.case_id}` + (issue ? (h ? ` · jawab ${fmtDayTime(issue.reply_by)} tak · hal ${fmtDate(issue.resolve_by)} tak`
      : ` · reply by ${fmtDayTime(issue.reply_by)} · resolved by ${fmtDate(issue.resolve_by)}`) : '')
    : null
  const who: Record<string, string> = { cierto: 'Cierto', pakka: 'Cierto', courier: v.carrier ?? (v.vertical === 'quick' ? 'Rider' : 'Courier'),
    host: v.brand, bank: 'Bank', agent: h ? 'Support team' : 'Support' }
  return {
    message: r.shopper_message,
    remedy,
    caseLine,
    stepsLabel: h ? `Cierto ne kya kiya · ${r.steps.length}` : `What Cierto did · ${r.steps.length}`,
    steps: r.steps.map((s) => ({ when: fmtWhen(s.at, v.now), who: who[s.actor] ?? s.actor, text: s.text })),
  }
}

export const fmtClockLine = fmtTime
