# Decision log

One short note per iteration: what was decided, what was cut, and why. These become the pitch write-up.

## 1.1 — Event log (2026-09-29)

**Built:** canonical `Event` model with a two-level status taxonomy mapped to ONDC fulfilment states; an append-only Postgres event log with per-tenant row-level security; a scenario format and `python -m wismo replay`; the first scenario from complaint IC-213360. 27 tests pass.

**Decided:**
- Every event records **who asserted it** (merchant, carrier, rider, payment, customer, engine). "Delivered" from a courier and "received" from a customer are different facts, and the dataset's worst failure lives in that gap.
- Proof fields are **tri-state**: `false` ("no OTP was used") is evidence; `null` ("the carrier didn't say") is not. Collapsing them would make a missing field look like a verified delivery.
- Timelines sort by **when things happened**, not when they arrived. Carrier pushes arrive late; the scenario proves a late hub scan still lands before "out for delivery".
- Retries are safe: the same `event_id` with the same content is a no-op; the same ID with different content is rejected as an error, not silently overwritten.
- Isolation fails closed: a session with no tenant set sees zero rows; one tenant can't read or write another's events. The log refuses UPDATE, DELETE and TRUNCATE even from the database owner.
- Embedded Postgres (`pgserver`) instead of Docker or SQLite: nothing to install, and local runs use the same database features (RLS) as the cloud.

**Cut / deferred:** projections and derived state (1.2); timers (1.3); snapshotting; any cloud adapter (Phase 4).

**Honesty note:** the IC-213360 timeline is synthesized from the complaint summary; dates, amounts and phone digits are illustrative and labelled so in the scenario file.

## 1.2 — Projector (2026-09-29)

**Built:** `project(events, now, profile)`, a pure function from the log to what is actually known: merchant, carrier and customer views kept apart; a reconciled state; named conflicts; and a delivery **proof state** (none → claimed → verified or disputed).

**Decided:**
- "Delivered" from a courier is a **claim**. It becomes verified only by an OTP, a photo *with* a geofence match, the customer confirming, or the report window lapsing with no dispute. A photo alone doesn't count.
- The customer's "not received" outranks the courier's "delivered".
- Conflicts are first-class: a doorstep rejection while the store still says "Shipped" (VX-07) is flagged, not silently overwritten by whichever source spoke last.
- The projection only sees events that have happened by "now". Found the hard way: replaying over a log that already held the scenario made every finding fire at order time.

## 1.3 — Commitments and the virtual clock (2026-09-29)

**Built:** commitments derived from the projection (ETA and every revision, report window, 48 h acknowledgement, 30-day resolution, refund start, refund credit in working days, order-after-payment, RBI T+5); an in-process scheduler on a **virtual clock** that replays days in milliseconds; the engine loop (ingest → project → detect → record finding → schedule next check).

**Decided:**
- Superseded ETAs stay visible (void, not deleted), so "the date moved three times" is a fact the UI can show.
- The engine schedules its own wake-ups from the commitments; no polling jobs.
- **Reaching a deadline counts as missing it.** A timer firing at exactly the due moment used to see "not yet late" and never rescheduled; a refund-start breach was caught 16 h late until fixed.
- **Late carrier data gets a grace period** (parcel 12 h, quick 3 min) before an ETA counts as missed. Found in the false-alarm run: an on-time delivery whose scan arrived 8 h late was flagged as late.
- Working days are Monday–Friday; bank holidays are a known simplification.

## 1.4 — Detectors and the replay harness (2026-09-29)

**Built:** 17 named rules, each with a plain-language message and the party holding the problem; `python -m wismo coverage`, which turns every complaint into a timeline of **only its stated facts**, replays it, and replays 400 healthy orders to measure false alarms.

**Decided:**
- Two kinds of finding: **exceptions** (something is wrong) and **checks** ("did you get it?"). Checks are cheap and are not counted as alarms.
- Unstated facts take the value that makes detection *harder*: tracking keeps moving, an out-for-delivery scan precedes every "delivered", proof is unknown rather than missing.
- Dropped a "delivered suspiciously early" flag: early deliveries are normal, and it would have raised false alarms.
- Each harness bug was fixed in the harness, not by loosening a rule: two generator timelines contradicted the complaint's stated facts or made "healthy" orders late.

## Phase 1 exit — coverage report (2026-09-29)

Full report: `docs/reports/phase1-coverage.md` (regenerate with `python -m wismo coverage`).

- **48 of 80** detectable complaints (60%) flagged from order, carrier and payment data alone; **79 of 80** before the public complaint once the engine's own "did you get it?" prompt and support clocks are included.
- Median lead time **4.3 days** before the public complaint (5.1 days from data alone), measured only on the 31 caught complaints with stated dates.
- **0 false alarms on 400 healthy orders**; **23% when carriers may go quiet for up to 96 h**. The stall threshold is the main trade-off a merchant must set.
- **13 item problems** (wrong, missing, damaged) can't be seen in delivery data at all; the engine's job there starts at the customer's report (Phase 3 cases).
- **1 explained miss:** IC-207446 is a return after delivery; returns aren't modelled yet.

**Honesty notes:**
- The rules were written after reading these complaints, so this is in-sample coverage, not a generalisation claim. The out-of-sample test is quick-commerce complaints and, later, real carrier data.
- Lead times for undated complaints depend on default timelines and are excluded from the headline.

## Phase 2 — The shopper sees the truth (2026-09-29)

**Built:**
- An engine HTTP API: an order *view* model plus demo sessions on the virtual clock.
- The `<wismo-order>` Web Component: Shadow DOM, themed by DTCG token files, in three variants.
- Concept replicas of Smytten (My Orders), Zomato (live tracking) and Swish (after delivery). Each carries a "not affiliated" label and uses no copied assets.
- The demo launcher in the platform's own cloud-edge world.
- Engine tests grew to 61. The finish review ended **ship** after three verdict rounds. DESIGN.md is written from the shipped code.

**Decided:**
- **Built from real screens, not reasoning.** The owner rejected the first structure round as generic. Studying the apps' own App Store screenshots showed that the widget should *upgrade slots those screens already have* (order-list row, tracking-card stack, post-delivery screen) instead of adding a new UI.
- **The widget has no identity.** Every colour, face and radius comes from the host's token file, and a brand-free neutral skin is the default. Issue references are host-neutral (`#337857`).
- **Hosts can let the truth drive their own chrome** (the headless tier). Zomato's header stops saying "on the way" in green once the proof is only the rider's tap.
- **Suspicious deliveries never become "verified" by silence.** An ordinary claim verifies when the report window lapses; a claim the engine flagged stays unproven until the customer answers.
- **Quick-commerce realities:** a rider on the road sends location pings (a new `en_route` status); waiting for the restaurant is not a stall; "no out-for-delivery scan" is only suspicious for parcels.
- **Accessibility over exact brand colour.** Smytten's #5292dc and Zomato's #df3542 fail WCAG AA with white text, so the replicas use #2f6fbd and #cb202d for primary buttons.

**What review caught that the build thread didn't:**
- Remounting the proof-edge ring also remounted the phone, which collapsed it to a sliver.
- The pastel proof edge was about 1.3–2:1 against the field and invisible at a glance.
- The sticky beat bar hid every phone's complaint citation at 1440×900.
- The uniform block maps read as wireframes.

**Cut / deferred:** Hinglish copy; the urgent-medicine scenario; real WhatsApp; the support console and agent (Phase 3).
