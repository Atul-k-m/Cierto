# Integrate a D2C parcel app (Smytten-like)

For an Indian D2C brand shipping through couriers: trial boxes and full-size products, web and Android apps, orders that take days, and a support team that today answers "where is my order" by pasting courier status. After this guide, the order page tells the shopper what actually happened, the "delivered but not received" case resolves itself inside your policy, and your support tool gets a case with the evidence instead of a complaint.

> **What's real in this proof of concept.** Steps 1, 2, 4, 5 (web and React), 6, 7 and 8 run today against `python -m wismo serve`. Hosted connectors (step 3), the Android and iOS SDKs (step 5), WhatsApp and SMS (step 9) and live keys (step 10) are designed; their snippets are marked **planned** and show the intended API.

| Step | What | Time (est.) |
|---|---|---|
| 0 | Run the [quickstart](quickstart.md) with the test orders | 10 min |
| 1 | A session endpoint in your backend | 1 h |
| 2 | Order feed from your OMS | 0.5 to 1 day |
| 3 | Carrier feed | 1 h with a connector (planned); a day with your own adapter |
| 4 | Payments and refunds | 2 to 4 h |
| 5 | Place the components: web, React, Android | 0.5 day per platform |
| 6 | Appearance and Hinglish | 1 h |
| 7 | Policies: start strict, simulate, loosen | 1 day (ops) |
| 8 | Handoff and approvals via webhooks | 2 h |
| 9 | Proactive messages (planned) | 1 day, mostly template approval |
| 10 | Go live (planned) | — |

The examples use the Smytten test tenant's keys:

```sh
export PK=pk_test_cierto_smytten_SSP8AOvPlbWFc8pmTdHzZ8C1
export SK=sk_test_cierto_smytten_fqH6YZbp9SXrAC5QvEAllTjA
```

## 1. A session endpoint

Your backend is the only thing that holds the secret key. Add one endpoint that checks the logged-in user owns the order, then asks Cierto for a 15-minute client secret for that order and customer:

```js
// Express-style handler in your BFF
app.post('/api/cierto/session', requireLogin, async (req, res) => {
  const orderId = req.query.order
  if (!(await orders.belongsTo(orderId, req.user.id))) return res.sendStatus(404)
  const r = await fetch('http://localhost:8787/v1/customer_sessions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${process.env.CIERTO_SECRET_KEY}`, 'content-type': 'application/json',
               'Idempotency-Key': `${req.user.id}:${orderId}:${Math.floor(Date.now() / 60_000)}` },
    body: JSON.stringify({ order_id: orderId, customer_ref: req.user.id }),
  })
  res.status(r.status).json(await r.json())      // { client_secret, expires_at, … }
})
```

`customer_ref` is your own stable id; no email or phone is needed. If the order was created with a `customer_ref`, Cierto refuses a session for anyone else (`403 customer_mismatch`).

## 2. Order feed

At checkout, send the order and, above all, the delivery promise the shopper saw. Cierto holds you to the promise you showed, not the courier's internal date. Include the customer signals you already have: they decide how much the resolver can take a customer at their word.

```sh
curl http://localhost:8787/v1/orders -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -H "Idempotency-Key: checkout-SMY-2025-771203" \
  -d '{"order_id": "SMY-2025-771203", "customer_ref": "cust_88213", "amount_inr": 599, "payment": "prepaid_upi",
       "title": "Glow trial box", "items": ["Niacinamide serum 5 ml", "Green tea toner 20 ml", "Sunscreen 8 g"],
       "account_phone_last4": "2946",
       "customer": {"account_age_days": 410, "orders_90d": 6, "remedies_90d": 0},
       "eta": {"due_by": "2026-10-06T23:59:00+05:30", "shown_to_customer": "Arrives by Tue, 6 Oct"}}'
```

Send it again when the promise changes; Cierto records a revision and keeps the old promise visible, struck through. Cancellations are events:

```sh
curl http://localhost:8787/v1/events -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"event_id": "oms:SMY-2025-771203:cancelled", "order_ref": "SMY-2025-771203", "type": "order.cancelled",
       "asserted_by": "merchant", "occurred_at": "2026-09-30T11:05:00+05:30", "source_adapter": "oms",
       "data": {"by": "customer", "reason": "wrong address"}}'
```

Run your OMS job with an `Idempotency-Key` per batch and a stable `event_id` per fact, and retries are safe: a repeated event is a duplicate, and the same `event_id` with different content is rejected, not silently overwritten.

## 3. Carrier feed

Every courier scan becomes a `shipment.status` event with the courier as the asserter, the two-level status, and the courier's own words in `raw`. Proof fields are three-valued on purpose: leave `otp_verified` out when the courier said nothing, send `false` when it says no OTP was used.

```sh
curl http://localhost:8787/v1/events -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"events": [
    {"event_id": "shiprocket:1432907788:packed", "order_ref": "SMY-2025-771203", "shipment_ref": "AWB-1432907788",
     "type": "shipment.status", "status": "packed", "substatus": "packed.packed", "asserted_by": "merchant",
     "occurred_at": "2026-09-30T13:15:00+05:30", "source_adapter": "wms", "data": {"consignee_phone_last4": "7310"}},
    {"event_id": "shiprocket:1432907788:ofd", "order_ref": "SMY-2025-771203", "shipment_ref": "AWB-1432907788",
     "type": "shipment.status", "status": "out_for_delivery", "substatus": "out_for_delivery.out_for_delivery",
     "asserted_by": "carrier", "occurred_at": "2026-10-03T09:00:00+05:30", "source_adapter": "shiprocket",
     "raw": {"code": "17", "message": "Out for delivery", "carrier": "Delhivery"}, "location": {"pincode": "110092", "city": "Delhi"}},
    {"event_id": "shiprocket:1432907788:dl", "order_ref": "SMY-2025-771203", "shipment_ref": "AWB-1432907788",
     "type": "shipment.status", "status": "delivered", "substatus": "delivered.delivered", "asserted_by": "carrier",
     "occurred_at": "2026-10-03T14:02:00+05:30", "source_adapter": "shiprocket",
     "raw": {"code": "7", "message": "DELIVERED", "carrier": "Delhivery"}, "proof": {"otp_verified": false, "call_logged": false}}
  ]}'
```

That last event is the most common complaint in the data behind this product: a "delivered" with no OTP, no call, and a different phone number on the parcel (`7310`, not the account's `2946`). Cierto shows it as **"Delhivery says it was delivered"** and asks the shopper, never as a green tick.

**Addresses.** If your checkout compares the map pin with the typed address, send the result. When they are far apart, the shopper sees "Your map pin is 1.2 km from the address you typed" and a **Confirm the right spot** button (the `fix_address` action) before the courier gets lost:

```sh
curl http://localhost:8787/v1/events -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"event_id": "checkout:SMY-2025-771203:address", "order_ref": "SMY-2025-771203", "type": "address.check",
       "asserted_by": "merchant", "occurred_at": "2026-09-30T11:01:00+05:30", "source_adapter": "checkout",
       "data": {"distance_m": 1200, "confidence": 0.35, "pin_area": "Wakad", "text_area": "Hinjewadi Phase 1"}}'
```

**Planned: hosted connectors.** Paste Shiprocket, Delhivery or ClickPost credentials in the dashboard and get an unguessable inbound URL, with poll-on-silence when the carrier goes quiet. Weakly signed feeds (Shiprocket's static `x-api-key`) are treated as low-trust claims and re-fetched from the carrier before any money moves.

## 4. Payments and refunds

Send refund stages from your finance service or your gateway's webhook handler. The bank reference (UPI RRN, card ARN) is what lets a shopper, their bank or Cierto trace a refund stuck at "initiated":

```sh
curl http://localhost:8787/v1/events -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"event_id": "razorpay:rfnd_Q1:initiated", "order_ref": "SMY-2025-771203", "type": "refund.status",
       "asserted_by": "payment", "occurred_at": "2026-09-30T12:00:00+05:30", "source_adapter": "razorpay",
       "data": {"stage": "initiated", "amount_inr": 599, "reference": "RRN 535418027766", "method": "upi"}}'
```

When the credit lands, send `"stage": "credited"`. If it doesn't within your promised working days, Cierto opens the case itself and asks the gateway to trace it (`ord_test_refund_stuck` shows this).

## 5. Place the components

**Web, script tag.** On the order detail page:

```html
<div id="cierto-order"></div>
<script src="https://js.cierto.dev/v1/cierto.js"></script>
<script>
  const cierto = Cierto.init({
    publishableKey: 'pk_test_cierto_smytten_SSP8AOvPlbWFc8pmTdHzZ8C1',
    fetchClientSecret: async ({ orderId }) =>
      (await fetch(`/api/cierto/session?order=${orderId}`, { method: 'POST', credentials: 'include' })).json()
        .then((r) => r.client_secret),
    locale: 'en-IN',
  })
  cierto.order(ORDER_ID).mount('#cierto-order', { variant: 'tracking-card' })
</script>
```

In the orders list, mount one widget per card with `variant: 'orders-row'`; after delivery, `after-delivered` makes the delivery check the main content of the screen.

**React.**

```tsx
import { Cierto } from '@cierto/js'
import { CiertoProvider, CiertoOrder, useCiertoOrder } from '@cierto/js/react'

const cierto = Cierto.init({ publishableKey: 'pk_test_cierto_smytten_SSP8AOvPlbWFc8pmTdHzZ8C1', fetchClientSecret })

export function OrderPage({ orderId }: { orderId: string }) {
  return (
    <CiertoProvider cierto={cierto}>
      <CiertoOrder orderId={orderId} variant="tracking-card" onResolution={(r) => analytics.track('cierto_resolution', { decision: r.decision })} />
    </CiertoProvider>
  )
}

// Or render it yourself from the view model:
function OrderStatus({ orderId }: { orderId: string }) {
  const { view, resolution, act } = useCiertoOrder(orderId)
  if (!view) return null
  return <MyCard tone={view.tone} title={view.state} note={resolution?.shopper_message}
                 onNotReceived={() => act('report_not_received')} />
}
```

`@cierto/js` is `packages/cierto-js` in this repo (not published): `npm run build` there produces `dist/cierto.mjs`, `dist/cierto.js` (UMD) and `dist/react.mjs`.

**Android. Planned: designed, not built.** The native SDK would render the same view model in Compose, with the same session flow:

```kotlin
// build.gradle.kts (planned)
dependencies { implementation("dev.cierto:cierto-android:0.+") }   // or cierto-android-core for headless

// Application.onCreate() (planned)
Cierto.initialize(
  context = this,
  publishableKey = "pk_test_cierto_smytten_…",
  clientSecretProvider = { orderId -> backend.createCiertoSession(orderId) },   // suspend fun: String
  config = CiertoConfig(locale = Locale.forLanguageTag("hi-Latn-IN"),
                       appearance = Appearance(theme = "smytten", colors = Colors(action = 0xFFE4007C))),
)

// OrderDetailFragment, Compose (planned)
CiertoOrder(orderId = "SMY-2025-771203", variant = Variant.TrackingCard)
```

Until then, an Android app can render from the same API with the headless calls (`GET /v1/orders/{id}/view`, `POST /v1/orders/{id}/actions`), or show the web widget in a Custom Tab from the order screen. iOS (`CiertoKit`, SwiftUI) and React Native are planned the same way.

## 6. Appearance and Hinglish

Match your brand with a theme and a few variables. Set them once on the server so every surface picks them up, or per page in `Cierto.init`:

```sh
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"appearance": {"theme": "smytten", "variables": {"colorAction": "#E4007C", "colorActionStrong": "#B8006A", "radiusSurface": "12px"}}}'
```

Shoppers also type their questions. Put Cierto behind your help chat and it answers from the order's data, in the shopper's language, without inventing a date:

```sh
curl http://localhost:8787/v1/orders/ord_test_stuck_ofd/ask -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"question": "parcel kahan hai?", "locale": "hi-Latn-IN"}'
```

Hinglish (`hi-Latn-IN`) is a real locale here, not a translation afterthought: "Courier ke hisaab se deliver ho gaya", "Kya aapko parcel mila?", and the resolution's own message ("…aapka ₹599 refund apne aap ho jayega"). Operating systems never report Hinglish, so pick it from your app's language setting or from how the shopper writes to support, and pass `locale` to `Cierto.init` or `cierto.update({ locale })`.

## 7. Policies

Start strict: the resolver proposes every refund and a person approves. Then look at what it would have done, and loosen.

```sh
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"policy": {"auto_refund_cap_inr": 0, "trust_min_for_instant": 0.6, "investigate_window_hours": 24, "reattempt_first": true}}'

curl http://localhost:8787/v1/config/simulate -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"policy": {"auto_refund_cap_inr": 499}}'
```

`simulate` runs every order in the sandbox through both policies and reports what changes and how many rupees would be refunded without a human. With real traffic, run it over the last 90 days of disputes before raising the cap to ₹299 to ₹499. Smytten specifics worth encoding:

- Trial boxes are low value, so a modest cap covers most disputes.
- Credits-based pricing makes wallet credit a natural remedy (planned remedy kind).
- The wrong phone on the parcel is a known failure. With `reattempt_first`, a stuck parcel gets a reattempt with the right number before any refund.

## 8. Handoff and approvals

Webhooks tell your helpdesk what happened, with the evidence, so an agent never re-asks the shopper. Subscribe your endpoint:

```sh
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"webhook_url": "https://support.smytten.example/hooks/cierto"}'
```

- `case.opened`: create or update the ticket with the case id (`#377992`) and the 48-hour acknowledgement deadline.
- `remedy.proposed` with `needs_approval: true`: put it in the approval queue with `resolution.agent_summary` and `trust.factors`; approve with `POST /v1/remedies/{id}/approve`.
- `remedy.executed`: post the refund reference to the ticket.

Remove "delivered correctly from our end" macros. When the proof says delivered, Cierto shows the shopper the OTP time; when it doesn't, Cierto won't let the ticket close while the order is still wrong. See [webhooks.md](webhooks.md) for signatures and payloads.

## 9. Proactive messages (planned)

A WhatsApp delivery check a few minutes after an unproven "delivered" ("Delhivery says your box was delivered. Did you get it?") and delay notices before a promise is missed. These need template approval from your WhatsApp provider and DLT registration for SMS.

## 10. Go live (planned)

Live keys, an origin allowlist on the publishable key, webhook signature verification in production, idempotency keys on every ingestion job, a policy you have simulated, a tested handoff, a signed DPA (Cierto is your data processor under DPDP), CSP updated for the SDK host, and a rollout to 10% of customers by `customer_ref` hash while you watch the disputed-delivery rate and how often approvers overturn a proposal.
