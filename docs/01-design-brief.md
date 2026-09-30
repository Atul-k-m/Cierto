# Design Brief — Shopper widget, host demos and platform UI

*Shaped with Impeccable, 2026-09-29. Status: confirmed by the user, pre-build. Companion to `00-product-brief.md` and `PRODUCT.md`.*

## 1. Job and audience

- **Shopper** (primary), in a host app on their phone, worried about one order: late, stuck, "delivered" but not received, refund missing, or an urgent order (medicine). They need the truth and a way forward in one glance. Mode: **Operate**.
- **Evaluator** (hiring manager), watching a demo: must see within one minute that this upgrades screens real apps already have, and why it's smarter than courier status.

## 2. Outcome and proof

Success = the shopper can answer "what actually happened, what do I do, by when?" without opening a chat. Proof is carried by real material: every demo scenario cites a complaint ID from `data/complaints.json`; host screens are grounded in the real apps' store screenshots (`.impeccable/refs/`).

## 3. Selected direction

**Two visual worlds with a hard boundary.**

1. **Host demos: each host's real look.** The widget has no identity of its own inside a host; it takes the host's type, colours, radius and buttons through theme tokens. Sampled references: Zomato `#df3542` (brand), `#24963f` (on-time header); Swish `#33c362` / `#1c8743`, yellow `#ffe644`; Smytten navy `#0d1929`, blue `#5292dc`, mint `#eefef1`. Each demo carries a small persistent label: "Concept demo · not affiliated with <brand>". Wordmarks are recreated as styled text; no copied logo files.
2. **Our platform UI: the iridescent cloud-edge world** (user-pinned). White field, slate ink, colour confined to a thin mint/rose/violet edge; text stays achromatic. Its uncertainty grammar maps onto delivery truth: the edge is *absent* (no proof yet), *forming* (courier says), *vivid* (confirmed), *dispersed* (disputed or lapsed). Applies to the demo launcher, hosted tracking page, support console and ops dashboard.

**Three demo structures, one per place a shopper checks an order:**

| Where the shopper checks | Host | Structure |
|---|---|---|
| The order list | Smytten | **My Orders, told truthfully.** Each row: truth line ("Courier says delivered 12 Sep · not confirmed by you"), deadline chip, one action |
| The live tracking screen | Zomato | **One smart card** slotted between the rider card and "Need help"; it changes job: on the way → did you get it? → your case → your refund |
| The moment after "Delivered" | Swish | **After-delivered screen** replacing the collapse-to-receipt: courier claim, proof row (OTP · photo · call, absences shown), one question, time left to report |

**Rules carried from the challengers the roll beat** (apply to all three structures):
- Fixed slots per row/card (status, deadline, action); missing proof is drawn on purpose ("No OTP used"), never left blank.
- Four named proof states: none yet · courier says · confirmed by you · disputed.
- Every line reads correctly as plain text, so it goes out unchanged on WhatsApp/SMS.
- Same three parts in every host, restyled only by tokens.
- Actions are the host's own pill buttons, never a boxed third-party panel.
- When an issue resolves, it says how in one line, then settles back.
- Carried from round 1: a changed ETA stays visible, struck through beside the new one; every open problem names who holds it (courier / brand / your bank); a human is one tap away.

**Signature moment for the demo:** the launcher shows the three phones side by side; the evaluator triggers "courier marks delivered, no OTP" and watches all three host screens tell the truth at once, while the platform's cloud edge shifts from *forming* to *disputed*.

## 4. Scope and boundaries

- **Fidelity:** interactive, production-grade front end driven by the replay engine; code-led (no image generation on this machine).
- **Breadth:** demo launcher (platform world) + three host phones. Support console and ops dashboard follow in later phases, in the platform world.
- **Anti-goals (from the user):** bolted-on/third-party look; chatbot-first (no screen opens on a text box); alarmist (calm, factual even when wrong; red reserved for true breaches); legal/jargon heavy (plain language; NDR/RTO/RBI never shown raw).
- **Untouched:** each host's own header, map, rider/kitchen cards and navigation, except the slots named above.

## 5. States and ranges

Scenarios in the first build, each tied to complaint IDs:

1. **Delivered but not received** (parcel and food): courier claim with no OTP/call; dispute flow; report window clock.
2. **Late / stuck in transit** (parcel): ETA slipped twice, no scan for 3 days; told first, with reason and new date.
3. **Refund stuck at "initiated"**: refund sub-timeline with bank reference, expected credit date, overdue escalation.
4. **10-minute food "delivered", no food** (Swish): minutes-scale version of #1.
5. **Urgent order (medicine)**: *deferred by the user (2026-09-29)*; revisit after the first build. Shortened clocks, immediate human, alternatives offered; host not yet chosen.

Ranges: 1–6 orders in the list; 0–3 open issues per order; clocks from minutes (food) to 30 days (grievance); Hinglish and English copy.

## 6. Interaction and layout

Mobile-first host phones at device viewport; launcher at desktop width with phones in frames. New events announce to screen readers; status never by colour alone; one-handed reach for primary actions; "Talk to a person" persistent on every issue state.

## 7. Constraints and open decisions

- **Platform:** web; widget as a framework-free Web Component (Shadow DOM, token-themed); serverless backend (provider TBD in the architecture step).
- **Accessibility:** WCAG 2.1 AA.
- **Open:** urgent-medicine scenario (deferred) and its host; product name; whether the platform world also skins the public hosted tracking page for hosts that want zero-code (default: yes).
- **Next Impeccable step (build):** the direction contract and `DESIGN.md` are written at build time, not here.
