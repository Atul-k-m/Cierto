# Configuration reference

Cierto has two kinds of configuration, and they never mix:

- **Tenant config** lives on the server: the resolver's policy, appearance defaults and your webhook endpoint. You set it with your secret key (`PUT /v1/config`), try changes first with `POST /v1/config/simulate`, and every change bumps a version. The browser can never read or raise a refund cap.
- **Client config** is presentation only: locale, theme and variables, passed to `Cierto.init` or to a single `mount`.

## Policy

```sh
export SK=sk_test_cierto_smytten_fqH6YZbp9SXrAC5QvEAllTjA     # the Smytten test tenant's secret key
curl -X PUT http://localhost:8787/v1/config -H "Authorization: Bearer $SK" -H "content-type: application/json" \
  -d '{"policy": {"auto_refund_cap_inr": 800, "trust_min_for_instant": 0.7}}'
```

| Field | Type, range | What it controls |
|---|---|---|
| `auto_refund_cap_inr` | number ≥ 0 | Refunds (and reships, by order value) above this need a human to approve. `0` means every money move is approved by a person. |
| `trust_min_for_instant` | 0 to 1 | Below this trust score, a remedy is proposed and waits for approval instead of going ahead. |
| `investigate_window_hours` | > 0, ≤ 720 | For `investigate_and_refund`: how long the courier has to prove delivery before the refund goes out on its own. |
| `reattempt_first` | boolean | A parcel stuck out for delivery (or with a failed attempt): ask the courier to reattempt within 24 hours before moving to a refund. |
| `food_instant_refund` | boolean | Quick commerce (`vertical: quick`): refund at once when the delivery is unproven or badly late, instead of investigating. |

The test tenants start with these values:

| Tenant | Vertical | `auto_refund_cap_inr` | `trust_min_for_instant` | `investigate_window_hours` | `reattempt_first` | `food_instant_refund` |
|---|---|---|---|---|---|---|
| `smytten` | parcel | 1000 | 0.60 | 24 | true | false |
| `zomato` | quick | 500 | 0.60 | 2 | false | true |
| `swish` | quick | 300 | 0.60 | 1 | false | true |

A new integration should start strict (`auto_refund_cap_inr: 0`, so the resolver proposes and people approve), run `simulate` over real disputes, and raise the cap once the proposals prove right. That is the path in [integrate-smytten-like.md](integrate-smytten-like.md#7-policies).

### How the resolver decides

The decision is deterministic code (`engine/src/wismo/resolver.py`). The same order, action and policy always give the same decision, and `simulate` shows it before you commit.

| Situation when the shopper acts | `report_not_received` | `talk_to_person` |
|---|---|---|
| Marked delivered **with** proof (OTP, or photo plus GPS at the address) | `escalate_human`: a person reviews the evidence; no automatic money | `escalate_human` |
| Marked delivered **without** proof, quick commerce, `food_instant_refund` | `refund_now` (gated) | `escalate_human` with the refund ready for the agent to approve |
| Marked delivered **without** proof, otherwise | `investigate_and_refund`: courier asked to re-verify; refund at the end of the window unless delivery is proven (gated) | as above |
| Parcel stuck out for delivery or failed attempt, `reattempt_first` | `reattempt` by +24 h; if it misses, `refund_now` (gated) | `escalate_human` |
| Parcel late or tracking stalled | `investigate_and_refund`: courier asked to locate it; refund unless it's delivered first (gated) | `escalate_human` with the refund ready |
| Food late (quick), `food_instant_refund` | `refund_now` (gated) | `escalate_human` with the refund ready |
| Cancelled or returned, refund overdue | `escalate_human` with `refund_trace` and the bank reference | same |
| Cancelled, refund never started (prepaid) | `refund_now` (owed money: cap only, no trust check) | `escalate_human` with the refund ready |
| On its way and not late | `none`: says so, with the promised time | `escalate_human` |

`confirm_received` is always `none`, and cancels a refund still waiting to go out. `fix_address` is always `none`: it records the spot the shopper confirmed (and any landmark) and passes it to the courier. `report_missing_item` refunds the missing share of the order for food (`refund_now`, `partial_refund`) and reships it for parcels (`reship`), both gated.

**"Gated"** means the money gate applies: a remedy needs approval (`needs_approval: true`) if the amount is above `auto_refund_cap_inr`, if trust is below `trust_min_for_instant`, or if the order was cash on delivery. A shopper who asks for a person is never refused one, and the shopper is never told their trust score.

**Proof beats the clock, both ways.** If the courier sends real proof (an OTP-verified or photo-and-GPS `delivered` event) while a refund is waiting, the refund is paused and the case goes to a person (`remedy.cancelled`, then an `escalate_human` resolution). Silence proves nothing: a delivery already flagged as suspicious never becomes "verified" just because the report window lapsed.

### Trust score

The score starts at 0.50 and moves with named signals, clamped to 0..1. Every resolution stores the factors, and the agent summary names the top three.

| Signal | Weight | Source |
|---|---|---|
| OTP entered at handover | -0.35 | the delivery claim's `proof.otp_verified: true` |
| No OTP used at handover | +0.15 | `proof.otp_verified: false` |
| No OTP recorded | +0.05 | `otp_verified` not sent |
| Delivery photo on file / no photo | -0.10 / +0.05 | `proof.photo_url` |
| Courier GPS at / away from the address | -0.15 / +0.10 | `proof.geo_verified` |
| No call to the customer | +0.05 | `proof.call_logged: false` |
| Flagged as suspicious by the engine | +0.10 | the `suspicious_delivery` detector |
| Parcel carried a different phone number | +0.05 | `consignee_phone_last4` vs `account_phone_last4` |
| No refunds in 90 days / one / two or more | +0.10 / -0.05 / -0.25 | `customer.remedies_90d` |
| Account under 30 days / over a year | -0.10 / +0.05 | `customer.account_age_days` |
| Five or more orders in 90 days | +0.05 | `customer.orders_90d` |
| Cash on delivery | -0.10 | `order.placed` `payment: "cod"` |
| Customer attached a photo (missing item) | +0.10 | the action's `photo: true` |

Delivery evidence counts only for disputes about a delivery claim. For late or missing orders, trust rests on the customer's history, so an order with **no** history sits at 0.50 and, under the default 0.60 threshold, goes to a person. Send `customer` signals with `POST /v1/orders` to let good customers through.

### Clocks

Clocks come from the order's vertical, not from tenant config (in this proof of concept). An order is `parcel` or `quick` from its tenant, unless `order.placed` says otherwise (`vertical` in `POST /v1/orders`).

| Clock | `parcel` | `quick` |
|---|---|---|
| Customer can dispute a "delivered" for | 48 h | 40 min |
| Tracking stalled after no scan for | 72 h | 12 min |
| Packed but not picked up | 48 h | 15 min |
| Out for delivery with no outcome | 24 h | 25 min |
| Late-data grace before a promise counts as missed | 12 h | 3 min |
| Support must acknowledge (E-Commerce Rules 2020) | 48 h | 48 h |
| Support must resolve | 30 days | 30 days |
| Refund must start after cancellation | 48 h | 2 h |
| Refund should credit within (working days) | 7 | 5 |
| Rider stopped: pings from one spot (within 40 m) for | 20 min | 4 min |
| An answer calls tracking data stale after | 24 h | 5 min |
| Map pin this far from the typed address needs confirming | 500 m | 150 m |

### Language and the LLM

Messages are templated in English (`en-IN`) and Hinglish (`hi-Latn-IN`); ask for one with `locale` on the view or the action. If the server has `ANTHROPIC_API_KEY` set (and the optional `anthropic` package: `pip install "wismo[llm]"`), Claude (`claude-sonnet-5-5`) rewords `shopper_message` and `agent_summary` from the structured facts at decision time. The rewrite is discarded, and the template kept, if it adds or changes any number, drops the amount, the case id or a reference, or fails for any reason. The resolution event records whether a rewrite was used.

Answers to shopper questions (`POST /v1/orders/{id}/ask`) follow the same rule, more strictly: the answer is composed from the order's data by templates, and a rewrite is discarded if it adds, drops or changes any number, time, weekday, month or relative day ("today", "kal"). The response says whether a rewrite was used (`rephrased`).

## Appearance

The widget has no look of its own: every colour, face and radius is a token from the host. Pick a theme, then override single tokens with variables (the Stripe Appearance model).

```js
Cierto.init({
  publishableKey: 'pk_test_cierto_…',
  fetchClientSecret,
  appearance: { theme: 'neutral', variables: { colorAction: '#E4007C', fontBody: 'Inter, sans-serif', radiusSurface: '12px' } },
})
```

**Precedence**, highest first: `mount(…, { appearance })`, then `Cierto.init({ appearance })`, then the tenant's `appearance` from `PUT /v1/config` (fetched from `GET /v1/client_config` when you don't pass a theme), then the theme's own tokens.

**Themes:** `neutral` (default), `smytten`, `zomato`, `swish`.

**Variables.** Each maps to one `--w-*` custom property inside the widget's shadow root. Values must be plain CSS values (no `;`, `{`, `}`, `<`, `>` or `\`, at most 120 characters); anything else, and any unknown name, is ignored with one console warning.

| Variable | Token | `neutral` value | Used for |
|---|---|---|---|
| `colorInk` | `--w-color-ink` | `#1f2328` | Body text |
| `colorMuted` | `--w-color-muted` | `#57606a` | Secondary text, times |
| `colorSurface` | `--w-color-surface` | `#ffffff` | Cards |
| `colorSurface2` | `--w-color-surface-2` | `#f4f5f7` | Resolution panel, calm badge |
| `colorLine` | `--w-color-line` | `#dfe2e6` | Borders |
| `colorAction` | `--w-color-action` | `#1f2328` | Primary button |
| `colorActionInk` | `--w-color-action-ink` | `#ffffff` | Text on the primary button |
| `colorActionStrong` | `--w-color-action-strong` | `#000000` | Hover, links |
| `colorOk` / `colorOkSoft` | `--w-color-ok` / `-ok-soft` | `#1a7f37` / `#e6f4ea` | Verified, refunded |
| `colorCheck` / `colorCheckSoft` | `--w-color-check` / `-check-soft` | `#8a5300` / `#fff3dc` | Unproven, waiting for approval |
| `colorAlert` / `colorAlertSoft` | `--w-color-alert` / `-alert-soft` | `#b0241c` / `#fdebea` | Issue open, overdue |
| `colorFocus` | `--w-color-focus` | `#1f2328` | Focus ring |
| `fontBody` | `--w-font-body` | `system-ui, …` | All text |
| `radiusSurface` | `--w-radius-surface` | `12px` | Cards and panels |
| `radiusControl` | `--w-radius-control` | `10px` | Buttons |

Status is always carried by words as well as colour, so a brand palette can't make a state unreadable. Keep text contrast at WCAG AA (4.5:1) when you override ink or action colours.

## Client options

`Cierto.init(options)`:

| Option | Type | |
|---|---|---|
| `publishableKey` | string | required; `pk_test_cierto_…`. A secret key throws. |
| `fetchClientSecret` | `({ orderId }) => Promise<string>` | required; calls your server, which calls `POST /v1/customer_sessions`. Called again when the secret expires. |
| `locale` | `'en-IN' \| 'hi-Latn-IN'` | default `en-IN`. Hinglish covers the delivery check, the dispute and the resolution; other details fall back to English. |
| `appearance` | `{ theme?, variables? }` | see above |
| `baseUrl` | string | the Cierto API. Default: the origin that served `cierto.js`, else the page's origin. |
| `pollIntervalMs` | number | default 3000; how often mounted widgets and subscriptions refresh |

`cierto.order(id).mount(target, options)`:

| Option | |
|---|---|
| `variant` | `tracking-card` (default: a card in your stack), `orders-row` (inside your order list), `after-delivered` (the main content of a post-delivery screen) |
| `locale`, `appearance` | override the client's for this widget |

Returns `{ element, update(options), unmount() }`. `cierto.update({ locale, appearance })` changes every mounted widget.

**Events** (`cierto.on(name, handler)`, returns an unsubscribe function):

| Event | Payload | |
|---|---|---|
| `resolution` | `{ orderId, resolution }` | Cierto decided something new for this order |
| `action` | `{ orderId, action }` | The shopper tapped an action. Return `false` to handle it yourself (for example, open your own chat for `talk_to_person`). |
| `change` | the order view | Any change to the view |
| `error` | `{ orderId, code?, message }` | A failed request; the widget keeps its last good view and retries |

The element also dispatches DOM events that bubble out of the shadow root: `cierto:change`, `cierto:resolution`, `cierto:action` (cancelable), `cierto:error`, and `wismo:change` for older hosts.

## Webhook endpoint

`PUT /v1/config {"webhook_url": "https://your-app.example/cierto/webhooks"}` makes Cierto POST each signed event there as it happens, once (no retries in the proof of concept). Every event is also kept in `GET /v1/dev/webhook_log`. See [webhooks.md](webhooks.md).
