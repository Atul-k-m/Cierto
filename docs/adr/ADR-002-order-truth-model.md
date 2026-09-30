# ADR-002: Order truth model (event log, claimed vs verified, commitments)

**Status:** Proposed
**Date:** 2026-09-29
**Deciders:** Ishrajesh (owner)

## Context

The dataset's worst failures are state problems, not missing data:

- 35 of 93 complaints: a courier's "Delivered" was treated as fact (no OTP, no call).
- VX-07: cancelled at the doorstep, but the app still said "Shipped", so the refund never started.
- VX-02: tracking dates conflicted across sites.
- IC-213013: the ETA was extended daily, then the order was cancelled as "user-cancelled".

Quick commerce shows the same pattern in minutes: Instamart marked an order delivered at 05:36 with no OTP; Swish's complaint window starts from a stale "delivered" tap. Any design that stores one `status` column copied from the loudest source reproduces these failures.

## Decision

1. **Append-only event log.** Every fact is an immutable event with `what` (order/shipment), `when` (`occurred_at`, `received_at`), `where`, `why` (status, substatus) and **`asserted_by`** (merchant system, carrier, rider app, payment gateway, customer, engine). Current state is a projection.
2. **Two-level status taxonomy** (AfterShip-style ~9 statuses / ~50 substatuses) **unioned with ONDC fulfilment states** (Searching-for-Agent, Agent-assigned, Order-picked-up, Out-for-delivery, Order-delivered, Delivery-failed, Customer-not-found, RTO-Initiated/Delivered/Disposed, At-destination-hub). The raw source code and message are always kept.
3. **Per-source states plus a reconciled state.** The projection keeps `merchant_state`, `carrier_state`, `customer_claim` and a `reconciled_state` with a `conflict` flag. A conflict (e.g. carrier RTO while merchant says Shipped) is itself an exception.
4. **Proof state on delivery:** `none` → `claimed` (source says delivered) → `verified` (OTP / photo within geofence / customer confirmed / dispute window lapsed) or `disputed`. The UI never shows `claimed` as a green tick.
5. **Commitments are first-class objects:** promised ETA *as shown to the customer at checkout*, revised ETAs (old values kept), refund-by dates, claim windows, and statutory clocks (48-hour acknowledgement and 30-day resolution; RBI T+1/T+5; ONDC IGM 2h/24h). Every commitment owns a timer.
6. **Forward and return legs are separate shipments under one order.** ONDC's own spec bug showed that conflating them fails silently.

## Options considered

| | Single status column | Carrier-mirroring tracker | **Event log + projection (chosen)** |
|---|---|---|---|
| Complexity | Low | Low | Medium |
| Catches "marked delivered, not received" | No | No | Yes: proof state |
| Explains a dispute | No | Partly | Yes: full provenance |
| Reconciles merchant vs carrier | No | No | Yes: conflict flag |
| Replay for demos and evals | No | No | Yes: replay the log on a virtual clock |

## Consequences

- **Easier:** detectors are pure functions over the projection; demos and evaluations replay real complaint scenarios deterministically; disputes show their evidence.
- **Harder:** projection code must be idempotent and handle out-of-order events (`occurred_at` ≠ `received_at`); storage grows with events (mitigated by per-tenant retention TTLs).
- **Revisit:** snapshotting projections if logs per order get long (unlikely below hundreds of events).
