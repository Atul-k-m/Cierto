# API reference

Base URL (local): `http://localhost:8787`; in production it would be `https://api.cierto.dev` (illustrative, not hosted). Every example below runs as written against a local server started with `python -m wismo serve`, using the dev keys. Set them once:

```sh
export PK=pk_test_cierto_smytten_SSP8AOvPlbWFc8pmTdHzZ8C1
export SK=sk_test_cierto_smytten_fqH6YZbp9SXrAC5QvEAllTjA
export WHSEC='whsec_n+FvzK0kfaweD3lsK5xTNRcgUGbQzdfh'
curl -X POST http://localhost:8787/v1/dev/reset -H "Authorization: Bearer $SK"
```

> **Proof of concept.** Test mode only. Each tenant's data lives in an in-memory sandbox that resets when the server restarts. The API shape follows Stripe's conventions, so the live version would add keys and persistence, not change the calls.

## Conventions

**Keys.** Send `Authorization: Bearer <key>`.

| Prefix | Where it lives | What it can do |
|---|---|---|
| `pk_test_cierto_…` | Browser and app | Identify the tenant. With a client secret, read one order's view and take shopper actions on it. Read `GET /v1/client_config`. |
| `sk_test_cierto_…` | Your server | Everything below. Never ship it to a browser; `Cierto.init` refuses one. |
| `cs_test_…` | Browser, from your server | A 15-minute customer session for one order, sent as `Cierto-Client-Secret: cs_test_…` (or `?client_secret=`). The pre-rename header `Pakka-Client-Secret` is still accepted. |
| `whsec_…` | Your server | Verifies webhooks Cierto sends; signs events you send, optionally. |

**Errors** are JSON with an HTTP status:

```json
{"error": {"type": "invalid_request_error", "code": "order_not_found", "message": "No order 'nope' for Smytten. …"}}
```

| Status | `type` | Common `code`s |
|---|---|---|
| 400 | `invalid_request_error` | `invalid_json`, `invalid_parameters`, `invalid_action`, `invalid_policy`, `invalid_appearance`, `batch_too_large`, `idempotency_key_invalid` |
| 401 | `authentication_error` | `missing_api_key`, `invalid_api_key`, `client_secret_required`, `invalid_client_secret`, `client_secret_expired`, `signature_invalid` |
| 403 | `permission_error` | `secret_key_required`, `client_secret_wrong_order`, `customer_mismatch` |
| 404 | `invalid_request_error` | `order_not_found`, `remedy_not_found`, `not_found` (dev endpoints outside dev mode) |
| 409 | `idempotency_error`, `invalid_request_error` | `idempotency_key_reused`, `remedy_not_approvable` |

Keys carry the vendor prefix (`pk_test_cierto_…`, `sk_test_cierto_…`) so a leaked key is recognisable, and scannable, as a Cierto key; the tenant name follows.

**Idempotency.** `POST /v1/customer_sessions`, `/v1/events`, `/v1/orders` and `/v1/remedies/{id}/approve` accept an `Idempotency-Key` header (1-255 characters). The first successful response is stored and replayed for the same key with `Idempotent-Replayed: true`; the same key with a different body is a `409`. Separately, every event is deduplicated by `event_id`.

**Times** are ISO 8601 with an offset. Amounts are rupees (`amount_inr`), not paise.

---

## Customer sessions

### `POST /v1/customer_sessions`

Secret key. Mints a client secret for one order and one customer. If the order records a customer ref, `customer_ref` must match it.

| Field | Type | |
|---|---|---|
| `order_id` | string | required |
| `customer_ref` | string | required; your stable customer id |

```sh
curl http://localhost:8787/v1/customer_sessions \
  -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -H "Idempotency-Key: session-demo-1" \
  -d '{"order_id": "ord_test_unproven", "customer_ref": "cus_test_4242"}'
```

```json
{"object": "customer_session", "client_secret": "cs_test_5ZFp…", "order_id": "ord_test_unproven",
 "customer_ref": "cus_test_4242", "expires_at": "2026-09-30T…Z", "livemode": false}
```

---

## Orders

### `GET /v1/orders/{id}/view`

Secret key, or publishable key plus client secret. Query: `locale=en-IN|hi-Latn-IN` (the resolution's `shopper_message` comes in that locale).

```sh
CS=$(curl -s http://localhost:8787/v1/customer_sessions -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"order_id": "ord_test_unproven", "customer_ref": "cus_test_4242"}' \
  | python -c "import json,sys; print(json.load(sys.stdin)['client_secret'])")
curl "http://localhost:8787/v1/orders/ord_test_unproven/view?locale=en-IN" \
  -H "Authorization: Bearer $PK" -H "Cierto-Client-Secret: $CS"
```

The response is the same view model the demo hosts use, in an envelope:

```jsonc
{
  "object": "order_view",
  "order": { "id": "ord_test_unproven", "key": "ord_test_unproven", "tenant": "smytten", "brand": "Smytten", "livemode": false },
  "view": {
    "order_ref": "ord_test_unproven", "brand": "Smytten", "vertical": "parcel", "now": "…",
    "state": "delivery_claimed",       // placed|packed|preparing|rider_assigned|on_the_way|out_for_delivery|delayed|attempt_failed|
                                       // delivery_claimed|delivery_disputed|delivered|cancelled|returning|
                                       // refund_not_started|refund_on_its_way|refund_overdue|refunded|payment_issue
    "tone": "check",                   // calm|check|attention|urgent|resolved
    "reasons": ["phone_mismatch", "suspicious_delivery"],
    "cause": { "id": "delivered_not_received",   // why, in plain words, from the data (see below)
               "text": "Delhivery marked it delivered on Wed 30 Sep, 10:07 am, with no OTP and no photo",
               "facts": { "claimed_at": "…", "otp": false, "photo": false } },
    "proof": { "state": "claimed", "verified_by": null, "claimed_at": "…", "otp": "not_used", "call": "none", "photo": "none" },
    "eta": { "due": "…", "shown": "Arrives by Sat, 3 Oct", "state": "met", "history": [],
             "expected": "…", "latest_by": "…", "reason": null, "delay_minutes": null },
    "clocks": [{ "kind": "report_window", "due_at": "…", "state": "open" }],
    "holder": { "party": "carrier", "name": "Delhivery" },
    "issue": null,                     // { id, opened_at, reply_by, resolve_by } once a case is open
    "refund": null,
    "actions": [{ "id": "confirm_received", "primary": true }, { "id": "report_not_received", "primary": false }],
    "timeline": [{ "at": "…", "who": "carrier", "text": "Delhivery marked it delivered", "notice": false }],
    "resolution": null                 // see below
    // …also title, items, amount_inr, placed_at, extras, carrier, phone_mismatch, last_scan {at, where}, notices
  }
}
```

**`eta`**: `due` and `latest_by` are the committed time (after an `eta.revised`, the latest-by); `expected` is the current estimate; `reason` and `delay_minutes` come from the revision; `history` keeps every superseded promise.

**`cause`** is the one reason that best explains the order right now, or `null`. `text` comes in the requested locale; `facts` holds the numbers and times behind it. Every cause is computed from events; none is typed in by hand.

| `cause.id` | From | Example `text` |
|---|---|---|
| `rider_stalled` | `rider.location` pings from one spot for 4 min (quick) or 20 min (parcel) | "Anubhav has been stopped for 4 minutes near Agara junction" |
| `traffic_delay`, `eta_revised` | the latest `eta.revised` and its `reason` | "Traffic on Hosur Road added 9 minutes; Rahul is 1.3 km away" |
| `batched` | `dispatch.stop_sequence` with drops before this order | "Suresh is dropping one other order first, 600 m from you; you're next" |
| `address_mismatch` | `address.check` over 150 m (quick) or 500 m (parcel), or confidence under 0.5 | "Your map pin is 1.2 km from the address you typed (pin in Wakad, address in Hinjewadi Phase 1)…" |
| `courier_silent` | the `tracking_stalled` detector, with the last scan's place | "Delhivery hasn't scanned your parcel since Sun 21 Dec, 10:40 am, at the Bhiwandi hub" |
| `delivered_not_received` | an unproven or disputed delivery claim | "Imran marked it delivered at 2:02 pm, with no OTP and no photo" |
| `stuck_out_for_delivery`, `failed_attempt`, `phone_mismatch`, `eta_slipping`, `late` | the detectors of the same names | "Out for delivery since Tue 29 Sep, 8:09 am, with no attempt reported…" |
| `refund_overdue`, `refund_not_started`, `payment_without_order` | the money detectors | "Your ₹674 refund started Fri 18 Sep but hasn't reached your account" |

**`resolution`** is `null` until the shopper acts, then exactly:

```ts
resolution: null | {
  decision: 'investigate_and_refund' | 'refund_now' | 'reattempt' | 'reship' | 'escalate_human' | 'none'
  remedy: { kind: 'refund' | 'partial_refund' | 'reship' | 'reattempt' | 'refund_trace' | 'human_review' | 'none',
            amount_inr: number | null, eta: string | null, reference: string | null }
  needs_approval: boolean
  steps: { at: string, actor: 'cierto' | 'courier' | 'host' | 'bank' | 'agent', text: string }[]
  shopper_message: string     // in the requested locale
  agent_summary: string       // for the support console
  case_id: string | null      // "#377992"
}
```

`remedy.eta` is when the remedy happens; once executed, it is when it happened. `needs_approval` turns false when the host approves.

### `POST /v1/orders/{id}/actions`

Secret key, or publishable key plus client secret. Records the shopper's action as a fact, runs the resolver under the tenant's policy, and returns the updated view. Repeating the action behind the current resolution changes nothing.

| Field | Type | |
|---|---|---|
| `action` | string | `report_not_received`, `confirm_received`, `talk_to_person`, `report_missing_item`, `fix_address` |
| `locale` | string | `en-IN` (default) or `hi-Latn-IN` |
| `items` | string[] | for `report_missing_item` |
| `photo` | boolean | for `report_missing_item`: a photo was attached (raises trust) |
| `landmark` | string | for `fix_address`: passed to the courier with the confirmed spot |

`fix_address` ("Confirm the right spot") is offered, as the primary action, while an `address.check` flags the map pin; it records an `address.confirmed` fact, and the flag clears.

```sh
curl http://localhost:8787/v1/orders/ord_test_unproven/actions \
  -H "Authorization: Bearer $PK" -H "Cierto-Client-Secret: $CS" -H "content-type: application/json" \
  -d '{"action": "report_not_received", "locale": "hi-Latn-IN"}'
```

### `POST /v1/orders/{id}/ask`

Secret key, or publishable key plus client secret. Answers a shopper's question about the order in their words. The answer is composed only from the order's view and projection by deterministic templates (English and Hinglish): it covers the state, the ETA and its revisions, the cause, who holds the problem, the proof, the case and its clocks, the refund and the resolution, and it never states a date or time that isn't in the data. Where there is no new time, it says so.

| Field | Type | |
|---|---|---|
| `question` | string | required, 1-500 characters |
| `locale` | string | `en-IN` (default) or `hi-Latn-IN` |

```sh
curl http://localhost:8787/v1/orders/ord_test_qc_late/ask \
  -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"question": "khana kab aayega?", "locale": "hi-Latn-IN"}'
```

```jsonc
{
  "object": "order_answer",
  "intent": "when",                 // where | when | late | refund | not_received | address | cancel | human
  "answer": "Yeh 17 min late hai: ise 10:00 am tak aana tha, aur abhi nayi time nahi mili. Anubhav ka 22 min se koi update nahi. Ise theek karna delivery team ke haath mein hai. Agar ab bhi nahi aaya, toh 'Abhi tak nahi aaya' dabayein; Cierto Smytten ki policy ke hisaab se kadam uthayega.",
  "cause": "courier_silent",         // the view's cause.id, or null
  "promise": {                       // null when there is nothing to promise (delivered, refunded…)
    "now": null,                     // the current estimate, if there is one and it is still ahead
    "latest_by": "2026-09-30T10:00:19+05:30",   // the committed time (a refund's credit date for refunds)
    "fallback": null                 // {at, text}: what Cierto does automatically if it's missed, only when scheduled
  },
  "sources": [{ "name": "The rider app", "age_seconds": 1322 }, { "name": "Smytten delivery estimate", "age_seconds": 1742 }],
  "stale": true,                     // the newest tracking data is older than the vertical allows (5 min quick, 24 h parcel)
  "actions": [{ "id": "talk_to_person", "primary": true, "label": "Kisi insaan se baat karein" },
              { "id": "report_not_received", "primary": false, "label": "Abhi tak nahi aaya" }],
  "rephrased": false                 // true when Claude reworded the answer and the guard accepted it
}
```

**How it answers.** Keyword rules (English and Hinglish) pick the intent, so the answer leads with what was asked: "kab aayega" leads with the time, "refund" with the money, "cant find my house" with the address. Then it adds the cause, the promise and what is being done, each only when there is data for it. When the newest tracking data is older than 5 minutes for quick commerce or 24 hours for parcels, `stale` is `true` and the answer says how old it is.

**Optional rewording.** If the server has `ANTHROPIC_API_KEY` set, Claude (`claude-sonnet-5-5`) may reword the answer from the same facts. The rewrite is discarded, and the template kept, if it adds, drops or changes any number, time, weekday, month or relative day ("today", "kal").

### `POST /v1/orders`

Secret key. Creates or updates an order from a snapshot (Narvar-style) and returns `201` when created, `200` when it already existed. Cierto turns it into `order.placed` and `eta.promised` events; resending identical content adds nothing.

| Field | Type | |
|---|---|---|
| `order_id` | string | required; letters, digits, `_ . : -` |
| `amount_inr` | number | required |
| `customer_ref` | string | links sessions to this customer |
| `customer` | object | trust signals: `account_age_days`, `orders_90d`, `remedies_90d` |
| `payment` | string | `prepaid_upi` (default), `prepaid_card`, `cod`… |
| `items`, `title` | string[], string | shown to the shopper |
| `placed_at` | datetime | default now |
| `vertical` | `parcel` \| `quick` | overrides the tenant's vertical for this order |
| `account_phone_last4` | string | 4 digits; compared with the parcel's phone |
| `eta` | `{ due_by, shown_to_customer? }` | the promise shown at checkout; later changes become revisions |
| `extras` | object | `restaurant`, `kitchen`, `rider`, `area` |

```sh
curl http://localhost:8787/v1/orders -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -H "Idempotency-Key: order-SMY-1001" \
  -d '{"order_id": "SMY-1001", "customer_ref": "cus_88213", "amount_inr": 499, "payment": "prepaid_upi",
       "items": ["Glow trial box - 3 minis"], "title": "Glow trial box", "account_phone_last4": "4471",
       "customer": {"account_age_days": 610, "orders_90d": 4, "remedies_90d": 0},
       "eta": {"due_by": "2026-10-06T23:59:00+05:30"}}'
```

### `GET /v1/orders`

Secret key. Every order in the sandbox with its state, proof and current decision.

```sh
curl http://localhost:8787/v1/orders -H "Authorization: Bearer $SK"
```

### `GET /v1/orders/{id}/events`

Secret key. The audit log: every fact with who asserted it (`merchant`, `carrier`, `rider`, `payment`, `customer`), and every engine finding, resolution, approval and execution (`engine`, or `merchant` for approvals).

```sh
curl http://localhost:8787/v1/orders/ord_test_unproven/events -H "Authorization: Bearer $SK"
```

---

## Events

### `POST /v1/events`

Secret key. Ingests canonical events: one event, or `{"events": [...]}` with up to 100. Returns `202` with per-event results; one bad event doesn't sink the batch. `tenant_id` comes from the key and can be omitted.

| Field | | |
|---|---|---|
| `event_id` | required | dedupe key; the same id with different content is rejected as `event_conflict` |
| `order_ref` | required | |
| `type` | required | `order.placed`, `order.confirmed`, `order.cancelled`, `shipment.status`, `eta.promised`, `eta.revised`, `rider.location`, `dispatch.stop_sequence`, `address.check`, `address.confirmed`, `payment.captured`, `payment.failed`, `refund.status`, `customer.contacted`, `customer.receipt_confirmed`, `customer.receipt_disputed` |
| `status`, `substatus` | for `shipment.status` | two-level taxonomy, e.g. `delivered` / `delivered.delivered`, `out_for_delivery` / `out_for_delivery.out_for_delivery`, `failed_attempt` / `failed_attempt.customer_unreachable` |
| `occurred_at` | required | when it happened, not when you send it; out-of-order is fine |
| `asserted_by` | required | `merchant`, `carrier`, `rider`, `payment`, `customer`. Cierto weighs claims by who made them. |
| `source_adapter` | required | e.g. `shiprocket`, `oms` |
| `raw` | | the source's own words: `code`, `message`, `carrier` |
| `proof` | | `otp_verified`, `photo_url`, `geo_verified`, `call_logged` (null = not said; false = didn't happen) |
| `location` | | `pincode`, `city` |
| `data` | | type-specific: `amount_inr`, `due_by`, `stage` (`initiated`/`processed`/`credited`), `reference`, `consignee_phone_last4`… (below for the newer types) |

The event types that explain a delay:

| `type` | `data` | Cierto turns it into |
|---|---|---|
| `eta.revised` | `expected_by` (required, with offset), `latest_by`, `reason` (`traffic`, `weather`, `batched`, `kitchen`, …), `delay_minutes`, `where`, `shown_to_customer` | `eta.expected` and `eta.latest_by`; cause `traffic_delay` or `eta_revised`. The earlier promise stays in `eta.history`. |
| `rider.location` | `lat`, `lng` (required), `near` (a place name), `distance_to_drop_m` | fresh tracking; `rider_stalled` when pings come from one spot (within 40 m) for 4 min (quick) or 20 min (parcel) |
| `dispatch.stop_sequence` | `stops`: `[{order_ref, distance_to_you_m}, …]`, one of them this order; `added_minutes` | cause `batched`: "one other drop first, 600 m from you". Other orders' refs are never shown to the shopper. |
| `address.check` | `distance_m` (required: map pin to the typed address), `confidence` (0-1), `pin_area`, `text_area`, `fix_by` | the `address_mismatch` check and the `fix_address` action |
| `address.confirmed` | `landmark` | clears the mismatch (the `fix_address` action writes it for you) |

Engine and remedy events (`engine.*`, `remedy.*`, `asserted_by: engine`) are Cierto's own and are rejected.

```sh
curl http://localhost:8787/v1/events -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -H "Idempotency-Key: batch-2026-09-30-001" \
  -d '{"events": [
    {"event_id": "shiprocket:AWB778:1", "order_ref": "SMY-1001", "type": "shipment.status",
     "status": "in_transit", "substatus": "in_transit.picked_up", "asserted_by": "carrier",
     "occurred_at": "2026-09-30T09:10:00+05:30", "source_adapter": "shiprocket",
     "raw": {"code": "6", "message": "Shipment picked up", "carrier": "Delhivery"},
     "data": {"consignee_phone_last4": "4471"}},
    {"event_id": "shiprocket:AWB778:1", "order_ref": "SMY-1001", "type": "shipment.status",
     "status": "in_transit", "substatus": "in_transit.picked_up", "asserted_by": "carrier",
     "occurred_at": "2026-09-30T09:10:00+05:30", "source_adapter": "shiprocket",
     "raw": {"code": "6", "message": "Shipment picked up", "carrier": "Delhivery"},
     "data": {"consignee_phone_last4": "4471"}}
  ]}'
```

```json
{"object": "event_batch", "accepted": 1, "duplicates": 1, "rejected": [], "orders": ["SMY-1001"]}
```

**Signed ingestion (optional).** If the request carries Standard Webhooks headers, Cierto verifies them with your `whsec_` and rejects a bad or stale (over 5 minutes) signature with `401 signature_invalid`. Useful when a connector or queue sits between your OMS and Cierto:

```sh
BODY='{"event_id": "oms:SMY-1001:cancel-check", "order_ref": "SMY-1001", "type": "customer.contacted", "asserted_by": "customer", "occurred_at": "2026-09-30T10:00:00+05:30", "source_adapter": "oms", "data": {"channel": "email", "replied": false}}'
MSG=msg_$(date +%s); TS=$(date +%s)
SIG=$(python -c "import base64,hashlib,hmac,sys; k=base64.b64decode(sys.argv[1].split('_',1)[1]); print('v1,'+base64.b64encode(hmac.new(k, f'{sys.argv[2]}.{sys.argv[3]}.{sys.argv[4]}'.encode(), hashlib.sha256).digest()).decode())" "$WHSEC" "$MSG" "$TS" "$BODY")
curl http://localhost:8787/v1/events -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -H "webhook-id: $MSG" -H "webhook-timestamp: $TS" -H "webhook-signature: $SIG" -d "$BODY"
```

---

## Configuration

### `GET /v1/config` and `PUT /v1/config`

Secret key. Tenant policy for the resolver, appearance defaults and the webhook endpoint. `PUT` is a partial update; each change bumps `version`. See [config-reference.md](config-reference.md).

```sh
curl http://localhost:8787/v1/config -H "Authorization: Bearer $SK"
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"policy": {"auto_refund_cap_inr": 800, "investigate_window_hours": 12},
       "appearance": {"theme": "smytten", "variables": {"colorAction": "#E4007C", "radiusSurface": "12px"}}}'
```

```json
{"object": "config", "tenant": "smytten", "version": 2,
 "policy": {"auto_refund_cap_inr": 800.0, "trust_min_for_instant": 0.6, "investigate_window_hours": 12.0,
            "reattempt_first": true, "food_instant_refund": false},
 "appearance": {"theme": "smytten", "variables": {"colorAction": "#E4007C", "radiusSurface": "12px"}},
 "webhook_url": null}
```

`webhook_url` (an `http(s)` URL, or `""` to stop) makes Cierto also POST each signed webhook there, once, as it records it.

### `POST /v1/config/simulate`

Secret key. Runs the resolver under a proposed policy, against one order or every order in the sandbox, and writes nothing. Compare decisions, approvals and how much would be refunded automatically before you change the live policy.

| Field | | |
|---|---|---|
| `policy` | object | the proposed changes (merged over the current policy) |
| `order_id` | string | optional; default: every order |
| `action` | string | default `report_not_received` |
| `customer` | object | optional trust signals to try, e.g. `{"remedies_90d": 3}` |

```sh
curl http://localhost:8787/v1/config/simulate -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"policy": {"auto_refund_cap_inr": 300, "reattempt_first": false}}'
```

```jsonc
{
  "object": "simulation", "action": "report_not_received",
  "policy": { "current": { … }, "proposed": { … } },
  "summary": { "orders": 4, "changed": 2, "auto_refund_inr": { "current": 599.0, "proposed": 0.0 } },
  "data": [
    { "order_id": "ord_test_unproven", "changed": ["needs_approval"],
      "current":  { "resolution": { "decision": "investigate_and_refund", "needs_approval": false, … }, "trust": { "score": 1.0, "factors": [ … ] } },
      "proposed": { "resolution": { "decision": "investigate_and_refund", "needs_approval": true, … }, "approval_reason": "₹599 is above the ₹300 auto-refund limit" } }
    // …
  ]
}
```

### `GET /v1/client_config`

Publishable key. What the browser SDK may read: brand, vertical and appearance defaults. `Cierto.init` fetches it when you don't pass `appearance.theme`.

```sh
curl http://localhost:8787/v1/client_config -H "Authorization: Bearer $PK"
```

---

## Remedies

A remedy is the money or logistics part of a resolution (`refund`, `partial_refund`, `reship`, `reattempt`). It is `proposed` when policy needs a human, `approved` (by policy or by you), then `executed`; a later decision can `supersede` it.

### `GET /v1/remedies/{id}`

```sh
curl -X POST http://localhost:8787/v1/orders/ord_test_unproven/actions -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"action": "report_not_received"}'
curl http://localhost:8787/v1/remedies/rem_fc0e3c896d6310 -H "Authorization: Bearer $SK"
```

```json
{"object": "remedy", "id": "rem_fc0e3c896d6310", "order_id": "ord_test_unproven", "case_id": "#377992",
 "decision": "investigate_and_refund", "kind": "refund", "amount_inr": 599, "eta": "…", "reference": "CRF-036990",
 "needs_approval": false, "approval_reason": null, "status": "approved", "approved_by": null,
 "trust": {"score": 1.0, "factors": ["…"]}, "resolution": {"…": "the view's resolution"}, "order_version": 17}
```

Remedy ids are stable per tenant, order and decision, so after `POST /v1/dev/reset` the first remedy on `ord_test_unproven` is always `rem_fc0e3c896d6310` (Smytten), `rem_49035abe088603` (Zomato) or `rem_6a44f2b784fecd` (Swish).

### `POST /v1/remedies/{id}/approve`

Secret key. The approval loop: approves a `proposed` remedy. A refund that was due executes at once; one still inside the courier's window executes when the window closes, unless delivery is proven first. `409 remedy_not_approvable` if it's already approved, executed or superseded.

```sh
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"policy": {"auto_refund_cap_inr": 300}}'
curl -X POST http://localhost:8787/v1/dev/reset -H "Authorization: Bearer $SK"
curl -X POST http://localhost:8787/v1/orders/ord_test_unproven/actions -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"action": "report_not_received"}'
curl -X POST http://localhost:8787/v1/remedies/rem_fc0e3c896d6310/approve -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"approved_by": "ops@smytten.example"}'
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"policy": {"auto_refund_cap_inr": 1000, "investigate_window_hours": 24}}'
```

---

## Dev mode

These exist only while `CIERTO_ENV` is unset or `dev`; with `CIERTO_ENV=live` they return `404`.

### `GET /v1/dev/keys`

No key. Every tenant's test keys, webhook secret and test orders.

```sh
curl http://localhost:8787/v1/dev/keys
```

### `POST /v1/dev/advance`

Secret key. Moves the tenant's test clock forward (`minutes` and/or `hours`), firing everything due on the way: detector checks, the courier's proof window, reattempt deadlines. Like Stripe test clocks.

```sh
curl http://localhost:8787/v1/dev/advance -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"hours": 25}'
```

```json
{"object": "test_clock", "tenant": "smytten", "now": "2026-10-01T03:20:00+05:30", "offset_minutes": 1500.0}
```

### `POST /v1/dev/reset`

Secret key. A fresh sandbox: test orders re-seeded at their interesting moment, the test clock back to now, the webhook log and idempotency keys cleared. Keys and config are kept.

```sh
curl -X POST http://localhost:8787/v1/dev/reset -H "Authorization: Bearer $SK"
```

### `GET /v1/dev/webhook_log`

Secret key (or `?tenant=smytten|zomato|swish` with no key, for demo pages). Outgoing webhooks, newest first, each with its signed headers and exact body. `limit` defaults to 50.

```sh
curl "http://localhost:8787/v1/dev/webhook_log?limit=5" -H "Authorization: Bearer $SK"
```

---

## The browser SDK bundle

| URL | |
|---|---|
| `GET /sdk/cierto.js` | UMD: a `<script>` tag defines the global `Cierto`; also `require()`-able |
| `GET /sdk/cierto.mjs` | ESM: `import { Cierto } from 'http://localhost:8787/sdk/cierto.mjs'` |
| `GET /sdk/react.mjs` | The React wrapper (React stays external) |
| `GET /sdk/pakka.js`, `/sdk/pakka.mjs` | The same bundles, for pages written before the rename |

In production the bundle would be served from a CDN, e.g. `https://js.cierto.dev/v1/cierto.js` (illustrative). The element is `<cierto-order>`; `<wismo-order>` and `<pakka-order>` are registered as aliases.

```sh
curl -I http://localhost:8787/sdk/cierto.js
```

## Demo endpoints

The host replicas and the site use demo sessions: several brands on one shared virtual clock, moved by story beats. They return the same view model, and actions go through the same resolver.

| Endpoint | |
|---|---|
| `POST /v1/demo/sessions` | Start a session (preset `signature`) |
| `GET /v1/demo/sessions/{sid}` | Summary: clock, beats, orders (each with its `cause` and `live_cause`), `causes` (id, label, order keys), engine feed |
| `POST /v1/demo/sessions/{sid}/advance` | `{"beat": "claimed"}` or `{"minutes": 30}` |
| `GET /v1/demo/sessions/{sid}/orders/{key}` | `{order, view}`; `?locale=hi-Latn-IN` |
| `POST /v1/demo/sessions/{sid}/orders/{key}/actions` | `{"action": "report_not_received", "locale": "en-IN"}` (also `fix_address` with `landmark`) |
| `POST /v1/demo/sessions/{sid}/orders/{key}/ask` | `{"question": "where is my order?", "locale": "en-IN"}`: the same answer as `POST /v1/orders/{id}/ask` |
| `GET /v1/demo/sessions/{sid}/orders/{key}/case` | For a console: audit timeline, proof, resolution with trust and follow-up, this order's webhooks, and the policy that applied |
| `POST /v1/demo/sessions/{sid}/orders/{key}/approve` | Approve the order's pending remedy (`409` if there is none) |
| `GET /v1/demo/sessions/{sid}/webhooks` | The session's signed webhooks, newest first; `?order=<key>` for one order |

The `signature` preset holds one order per WISMO cause, each at its interesting moment by the `claimed` beat (2:02 pm), and each citing its review evidence in `sources`:

| Key | Cause | What the data says at 2:02 pm |
|---|---|---|
| `swish-stalled` | `rider_stalled` | Rider pings from Agara junction for 4 minutes; the 2:03 pm promise not yet missed. Delivered with OTP at 2:08 pm. |
| `zomato-traffic` | `traffic_delay` | Traffic on Hosur Road added 9 minutes: expected 2:04 pm, latest by 2:10 pm (first promised 1:55 pm). |
| `zomato-batched` | `batched` | One other drop first, 600 m from the shopper; expected 2:10 pm, latest by 2:15 pm. |
| `smytten-address` | `address_mismatch` | Out for delivery; map pin 1.2 km from the typed address; Delhivery's cut-off for a fix is 3:00 pm. |
| `smytten-silent` | `courier_silent` | No scan since Sun 21 Dec at the Bhiwandi hub; the shopper reported it at 1:40 pm, so a refund goes out at Thu 1:40 pm unless it's delivered. |
| `smytten-delivered`, `zomato`, `swish` | `delivered_not_received` | Marked delivered at 2:02 pm with no OTP. |

`smytten-late` (`eta_slipping`), `smytten-refund` (`refund_overdue`) and `smytten-ok` (no cause) complete the preset.

```sh
SID=$(curl -s -X POST http://localhost:8787/v1/demo/sessions | python -c "import json,sys; print(json.load(sys.stdin)['id'])")
curl -X POST http://localhost:8787/v1/demo/sessions/$SID/advance -H "content-type: application/json" -d '{"beat": "claimed"}'
curl http://localhost:8787/v1/demo/sessions/$SID/orders/zomato/actions -H "content-type: application/json" \
  -d '{"action": "report_not_received"}'
curl http://localhost:8787/v1/demo/sessions/$SID/orders/swish-stalled/ask -H "content-type: application/json" \
  -d '{"question": "where is my order?? its been 15 min"}'
curl http://localhost:8787/v1/demo/sessions/$SID/orders/zomato/case
curl "http://localhost:8787/v1/demo/sessions/$SID/webhooks?order=zomato"
```
