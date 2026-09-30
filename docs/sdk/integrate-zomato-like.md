# Integrate a food delivery app, headless (Zomato-like)

For a food or quick-commerce app with its own riders, its own live map and its own design system. Apps at this scale rarely embed a vendor's UI, so Cierto goes in headless: you keep the map and the screens, and Cierto supplies the truth about the order (is "delivered" proven?), minute-level clocks, the actions that make sense right now, and a decision when something goes wrong.

> **What's real in this proof of concept.** The headless client, the React hook, the view model, minute clocks, rider pings, ETA revisions and stop sequences as events, grounded answers (`ask`), actions, the food policy and webhooks all run against `python -m wismo serve`. A high-rate location stream, incident detection, server-sent events and the native Android/iOS headless SDKs are designed; their snippets are marked **planned**.

The examples use the Zomato test tenant:

```sh
export PK=pk_test_cierto_zomato_cVzjS5YzlNCjNTdLjhK7pCJm
export SK=sk_test_cierto_zomato_2tnh2CSaHFlbg4GlueSvOtDE
curl -X POST http://localhost:8787/v1/dev/reset -H "Authorization: Bearer $SK"
```

## 1. A session per active order

Same as any integration: your backend mints a client secret for the order the shopper is watching (`POST /v1/customer_sessions` with your secret key). The 15-minute lifetime fits a food order; the SDK fetches a new secret through `fetchClientSecret` if the order runs long.

## 2. Send the order, the kitchen and the rider

Your dispatch system, not the rider's phone, sends the events. Cierto keeps who said what: the kitchen's "ready", the rider's "picked up" and the rider's "delivered" are claims, weighed against proof.

```sh
curl http://localhost:8787/v1/orders -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"order_id": "ZMT-9912", "customer_ref": "u_5521", "amount_inr": 412, "payment": "prepaid_upi",
       "title": "Burger Singh - 3 items", "items": ["Punjabi Tadka burger", "Masala fries", "Cold coffee"],
       "extras": {"restaurant": "Burger Singh", "area": "Laxmi Nagar"},
       "customer": {"account_age_days": 900, "orders_90d": 22, "remedies_90d": 0},
       "eta": {"due_by": "2026-09-30T14:05:00+05:30", "shown_to_customer": "Arriving by 2:05 pm"}}'
```

```sh
curl http://localhost:8787/v1/events -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"events": [
    {"event_id": "disp:ZMT-9912:prep", "order_ref": "ZMT-9912", "type": "shipment.status", "status": "pending",
     "substatus": "pending.preparing", "asserted_by": "rider", "occurred_at": "2026-09-30T13:26:00+05:30", "source_adapter": "dispatch"},
    {"event_id": "disp:ZMT-9912:assigned", "order_ref": "ZMT-9912", "type": "shipment.status", "status": "pending",
     "substatus": "pending.agent_assigned", "asserted_by": "rider", "occurred_at": "2026-09-30T13:34:00+05:30",
     "source_adapter": "dispatch", "data": {"rider": "Imran"}},
    {"event_id": "disp:ZMT-9912:pickup", "order_ref": "ZMT-9912", "type": "shipment.status", "status": "in_transit",
     "substatus": "in_transit.picked_up", "asserted_by": "rider", "occurred_at": "2026-09-30T13:48:00+05:30", "source_adapter": "dispatch"},
    {"event_id": "disp:ZMT-9912:delivered", "order_ref": "ZMT-9912", "type": "shipment.status", "status": "delivered",
     "substatus": "delivered.delivered", "asserted_by": "rider", "occurred_at": "2026-09-30T14:02:00+05:30",
     "source_adapter": "dispatch", "proof": {"otp_verified": true, "geo_verified": true}}
  ]}'
```

Send the OTP, GPS and photo results on `delivered`. An OTP-verified delivery is shown as delivered; one without proof is shown as "Imran marked it delivered" with a question, and a 40-minute window to answer.

### Say why it's late, from your own data

Three more events let Cierto name the cause instead of showing a dot that stops. Send them from dispatch as they happen:

```sh
curl http://localhost:8787/v1/events -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"events": [
    {"event_id": "gps:ZMT-9912:1", "order_ref": "ZMT-9912", "type": "rider.location", "asserted_by": "rider",
     "occurred_at": "2026-09-30T13:52:00+05:30", "source_adapter": "rider_app",
     "data": {"lat": 12.9226, "lng": 77.6287, "near": "Hosur Road", "distance_to_drop_m": 2900}},
    {"event_id": "eta:ZMT-9912:2", "order_ref": "ZMT-9912", "type": "eta.revised", "asserted_by": "merchant",
     "occurred_at": "2026-09-30T13:52:00+05:30", "source_adapter": "eta_service",
     "data": {"reason": "traffic", "delay_minutes": 9, "where": "Hosur Road",
              "expected_by": "2026-09-30T14:14:00+05:30", "latest_by": "2026-09-30T14:20:00+05:30"}},
    {"event_id": "disp:ZMT-9912:seq", "order_ref": "ZMT-9912", "type": "dispatch.stop_sequence", "asserted_by": "merchant",
     "occurred_at": "2026-09-30T13:52:00+05:30", "source_adapter": "dispatch",
     "data": {"stops": [{"order_ref": "ZMT-9913", "distance_to_you_m": 600}, {"order_ref": "ZMT-9912"}], "added_minutes": 4}}
  ]}'
```

- **`rider.location`** keeps tracking fresh, and when the pings keep coming from one spot for 4 minutes the `rider_stalled` check fires: "Imran has been stopped for 4 minutes near Hosur Road".
- **`eta.revised`** gives the view two numbers, `eta.expected` (now expected) and `eta.latest_by`, with the reason, and keeps the first promise in `eta.history`.
- **`dispatch.stop_sequence`** explains a batched order ("one other drop first, 600 m from you; you're next") without ever showing the other shopper's order.

`view.cause` carries the explanation in the shopper's locale, and `ask` answers with it. The `signature` demo preset has one order for each (`swish-stalled`, `zomato-traffic`, `zomato-batched`).

## 3. Keep your map; render Cierto's truth

```js
import { Cierto } from '@cierto/js'   // or <script src="https://js.cierto.dev/v1/cierto.js">

const cierto = Cierto.init({
  publishableKey: 'pk_test_cierto_zomato_cVzjS5YzlNCjNTdLjhK7pCJm',
  fetchClientSecret: async ({ orderId }) => (await api.post('/cierto/session', { orderId })).client_secret,
  locale: 'hi-Latn-IN',
})

const order = cierto.headless.order('ord_test_qc_late')
const minutesUntil = (iso, now) => Math.round((Date.parse(iso) - Date.parse(now)) / 60_000)

const stop = order.subscribe((view) => {
  // Your map stays yours. Cierto supplies the status strip under it.
  statusStrip.render({
    tone: view.tone,                                   // calm | check | attention | urgent | resolved
    state: view.state,                                 // e.g. delayed, delivery_claimed, delivery_disputed
    lateBy: view.eta ? -minutesUntil(view.eta.due, view.now) : null,
    reportWindow: view.clocks.find((c) => c.kind === 'report_window'),   // minutes left to say "not received"
    proof: view.proof,                                 // otp used? photo? claimed or verified?
    actions: view.actions.map((a) => a.id),            // what to offer right now
  })
  if (view.resolution) caseSheet.render(view.resolution)   // decision, remedy, steps, message, case id
}, { intervalMs: 5000 })

stillNotHereButton.onclick = () => order.act('report_not_received')
chatBox.onsubmit = async (text) => chat.reply((await order.ask(text)).answer)   // "order kab aayega?" → grounded answer
missingItemSheet.onsubmit = (items, hasPhoto) => order.act('report_missing_item', { items, photo: hasPhoto })
helpButton.onclick = () => order.act('talk_to_person')

cierto.on('resolution', ({ orderId, resolution }) => {
  if (resolution.decision === 'refund_now') toast(resolution.shopper_message)
})
```

Compute times from `view.now`, not the device clock: it is the server's time, and it follows the sandbox's test clock.

In React, the hook does the polling and gives you the action function:

```tsx
import { useCiertoOrder } from '@cierto/js/react'

function LiveOrderStatus({ orderId }: { orderId: string }) {
  const { view, resolution, act } = useCiertoOrder(orderId, { intervalMs: 5000 })
  if (!view) return <Skeleton />
  return (
    <>
      <HostMap orderId={orderId} />
      <StatusStrip tone={view.tone} state={view.state} eta={view.eta} clocks={view.clocks} />
      {view.actions.some((a) => a.id === 'report_not_received') && <Button onPress={() => act('report_not_received')}>Abhi tak nahi aaya</Button>}
      {resolution && <CaseSheet resolution={resolution} />}
    </>
  )
}
```

If you'd rather not build the strip, `cierto.order(id).mount(el, { variant: 'tracking-card' })` renders the same thing in your tokens under your map.

## 4. Minute clocks

Food runs on a different clock from parcels. Orders on a quick-commerce tenant (or sent with `"vertical": "quick"`) use these, all visible in `view.clocks`, `view.reasons` and the resolution's steps:

| | Quick commerce | Parcel, for comparison |
|---|---|---|
| Window to report "not received" after a "delivered" | 40 min | 48 h |
| Tracking stalled (no rider update) | 12 min | 72 h |
| Out for delivery with no outcome | 25 min | 24 h |
| Promise counts as missed after | 3 min grace | 12 h grace |
| Refund must start after a cancellation | 2 h | 48 h |

`ord_test_qc_late` shows it: a ten-minute meal 17 minutes past its promise with the rider silent since pickup. The view says `delayed` with `reasons: ["eta_breached", "tracking_stalled"]`, the widget headline reads "Running 17 min late", and the actions include `report_not_received` ("Still not here").

## 5. The food policy

```sh
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"policy": {"food_instant_refund": true, "auto_refund_cap_inr": 500, "trust_min_for_instant": 0.6}}'
curl http://localhost:8787/v1/orders/ord_test_qc_late/actions -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"action": "report_not_received"}'
```

With `food_instant_refund`, an unproven "delivered" or a badly late order is refunded at once for customers above the trust threshold and under the cap. Nobody investigates cold food for a day. A missing item refunds its share of the order (`partial_refund`); a photo raises trust. Anything over the cap, or from a customer with a history of refund claims, waits for a person (`needs_approval: true`, and a `remedy.proposed` webhook). And the resolver never refunds what the evidence contradicts: an OTP-verified, GPS-matched delivery goes to a person, with the evidence, not to money.

Check a change before making it:

```sh
curl http://localhost:8787/v1/config/simulate -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"policy": {"auto_refund_cap_inr": 150}, "customer": {"remedies_90d": 3}}'
```

## 6. Handoff

Wire your in-house support tool to the webhooks (`case.opened`, `remedy.proposed`, `remedy.executed`); see [webhooks.md](webhooks.md). When the shopper taps help, `talk_to_person` hands the agent the evidence and, where policy allows, a refund ready to approve, so the agent's first message can be the answer. If you run your own chat, return `false` from `cierto.on('action', …)` for `talk_to_person` to open it yourself.

## Planned

**A location stream.** Today rider pings are ordinary `rider.location` events through `POST /v1/events`, which is enough to detect a stopped rider. A dedicated stream (`POST /v1/rider_locations`, every few seconds, kept for 24 hours) would add facts such as "rider far from the drop when 'delivered' was tapped" and ETA drift. It would not redraw your map.

**Incidents.** Kitchen × zone and rider-fleet × zone spikes in a 30-minute window (rain, a slow kitchen) raise `incident.detected` and a proactive note on affected orders ("Baarish ki wajah se 10 min late").

**Push instead of polling.** Server-sent events with resume, for a target of under five seconds from event to screen. Today the client polls (every 3 seconds by default).

**Native headless SDKs.** Designed, not built:

```kotlin
// Android (planned)
CiertoCore.orders.observe("ZMT-9912").collect { view -> statusStrip.render(view) }   // Flow<OrderView>
CiertoCore.orders.act("ZMT-9912", Action.ReportNotReceived)
```

```swift
// iOS (planned)
for await view in CiertoCore.orders.observe("ZMT-9912") { statusStrip.render(view) }   // AsyncStream<OrderView>
```

Until they exist, native apps can call the same two endpoints (`GET /v1/orders/{id}/view`, `POST /v1/orders/{id}/actions`) with the publishable key and client secret; the view model is already display-ready.
