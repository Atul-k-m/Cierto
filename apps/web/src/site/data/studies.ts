export type Slug = 'smytten' | 'swish' | 'zomato'

// What the data says for each brand, and what Cierto would change. Numbers come from insights.json.
export const STUDIES: Record<Slug, {
  name: string; kind: string; line: string; takeaways: string[]
  plays: { cause: string; now: string; cierto: string }[]; quoteCats: string[]
}> = {
  smytten: {
    name: 'Smytten', kind: 'D2C trial boxes · courier · days',
    line: 'Parcels that stop moving, deliveries nobody can prove, and a support queue that closes tickets instead of fixing orders.',
    takeaways: [
      'WISMO is a quarter of every 1–2★ review. For a courier-shipped D2C brand, the order journey is the product experience.',
      'Late and missing parcels dominate. “Not received / where is my order” is almost as common as a late delivery.',
      'When a parcel is marked delivered but never arrives, 4 in 10 of those shoppers also describe support failing them.',
      'It is episodic: in Dec 2025 and Jan 2026 WISMO jumped to about half of all 1–2★ reviews, driven by “delivered” parcels that never arrived.',
    ],
    plays: [
      { cause: 'Parcel silent for days', now: 'The tracker shows the last scan as if it were current.', cierto: 'Lane-aware stall detection, an automatic courier trace, and a dated remedy the shopper can see.' },
      { cause: 'Delivered, not received', now: 'A green tick, then a bot that repeats it.', cierto: 'Held as a claim until OTP, photo or shopper confirms; auto-refund inside the cap if the courier can’t prove it.' },
      { cause: 'Support loops', now: 'Tickets closed as “escalated”.', cierto: 'A case closes only on delivery or a refund reference; a person is one tap away with the whole timeline.' },
    ],
    quoteCats: ['Not received / where is my order', 'Marked delivered, not received', 'ETA slip / late delivery'],
  },
  swish: {
    name: 'Swish', kind: '10-minute food · Bangalore · minutes',
    line: 'When the promise is ten minutes, every stalled rider and every wrong pin is visible, and shoppers notice first.',
    takeaways: [
      'Seven in ten WISMO reviews are about lateness: the promise itself is the product.',
      'A rider stuck, or no delivery partner assigned at all, shows up in 1 in 9 WISMO reviews: the highest of the three apps.',
      'Address and location trouble is also highest here, because a 10-minute window leaves no time for a rider to search.',
    ],
    plays: [
      { cause: 'Rider stuck', now: 'A dot that stops, and no explanation.', cierto: 'Motion watch: stopped more than 4 min means an explanation; more than 10 min means offer a credit or cancellation.' },
      { cause: 'Late against the promise', now: 'A countdown that quietly resets.', cierto: 'Two numbers, now expected and latest by, with the late credit applied automatically under your policy.' },
      { cause: 'Bad address', now: 'The rider calls and the food cools.', cierto: 'Pin-versus-text check at checkout and a one-tap fix sent before dispatch.' },
    ],
    quoteCats: ['ETA slip / late delivery', 'Rider / parcel stuck, not moving', 'Address / location resolution'],
  },
  zomato: {
    name: 'Zomato', kind: 'Restaurant delivery · minutes',
    line: 'Lateness dominates, batching goes unexplained, and “delivered” without food is where support breaks down.',
    takeaways: [
      'Three in four WISMO reviews are about late orders and slipping ETAs, the highest share of the three apps.',
      'Batched and multiple orders appear in about 8% of WISMO reviews, more than at Smytten or Swish.',
      'Four in ten “delivered but not received” complaints also describe support failing.',
    ],
    plays: [
      { cause: 'Batched orders', now: 'The rider turns the other way; nobody says why.', cierto: 'Stop-sequence explainer: “one drop first, 600 m from you, then you”, with a new time.' },
      { cause: 'ETA slips', now: 'A single moving number.', cierto: 'Now expected and latest by, re-promised only on real change, with the reason named.' },
      { cause: 'Delivered, no food', now: 'The chat bot starts from zero.', cierto: 'Proof check (OTP, rider GPS at drop) first; refund or redeliver inside policy; reason-coded escalation.' },
    ],
    quoteCats: ['ETA slip / late delivery', 'Multiple / batched orders', 'Marked delivered, not received'],
  },
}
