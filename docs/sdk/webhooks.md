# Webhooks

Cierto tells your server when something changes that you may need to act on: a case opened, a remedy proposed or approved, money moved, delivery proof changed. Each webhook is signed with the [Standard Webhooks](https://www.standardwebhooks.com) scheme, the same one OpenAI, Twilio and Supabase use.

> **Proof of concept.** Webhooks are recorded, signed and kept in a log you can read (`GET /v1/dev/webhook_log`). If you set a `webhook_url`, each one is also POSTed there once. Retries with backoff, resend from a dashboard and endpoint health are designed, not built.

## Event types

| Type | Sent when | `data.object` |
|---|---|---|
| `case.opened` | Cierto opens a case for an order (the first time a decision needs one) | `case`: `id` (e.g. `#377992`), `order_id`, `reason`, `opened_at`, `ack_by` (48 h), `resolve_by` (30 days) |
| `remedy.proposed` | A decision includes a refund, partial refund, reship or reattempt | `remedy` (below) |
| `remedy.approved` | Policy approved it (`approved_by: "policy"`), or you did through `POST /v1/remedies/{id}/approve` | `remedy` |
| `remedy.executed` | It happened: the refund was initiated, the reship sent, or the reattempt delivered (`outcome`) | `remedy` |
| `remedy.cancelled` | A later decision replaced a remedy that hadn't executed: the courier proved delivery, the shopper confirmed receipt | `remedy` with `status: "cancelled"`, `superseded_by` |
| `order.proof_changed` | The order's delivery proof state changed, e.g. `claimed` → `disputed` → `verified` | `order`: `id`, `proof {state, verified_by}`, `previous {state}` |

The `remedy` object:

```jsonc
{
  "object": "remedy", "id": "rem_fc0e3c896d6310", "order_id": "ord_test_unproven", "case_id": "#377992",
  "decision": "investigate_and_refund", "kind": "refund", "amount_inr": 599,
  "eta": "2026-10-01T02:33:36+05:30",      // when it happens; once executed, when it happened
  "reference": "CRF-036990",
  "needs_approval": false, "approval_reason": null,
  "status": "approved",                    // proposed | approved | executed | superseded | cancelled
  "approved_by": "policy",
  "trust": { "score": 1.0, "factors": [{ "signal": "no_otp", "weight": 0.15, "text": "No OTP used at handover" }, …] },
  "resolution": { … },                     // the order view's resolution, as the shopper sees it
  "order_version": 14
}
```

`status` is the remedy's state when the event was sent. A remedy that policy approves on the spot arrives as `remedy.proposed` with `status: "approved"`, immediately followed by `remedy.approved` from `"policy"`. One that needs a person arrives as `proposed` with `needs_approval: true` and an `approval_reason` such as `"₹599 is above the ₹500 auto-refund limit"`.

## Envelope

```json
{
  "id": "evt_fdbce968ca8264384cd8be1b",
  "type": "case.opened",
  "api_version": "2026-09-30",
  "created": "2026-09-30T02:33:36+05:30",
  "livemode": false,
  "tenant": "smytten",
  "data": { "object": { "object": "case", "id": "#377992", "order_id": "ord_test_unproven", "reason": "report_not_received",
                        "opened_at": "2026-09-30T02:33:36+05:30", "ack_by": "2026-10-02T02:33:36+05:30",
                        "resolve_by": "2026-10-30T02:33:36+05:30" } }
}
```

- **Order.** Delivery order isn't guaranteed. Use `data.object.order_version` (it only grows, per order) to drop a stale update, and don't sort by `created`.
- **Duplicates.** Delivery is at least once. Deduplicate on the `webhook-id` header or the envelope `id`.
- **Unknown values.** New event types and enum values will appear. Ignore what you don't know rather than failing.

## Verifying signatures

Every request carries three headers:

```
webhook-id: msg_7355d7613b8a079d749db507
webhook-timestamp: 1790715816
webhook-signature: v1,8t3g22YWyduEAdD8dHxDmyzHRVFmUhUlGwZWnIyzf3E=
```

The signature is `base64(HMAC-SHA256(key, "{webhook-id}.{webhook-timestamp}.{raw body}"))`, where `key` is the base64-decoded part of your `whsec_…` secret after the prefix. During a key rotation the header can hold several space-separated signatures; accept the request if any `v1` one matches. Reject a timestamp more than five minutes from now. Always verify against the **raw** body, before parsing it.

Node (no dependencies):

```js
import crypto from 'node:crypto'

export function verifyCierto(secret, headers, rawBody) {
  const id = headers['webhook-id'], ts = headers['webhook-timestamp'], sigs = headers['webhook-signature']
  if (!id || !ts || !sigs) throw new Error('missing webhook headers')
  if (Math.abs(Date.now() / 1000 - Number(ts)) > 300) throw new Error('stale webhook')
  const key = Buffer.from(secret.replace(/^whsec_/, ''), 'base64')
  const expected = crypto.createHmac('sha256', key).update(`${id}.${ts}.${rawBody}`).digest()
  const ok = sigs.split(' ').some((s) => {
    const [version, value] = s.split(',')
    const given = Buffer.from(value ?? '', 'base64')
    return version === 'v1' && given.length === expected.length && crypto.timingSafeEqual(given, expected)
  })
  if (!ok) throw new Error('bad signature')
  return JSON.parse(rawBody)
}
```

Python (the same function Cierto uses, `engine/src/wismo/webhooks.py`):

```python
import base64, hashlib, hmac, time

def verify_cierto(secret: str, headers: dict, raw_body: bytes) -> None:
    msg_id, ts, sigs = headers["webhook-id"], headers["webhook-timestamp"], headers["webhook-signature"]
    if abs(time.time() - int(ts)) > 300:
        raise ValueError("stale webhook")
    key = base64.b64decode(secret.removeprefix("whsec_"))
    expected = base64.b64encode(hmac.new(key, f"{msg_id}.{ts}.".encode() + raw_body, hashlib.sha256).digest()).decode()
    if not any(v == "v1" and hmac.compare_digest(s, expected) for v, _, s in (x.partition(",") for x in sigs.split())):
        raise ValueError("bad signature")
```

Any Standard Webhooks library works too (`standardwebhooks` on npm and PyPI): `new Webhook(secret).verify(rawBody, headers)`.

## Try it locally

```sh
export SK=sk_test_cierto_smytten_fqH6YZbp9SXrAC5QvEAllTjA
curl -X POST http://localhost:8787/v1/dev/reset -H "Authorization: Bearer $SK"
curl http://localhost:8787/v1/orders/ord_test_unproven/actions -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"action": "report_not_received"}'
curl "http://localhost:8787/v1/dev/webhook_log?limit=10" -H "Authorization: Bearer $SK"
```

Each log entry has the `headers` and the exact `body` string that was signed, so you can feed them to your verifier. To receive them on your own server, point Cierto at it:

```sh
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"webhook_url": "http://localhost:3000/cierto/webhooks"}'
# and to stop:
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"webhook_url": ""}'
```

The log records each delivery's HTTP status. Reply `2xx` fast and do the work on a queue.

## The approval loop

When policy puts a remedy in front of a person, your support tool gets `remedy.proposed` with `needs_approval: true`, the evidence (`resolution.steps`, `resolution.agent_summary`, `trust.factors`) and the reason it needs a human. Approve from wherever your agents work:

```sh
curl -X POST http://localhost:8787/v1/remedies/rem_fc0e3c896d6310/approve -H "Authorization: Bearer $SK" \
  -H "content-type: application/json" -d '{"approved_by": "priya@smytten.example"}'
```

Cierto records the approval as a fact asserted by the merchant (auditable in `GET /v1/orders/{id}/events`), sends `remedy.approved`, updates what the shopper sees, and executes the remedy when it is due, sending `remedy.executed`. The shopper never has to ask again.

**In the demo.** Demo sessions keep their own signed log: `GET /v1/demo/sessions/{sid}/webhooks` (add `?order=<key>` for one order), and `GET /v1/demo/sessions/{sid}/orders/{key}/case` returns an order's webhooks with its audit timeline, resolution and the policy that applied. `POST /v1/demo/sessions/{sid}/orders/{key}/approve` approves its pending remedy.

**Who moves the money.** In this proof of concept Cierto records the refund's initiation itself, as if through your payment connector, so the flow is visible end to end. In production you choose per remedy type: Cierto calls your refund endpoint (or Razorpay/Juspay with a restricted, agent-tagged key, capped by policy), or your server does it on `remedy.approved` and reports back with a `refund.status` event carrying the bank reference (ARN/RRN).

## Signing what you send

The same scheme works in the other direction. If `POST /v1/events` carries `webhook-id`, `webhook-timestamp` and `webhook-signature` headers, Cierto verifies them with your `whsec_` secret and rejects a bad or stale signature with `401 signature_invalid`. See [the example in the API reference](api-reference.md#post-v1events). (The proof of concept uses one secret per tenant for both directions; production would issue a separate inbound secret.)

## Planned

- Retries with exponential backoff for three days (live) and a few hours (test); resend from a dashboard for 15 days.
- Endpoint health, automatic disable after repeated failures, and an alert.
- Secret rotation with both secrets signing for 24 hours.
- Thin events (`{id, type, related_object}`) for hosts that prefer to fetch the latest state.
- More types: `order.truth_changed`, `exception.opened`/`resolved`, `case.updated`/`closed`, `conversation.handoff_requested`, `notify.requested`, `incident.detected`.
