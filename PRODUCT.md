# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

Mobile-first. Demo host apps are presented as phone-sized web apps (in device frames on desktop); support and ops consoles are desktop web.

## Stack

- **Backend:** serverless (user preference, 2026-09-29). Provider and runtime (e.g. Python vs TypeScript functions) to be decided in the architecture step.
- **Front end:** delegated. Working choice: React + TypeScript (Vite) for the demo host apps and consoles; the shopper widget as a framework-free Web Component (Shadow DOM) so it can drop into any host app.

## Users

- **Shopper:** a customer of a D2C or delivery app whose order is late, stuck, or marked delivered but not received. Often anxious, on a phone, sometimes writing in Hinglish. Job: know the truth about the order and fix it without chasing support.
- **Support agent** at the host company: needs to see what actually happened and act (re-attempt, correct phone, claim, propose refund) without switching tools.
- **Ops lead** at the host company: needs to know when a courier, hub or lane is failing before complaint volume shows it.
- **Host app engineer** (the buyer): wants to add this in days without replacing their order system or helpdesk.
- **Site visitor (buyer):** a CX or engineering lead at a Smytten/Zomato/Swish-type company deciding whether Cierto is worth an integration sprint.
- **Evaluator audience (this proof of concept):** hiring managers judging the builder as an engineer + product owner.

## Product Purpose

Cierto is a configurable **AI WISMO SDK**: a drop-in shopper widget (web, Android, iOS, React Native) plus a server ingestion API and an AI agent that answers every "where is my order?" (late, rider stuck, batched orders, bad address, silent courier, delivered but not received) from live order, courier and rider data, and **acts within the host's policy** (credit, reattempt, refund, reship, escalate). The product is the SDK and engine. Its public face is a small, consolidated product site (home, demos, case studies with review-mining charts, docs, plus a footer-only Built by page) written for the buyer the way Stripe or Intercom write theirs, with a "Built by" page telling hiring managers it is a proof of concept.

In short: an integrable "intelligent WISMO" layer (Where Is My Order) that tells customers what actually happened to their order before they have to ask, and gives support the evidence and authority to fix it. Success in the proof of concept is measured by replaying a corpus of real public complaints: how many failures the engine flags, how early, with how few false alarms, and whether support conversations end in a real state change.

## Positioning

Tracking vendors mirror courier status; support AI answers from that same status. This product derives **delivery truth**: a courier's "Delivered" is a claim until backed by proof (OTP, photo, customer confirmation) or time without dispute. It pairs that with customer-side resolution and visible statutory clocks (48-hour acknowledgement and 30-day resolution under India's E-Commerce Rules 2020; RBI T+5 auto-reversal for failed payments), and is built for Indian D2C and quick commerce, integrable by one engineer in days.

## Operating Context

- Demonstrated inside three host-app replicas that follow the look of the real apps: **Smytten** (D2C beauty trial boxes via courier; days-long clock), **Swish** (10-minute food delivery, Bangalore; minutes), **Zomato** (restaurant food delivery; minutes to an hour). Each shows a persistent "Concept demo · not affiliated with <brand>" label; logos are recreated as styled wordmarks, not copied assets; replicas are for local or private demos only.
- Order events come from a replay engine; each demo scenario cites a real complaint ID.
- Surfaces: shopper order widget (first), support agent console, ops anomaly dashboard, WhatsApp-style message simulator.
- Channels in India: in-app first, WhatsApp as the dominant messaging channel.

## Capabilities and Constraints

- Canonical order timeline modelled on ONDC/Beckn fulfilment states plus a normalised status taxonomy that keeps the raw carrier code.
- Derived delivery state with confidence ("claimed" vs "verified" delivered).
- Proactive exception detection by rules and SLA clocks (ETA slips, stale scans, out-for-delivery too long, refund ageing, doorstep cancellation not reconciled, payment without order, phone mismatch).
- Self-serve actions gated by order state: confirm receipt, report not received, change phone/address before out-for-delivery, reschedule, report missing/wrong item with photo, request refund/replacement.
- AI support agent with order context and tools; proposes refunds and reships, a human approves. Never closes a ticket while the order is in an exception state; a human path is always one tap away.
- Every issue has a visible ID, a 48-hour acknowledgement clock and a 30-day resolution clock; breach produces a ready-to-file escalation (NCH 1915, e-Jagriti, bank/RBI CMS).
- Two modes of time: parcel (days) and quick commerce (minutes).
- Not in the proof of concept: order-time delivery-date prediction, live rider map, real WhatsApp/SMS sending, real payments, ML anomaly models, languages beyond English and Hinglish, scraping or overlaying the real apps.
- Terminology: WISMO, AWB (courier tracking number), NDR (non-delivery report), RTO (return to origin), OFD (out for delivery), POD (proof of delivery), RRN/ARN (bank refund references).

## Brand Commitments

- Product name: **Cierto** (Spanish for "certain, true"), chosen 2026-09-30. It replaces the earlier names Cierto and "Intelligent WISMO".
- Voice: plain, honest, specific. States what is known and what isn't ("the courier marked this delivered at 14:02 with no OTP"). Never blames the customer. Hinglish-capable.
- Host-app skins follow each real brand's visual identity (see Operating Context for guardrails). The widget itself must take on each host's look through theme tokens, not forks.
- The product's own platform UI (demo launcher, hosted tracking page, support console, ops dashboard) uses the "iridescent cloud edge" world, pinned by the user on 2026-09-29. Details live in `docs/01-design-brief.md` until DESIGN.md is written at build.

## Evidence on Hand

- `research/research.py`: 93 unique in-window (2025–2026) and 103 legacy public Smytten complaints with permalinks, dates and verbatim fragments.
- `data/complaints.json`: machine-readable export of the above.
- `docs/00-product-brief.md`: problem ranking, users, scope, cut list, metrics, positioning, risks.
- Absent and not to be fabricated: real order volumes or failure rates for any brand, customer testimonials, partnerships with Smytten/Swish/Zomato, audited deflection figures, real courier proof-of-delivery data.

## Product Principles

1. **Truth over status.** Show what is known and how confident it is; an unverified "Delivered" is never shown as a green tick.
2. **Tell before they ask.** Every exception reaches the customer with a reason and a next step before they have to chase.
3. **Always a way forward.** Every state offers an action, and a human is one tap away; no loops, no dead ends, no silent closures.
4. **Clocks are visible.** Deadlines, SLAs and legal rights are shown as countdowns, not buried in policy pages.
5. **Fits any host.** The host's brand, language and tone come through configuration; the engine and behaviour stay identical.

## Accessibility & Inclusion

WCAG 2.1 AA as the floor (Indian RPwD Act 2016; GIGW 3.0 uses 2.1 AA). Status never conveyed by colour alone; screen-reader announcements for new events; large touch targets for one-handed phone use; Indic-script font fallbacks; Hinglish and English copy.
