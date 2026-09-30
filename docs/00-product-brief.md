# Intelligent WISMO — Product Brief (Phase 0)

*Working name. Status: draft v0.1, 2026-09-29. Owner: Ishrajesh.*

## 1. One line

A drop-in layer for any shopping or delivery app that **tells customers what actually happened to their order before they have to ask, and gives support the evidence and authority to fix it.** It is not another tracking page.

## 2. The problem, from evidence

I collected **93 unique, sourced, public post-purchase complaints about Smytten** (Jan 2025 – Sep 2026), plus 103 older ones, from Trustpilot, Voxya, the App Store, MouthShut and IndiaCustomerCare. Every one has a permalink, a date and a verbatim quote (`data/complaints.json`).

| Rank | Failure the customer leads with | Unique complaints | Share |
|---|---|---|---|
| 1 | **Marked delivered, but nothing arrived** (no call, no OTP) | 35 | 37.6% |
| 2 | Late / stuck / never arrived (delay, frozen tracking, "out for delivery" for days) | 21 | 22.6% |
| 3 | Refund stuck at "initiated" or never created | 12 | 12.9% |
| 4 | Wrong, missing or partial items, then claim denied | 12 | 12.9% |
| 5 | Courier attempt failures (wrong phone on the parcel, "no partner in your area") | 6 | 6.5% |
| 6 | Money debited, no order created | 2 | 2.2% |

Two findings shape the whole product:

1. **The worst failure isn't "slow", it's "falsely closed".** In 2019–2024 the top complaint was delay (27%) and "marked delivered" was 6%. In 2025–26, "marked delivered" is 38%. A tracker that mirrors the courier's status shows "Delivered ✓" and is confidently wrong.
2. **Support multiplies the damage.** Only 2 complaints *lead* with support, but **36 of the 40 customers who contacted support describe it failing**: an AI chat that repeats questions ("10 bar ek issue raised kar chuki hai"), tickets closed as "resolved" with no fix, tickets that can't be raised or don't appear, no phone line (which is Smytten's stated policy), and "delivered correctly from our end". Support answers from the same status the customer is disputing.

**Honest limits.** This is a catalogue of failure modes, not a rate. There is no public order-volume denominator; 63 of 93 rows are unverified public comments; and 39 of 93 fall in December 2025 (27 of the 35 "marked delivered"), which looks like one courier or peak-season incident plus copy-paste pile-on. I use the data to define **what to detect**, not to claim "X% of Smytten orders fail". The December cluster is itself a design input: a fleet-level spike like that should be caught on day two, not after dozens of public complaints.

**Beyond Smytten.** Quick commerce and food delivery (Swish, Swiggy, Zomato) share the same failure shapes on a minutes-long clock: "delivered" with no food, refunds that say processed but never arrive, and bot-only support. Research on those is in progress and will adjust section 6.

## 3. Who it's for

| User | Job to be done | Today's failure |
|---|---|---|
| **Shopper** | "Tell me the truth about my order and let me fix it myself." | Sees raw courier status; has to chase; can't escalate to a human |
| **Support agent** | "Show me what really happened and let me act without five tools." | Sees the same "Delivered" as the bot; closes the ticket; no authority |
| **Ops lead** | "Tell me when a courier, hub or lane is going wrong, before Twitter does." | Finds out from complaint volume, days late |
| **Host app's engineer** (buyer) | "Add this in days without replacing our OMS or helpdesk." | Vendor tools are quote-only enterprise integrations taking 2–4 months |

## 4. What makes it "intelligent"

Five capabilities. Each maps to a failure in section 2:

1. **Delivery truth, not courier status.** Every order carries a *derived* state with a confidence level: a "Delivered" scan is only a *claim* until it's backed by proof (OTP, photo, customer confirmation) or by time passing without a dispute. Delivered-before-ETA, delivered with no out-for-delivery scan, and phone-on-parcel ≠ account phone all mark it *unverified*. → Failures 1, 5.
2. **Proactive exception detection.** SLA and ageing rules on one event timeline: ETA slipped twice, no scan in 48h, "out for delivery" for over 24h, refund initiated over 7 working days ago with no bank reference, cancelled at the doorstep but still "Shipped", payment succeeded with no order after N minutes. The customer hears about it first, with a reason and a new date. → Failures 2, 3, 6.
3. **Support that can see and act.** An AI agent with order context (it never asks for the order ID) and tools: it can explain the evidence, request a re-attempt, update the phone number, or open a missing-item claim. It **proposes** refunds and reships; a human approves them. It can never close a ticket while the order is still in an exception state, and "talk to a person" is always one tap away. → The support failures.
4. **Visible clocks and rights.** Every issue gets an ID the customer can see, a 48-hour acknowledgement timer and a 30-day resolution timer (E-Commerce Rules 2020). Failed payments get an RBI T+5 auto-reversal countdown. When a deadline is breached, the customer gets a ready-to-file escalation (NCH 1915 / e-Jagriti / bank). No vendor we found exposes these to the customer.
5. **Fleet-level anomaly view.** Rate of unverified deliveries by courier, hub and day. This would have flagged the December 2025 pattern within days.

## 5. How it fits into any app

- **One canonical order timeline**, modelled on ONDC/Beckn fulfilment states plus a normalised status taxonomy that keeps the raw carrier code. Any source maps into it through an adapter.
- **Three integration tiers:** a hosted page (zero code), an embeddable web component themed by a design-token file per brand, and a headless API/SDK for native apps.
- **Same truth on every surface:** in-app widget, WhatsApp, the support agent's view, and an MCP/tool API so the host's existing AI assistant can ask "what really happened to order X?".

"Custom UI preference" is therefore a config file (brand tokens, language, tone), not a fork.

## 6. Proof of concept scope

**Demo:** three mock host apps, each a replica order journey with the same engine and widget in a different skin.

| Host | Journey shape | Clock |
|---|---|---|
| Smytten-style | D2C trial box via courier (parcel) | days |
| Swish-style | 10-minute food delivery | minutes |
| Zomato-style | restaurant food delivery | minutes to an hour |

Order events are generated by a replay engine. Every demo scenario is derived from, and cites, a real complaint ID.

**Why mocks.** Smytten, Swish, Swiggy and Zomato don't expose consumer order or tracking APIs to third parties; only approved restaurant/POS partner integrations exist. A real integration needs a partnership. The POC proves the engine and the integration surface; the adapters show exactly where real data would plug in (e.g. Shiprocket/Delhivery webhooks, ONDC `/on_status`).

### Not building (and why)

| Cut | Reason |
|---|---|
| Delivery-date prediction at order time | Needs lane history a third party won't have; in-flight breach detection gets most of the value with only events + a promise date |
| Live rider map | Swiggy and Zomato already do this well; copying it proves nothing |
| Real WhatsApp/SMS sending | DLT registration and business verification take weeks; a WhatsApp-style simulator shows the same flows and templates |
| Real payments/refunds | A mock gateway with realistic states (initiated → RRN → credited) is enough to demonstrate the refund clock |
| ML anomaly models | No labelled data; transparent rules plus a statistical spike check are more defensible at this stage |
| Multi-language beyond English + Hinglish | Hinglish is in the evidence; other languages are a later phase |
| Scraping or overlaying the real apps | Terms-of-service and data-protection risk; mocks are the honest route |

## 7. How we'll know it works

Measured by **replaying the complaint corpus** through the engine, not by vendor-style deflection claims.

| Metric | Definition | Target (to validate) |
|---|---|---|
| **Detection coverage** | Share of the 93 complaints whose failure the engine flags from the events it would have had | ≥ 80% of WISMO-core cases |
| **Lead time** | Time between the engine's flag and the customer's reported complaint | Flag before the customer would have had to ask |
| **False alarm rate** | Flags on synthetic healthy orders | < 5% |
| **Verified resolution rate** | Agent conversations that end in a real state change or a customer confirmation, as opposed to the conversation merely ending | Reported separately from "automation rate" |
| **Anti-pattern tests** | Scripted tests from the complaints: no re-asking the order ID, no closing while in exception, human path always offered, Hinglish understood | 100% pass |
| **Integration effort** | Time for a new host skin plus adapter | < 1 day per host |

Why this matters: vendors blur "the bot engaged" and "the problem was solved". Reporting both honestly, on public evidence, is more credible than any headline percentage.

## 8. Positioning

Existing tools fall into two layers that rarely meet:

- **Tracking platforms** (AfterShip, Narvar, parcelLab; in India ClickPost, Shiprocket, Unicommerce) surface courier events but don't audit them.
- **Support AI** (Gorgias, Intercom Fin, Zendesk; in India Haptik, Yellow.ai, Verloop) answers from those same unaudited statuses.

Agentic post-purchase products (Narvar NAVI, Jan 2026; ClickPost Parth, 2025) are enterprise, quote-priced, and work on the merchant's side of the problem. **The gap is delivery truth plus customer-side resolution with statutory clocks, for Indian D2C and quick commerce, integrable by one engineer in days.**

## 9. Key risks and assumptions

| Risk / assumption | Mitigation |
|---|---|
| Real host data may lack an OTP flag, a promised ETA or the parcel's phone number | Engine degrades gracefully: absence of proof is itself a signal; customer confirmation fills the gap |
| The December 2025 spike may be one incident, not a pattern | Framed as a replay scenario, not a prevalence claim |
| An LLM agent could take wrong money-moving actions | Humans approve refunds and reships; deterministic workflows for predictable paths; evals include adversarial cases |
| A third-party layer holds customer PII (DPDP Act) | Designed as a data processor: minimal fields, tenant isolation, erasure endpoint, India-region data |
| Hinglish degrades model accuracy | Hinglish cases in the eval set from day one |

## 10. Open questions

- What courier/tracking stack do Smytten-like brands actually run, and do Indian carrier APIs expose OTP-verified, call-attempt or photo proof fields?
- Precise status models and failure moments for Swish/Swiggy/Zomato (research in progress).
- Which ONDC fulfilment-state version is live in production (v1.2 vs the 2.0 draft)?
- Can one real D2C brand or Shopify store share 30 days of tagged tickets to calibrate the "support contacts per 100 orders" baseline?

---
*Evidence: `research/research.py` (dataset and method), `data/complaints.json` (export). Research notes on landscape, integration, UX and regulation will be linked from `docs/` as they're finalised.*
