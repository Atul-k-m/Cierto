# Quickstart: see a disputed delivery resolved in five minutes

You will run Cierto on your machine, put the `<cierto-order>` widget on a page, tap **"No, I didn't"** on an order the courier marked delivered without proof, watch Cierto decide, act and tell your server about it, and ask it "where is my order?" the way a shopper would.

> **Proof of concept.** Everything here runs locally in test mode: test keys, an in-memory sandbox per tenant, and four test orders. Live keys, hosted connectors and the native Android and iOS SDKs are designed but not built. See [What is real today](#what-is-real-today).

## 1. Run Cierto and get your test keys (1 minute)

```sh
cd engine
.venv/Scripts/python.exe -m wismo serve --build     # macOS/Linux: .venv/bin/python -m wismo serve --build
```

This builds the browser SDK and the web app, then serves everything on one port: the API at `http://localhost:8787/v1`, the SDK at `http://localhost:8787/sdk/cierto.js`. (In production the SDK would come from a CDN such as `https://js.cierto.dev/v1/cierto.js` and the API from `https://api.cierto.dev`; both are illustrative, nothing is hosted yet.)

```sh
curl http://localhost:8787/v1/dev/keys
```

Each demo tenant (`smytten`, `zomato`, `swish`) has a publishable key, a secret key and a webhook signing secret. They are derived from `CIERTO_DEV_SEED`, so unless you change it they are exactly these:

```sh
export PK=pk_test_cierto_smytten_SSP8AOvPlbWFc8pmTdHzZ8C1     # browser: identifies the tenant, can do nothing alone
export SK=sk_test_cierto_smytten_fqH6YZbp9SXrAC5QvEAllTjA     # your server only
```

The rest of this page uses `$PK` and `$SK`. Start from a clean sandbox:

```sh
curl -X POST http://localhost:8787/v1/dev/reset -H "Authorization: Bearer $SK"
```

## 2. Mint a customer session on your server (1 minute)

The browser never holds your secret key. Your server asks Cierto for a **client secret** scoped to one order and one customer; it lasts 15 minutes and the SDK asks for a new one when it expires (the Stripe `client_secret` pattern).

```sh
curl http://localhost:8787/v1/customer_sessions \
  -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"order_id": "ord_test_unproven", "customer_ref": "cus_test_4242"}'
```

```json
{"object": "customer_session", "client_secret": "cs_test_…", "order_id": "ord_test_unproven",
 "customer_ref": "cus_test_4242", "expires_at": "…", "livemode": false}
```

In your app this is one endpoint. A complete one in Node (18+), no dependencies:

```js
// server.mjs: node server.mjs, then open http://localhost:3000
import { createServer } from 'node:http'
import { readFile } from 'node:fs/promises'

const SK = 'sk_test_cierto_smytten_fqH6YZbp9SXrAC5QvEAllTjA'
createServer(async (req, res) => {
  if (req.method === 'POST' && req.url.startsWith('/my-backend/cierto-session')) {
    const orderId = new URL(req.url, 'http://x').searchParams.get('order')
    // Check here that the logged-in user owns orderId. Then:
    const r = await fetch('http://localhost:8787/v1/customer_sessions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${SK}`, 'content-type': 'application/json' },
      body: JSON.stringify({ order_id: orderId, customer_ref: 'cus_test_4242' }),
    })
    res.writeHead(r.status, { 'content-type': 'application/json' }).end(await r.text())
    return
  }
  res.writeHead(200, { 'content-type': 'text/html' }).end(await readFile('index.html'))
}).listen(3000)
```

## 3. Put the widget on a page (1 minute)

```html
<!-- index.html -->
<div id="cierto" style="max-width: 420px"></div>
<script src="http://localhost:8787/sdk/cierto.js"></script>   <!-- production (illustrative): https://js.cierto.dev/v1/cierto.js -->
<script>
  const cierto = Cierto.init({
    publishableKey: 'pk_test_cierto_smytten_SSP8AOvPlbWFc8pmTdHzZ8C1',
    fetchClientSecret: async ({ orderId }) =>
      (await fetch(`/my-backend/cierto-session?order=${orderId}`, { method: 'POST' })).json().then((r) => r.client_secret),
    locale: 'en-IN',                                   // or 'hi-Latn-IN' for Hinglish
    appearance: { theme: 'smytten' },                  // or neutral | zomato | swish, plus variables
  })
  cierto.order('ord_test_unproven').mount('#cierto', { variant: 'tracking-card' })
  cierto.on('resolution', (e) => console.log('Cierto decided', e.resolution.decision, e.resolution))
  cierto.on('action', (e) => console.log('shopper tapped', e.action))
</script>
```

The SDK talks to the server that served `cierto.js`, so the page can live on any origin. The widget shows **"Delhivery says it was delivered"** with the proof it has (no OTP, no call, no photo, a different phone number on the parcel) and asks **"Did you get your parcel?"**. A courier's "delivered" is a claim until it's proven; the widget never shows it as a green tick.

Prefer npm? `import { Cierto } from '@cierto/js'` does the same thing (`packages/cierto-js`, not published; see [the React wrapper](integrate-smytten-like.md#5-place-the-components)).

## 4. Tap "No, I didn't" (30 seconds)

The widget records the shopper's answer as a fact, and Cierto's resolver decides under Smytten's policy (auto-refund up to ₹1,000 for customers above a trust score of 0.60, with a 24-hour window for the courier to prove delivery). Without a browser, the same action from your server:

```sh
curl http://localhost:8787/v1/orders/ord_test_unproven/actions \
  -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"action": "report_not_received"}'
```

The order view now carries a `resolution`:

```json
{
  "decision": "investigate_and_refund",
  "remedy": { "kind": "refund", "amount_inr": 599, "eta": "<now + 24 h>", "reference": "CRF-036990" },
  "needs_approval": false,
  "steps": [
    { "at": "…", "actor": "cierto",   "text": "Checked delivery proof: no OTP, no photo, no call to you, courier GPS not shared" },
    { "at": "…", "actor": "cierto",   "text": "The parcel carried a different phone number (••7310) than your account (••2946), so the courier could not call you or send the OTP" },
    { "at": "…", "actor": "cierto",   "text": "Trust score 1.00 (instant remedies need 0.60): No OTP used at handover (+0.15); …" },
    { "at": "…", "actor": "courier", "text": "Asked Delhivery to re-verify the delivery (ticket DEL-RV-743735)" },
    { "at": "…", "actor": "cierto",   "text": "Refund of ₹599 scheduled for Thu 1 Oct, 2:19 am unless Delhivery proves delivery" },
    { "at": "…", "actor": "cierto",   "text": "Case #377992 opened · 48h acknowledgement clock started" }
  ],
  "shopper_message": "We couldn't find proof that your order reached you: no OTP, no photo and no call to you. We've asked Delhivery to re-check. If they can't prove delivery by Thu 1 Oct, 2:19 am, your ₹599 refund goes out automatically. You don't need to chase anyone. Case #377992.",
  "agent_summary": "Investigate and refund: refund ₹599 by … Policy: cap ₹1,000, trust ≥ 0.60 → auto-approved. Case #377992, acknowledge by ….",
  "case_id": "#377992"
}
```

Money decisions are deterministic policy code, never a model's say-so. If `ANTHROPIC_API_KEY` is set, Claude rewords `shopper_message` and `agent_summary` from the structured facts; a guard throws the rewrite away if it changes any number.

## 5. Ask it what the shopper would ask (30 seconds)

Shoppers don't tap buttons first; they type "where is my order?". `POST /v1/orders/{id}/ask` answers from the order's own data: the state, the cause, the promise and what Cierto is doing, in English or Hinglish, and it never states a time that isn't in the data.

```sh
curl http://localhost:8787/v1/orders/ord_test_unproven/ask \
  -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"question": "it says delivered but i didnt get it", "locale": "en-IN"}'
```

```jsonc
{
  "object": "order_answer",
  "intent": "not_received",
  "answer": "You told us on Wed 30 Sep, 10:13 am that it didn't arrive, though Delhivery marked it delivered. We couldn't find proof that your order reached you: no OTP, no photo and no call to you. We've asked Delhivery to re-check. If they can't prove delivery by Thu 1 Oct, 10:13 am, your ₹599 refund goes out automatically. You don't need to chase anyone. Case #377992.",
  "cause": "delivered_not_received",
  "promise": { "now": null, "latest_by": null,
               "fallback": { "at": "2026-10-01T10:13:49+05:30",
                             "text": "Your ₹599 refund goes out automatically at Thu 1 Oct, 10:13 am, unless Delhivery proves delivery." } },
  "sources": [{ "name": "Cierto case", "age_seconds": 7 }, { "name": "Your reports", "age_seconds": 7 },
              { "name": "Delhivery proof of delivery", "age_seconds": 607 }],
  "stale": false,
  "actions": [{ "id": "talk_to_person", "primary": true, "label": "Talk to a person" }],
  "rephrased": false
}
```

The answer leads with what was asked (keyword rules pick one of `where`, `when`, `late`, `refund`, `not_received`, `address`, `cancel`, `human`), and `sources` says which data it rests on and how old each is. In the browser, the same call is `cierto.headless.order(id).ask(question)`, with the publishable key and client secret. See [the API reference](api-reference.md#post-v1ordersidask).

## 6. See what your server was told, and let the clock run (1 minute)

```sh
curl "http://localhost:8787/v1/dev/webhook_log?limit=10" -H "Authorization: Bearer $SK"
```

You'll see `order.proof_changed`, `case.opened`, `remedy.proposed` and `remedy.approved` (approved by policy), each signed per [Standard Webhooks](webhooks.md). Now move the sandbox's test clock past the courier's window:

```sh
curl http://localhost:8787/v1/dev/advance -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"hours": 25}'
curl http://localhost:8787/v1/orders/ord_test_unproven/view -H "Authorization: Bearer $SK"
```

Delhivery never proved delivery, so the refund went out: the view's `refund.stage` is `initiated`, the resolution gained "Refunded ₹599 to your original payment method" and "Your bank shows it by …" steps, and the webhook log has `remedy.executed`.

## Test orders

Like Stripe's test cards, these exist in every tenant's sandbox, re-based so each is at its interesting moment when the sandbox starts (or after `POST /v1/dev/reset`). All belong to `customer_ref: "cus_test_4242"`, a long-standing customer with no refunds in 90 days.

| Order | What it is | `report_not_received` under each tenant's default policy |
|---|---|---|
| `ord_test_unproven` | Marked delivered 10 min ago (2 min for food) with no OTP and no photo. Smytten's parcel also had the wrong phone on it. | Smytten: `investigate_and_refund` (24 h window). Zomato, Swish: `refund_now` (food). |
| `ord_test_stuck_ofd` | A parcel out for delivery for 26 hours with no attempt reported; wrong phone on the parcel. | Smytten: `reattempt` (reattempt first, with the right phone), then a refund if it misses. Zomato, Swish: `investigate_and_refund`. |
| `ord_test_refund_stuck` | Cancelled; a ₹674 refund initiated 12 days ago with a bank reference, never credited. | `escalate_human` with a `refund_trace` remedy carrying the RRN. |
| `ord_test_qc_late` | A ten-minute meal 17 minutes past its promise; the rider silent since pickup. | Zomato, Swish: `refund_now`. Smytten (no food policy): `escalate_human`. |

Try the approval loop: lower the cap, report again on a fresh sandbox, and approve.

```sh
export ZSK=sk_test_cierto_zomato_2tnh2CSaHFlbg4GlueSvOtDE
curl -X POST http://localhost:8787/v1/dev/reset -H "Authorization: Bearer $ZSK"
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $ZSK" \
  -H "content-type: application/json" -d '{"policy": {"auto_refund_cap_inr": 300}}'
curl http://localhost:8787/v1/orders/ord_test_unproven/actions -H "Authorization: Bearer $ZSK" \
  -H "content-type: application/json" -d '{"action": "report_not_received"}'
#   → "needs_approval": true, and a remedy.proposed webhook for rem_49035abe088603
curl -X POST http://localhost:8787/v1/remedies/rem_49035abe088603/approve -H "Authorization: Bearer $ZSK" \
  -H "content-type: application/json" -d '{"approved_by": "ops@zomato.example"}'
#   → "status": "executed"; remedy.approved and remedy.executed webhooks
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $ZSK" \
  -H "content-type: application/json" -d '{"policy": {"auto_refund_cap_inr": 500}}'
```

## What is real today

| Built and running | Designed, not built |
|---|---|
| Order-truth engine, detectors, SLA clocks, virtual test clock | Live keys (`pk_live_cierto_…`), restricted keys (`rk_…`), key rotation |
| AI resolver: trust score, policy gate, remedies, steps, English and Hinglish messages, optional Claude rephrasing | Hosted connectors (Shiprocket, Delhivery, Razorpay, Freshdesk…) |
| SDK API: sessions, events, orders, views, actions, grounded answers (`ask`), config, simulate, remedies, webhooks log | Webhook retries and delivery dashboards (one attempt today) |
| Causes from the data: rider stopped, traffic, batched drop, address pin mismatch, silent courier, unproven delivery | Live rider-location streaming and incident detection (pings arrive as events today) |
| `<cierto-order>` web component, `Cierto.init`, headless client, React wrapper | Native Android, iOS, React Native and Flutter SDKs |
| Test orders and a test clock per tenant | Persistence: sandboxes are in memory and reset on restart |

Next: [integrate a D2C parcel app](integrate-smytten-like.md), [go headless for food delivery](integrate-zomato-like.md), the [API reference](api-reference.md), [configuration](config-reference.md) and [webhooks](webhooks.md).
