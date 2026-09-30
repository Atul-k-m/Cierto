# Roadmap — phases and small iterations

*Draft v0.1, 2026-09-29. Each iteration ends with something runnable and a one-paragraph decision note (what was decided, what was cut, why). Those notes become the pitch write-up.*

## Phase 0 — Understand and decide ✅

Research (7 areas), complaint dataset export, product brief, design brief, architecture and ADRs.
**Exit:** `docs/00`–`03`, `docs/adr/`, `PRODUCT.md`, `data/complaints.json`.

## Phase 1 — The engine proves it can see failures (local only) ✅

| Iteration | Build | Done when |
|---|---|---|
| 1.1 | Repo scaffold; canonical event schema; event log (Postgres in Docker) | Events from a hand-written scenario persist and replay |
| 1.2 | Projector: per-source states, reconciled state, conflict flag, **proof state** | Unit tests for VX-07 (doorstep cancel vs "Shipped") and IC-213360 (delivered, wrong phone) pass |
| 1.3 | Commitments + scheduler port on a **virtual clock** | A 7-day parcel scenario replays in seconds with timers firing in order |
| 1.4 | Top 8 detectors + replay harness over complaint-derived scenarios | **First coverage report:** "caught X of Y, median lead time Z, false alarms W" |

**Phase exit:** the coverage report exists and its misses are explained. This is the first number in the pitch.

**Result (2026-09-29):** `docs/reports/phase1-coverage.md`: 48/80 flagged from data alone, 79/80 before the public complaint, 0/400 false alarms (23% under a 96 h carrier-silence stress test), 1 explained miss. Details in `docs/decision-log.md`.

## Phase 2 — The shopper sees the truth (widget + three host replicas) ✅

| Iteration | Build | Done when |
|---|---|---|
| 2.1 | `<wismo-order>` Web Component, token theming; **Smytten replica** with *My Orders, told truthfully* | Scenario 1 (delivered, not received) and 2 (late/stuck) render correctly in the Smytten look |
| 2.2 | **Zomato replica** with the smart card in the tracking screen | Card walks on the way → did you get it? → case → refund |
| 2.3 | **Swish replica** with the after-delivered screen | 10-minute "delivered, no food" with a report window from verified handover |
| 2.4 | **Demo launcher** in the cloud-edge platform style: three phones side by side, scenario picker, time slider | The signature moment: one trigger, three apps tell the truth at once |

**Phase exit:** the hands-on demo runs locally end to end; accessibility pass (WCAG 2.1 AA) on the widget.

**Result (2026-09-29):** demo runs locally (`README.md`); engine API + view model added as 2.0; finish review **ship**; `DESIGN.md` recorded. Details in `docs/decision-log.md`.

## Phase 3 — Support that can act

| Iteration | Build | Done when |
|---|---|---|
| 3.1 | Cases (IGM-shaped): IDs, holders, 48h/30d clocks, closure rules | Anti-pattern tests pass (no silent close, ID always visible) |
| 3.2 | Router + templated status answers (English + Hinglish) | Status questions never hit the agent |
| 3.3 | Exception agent (≤10 tools) + approval queue + **support console** (platform style) | Reship/refund proposals wait for human approval with evidence attached |
| 3.4 | Agent evaluation harness (simulated users from complaints, ≥ 20% Hinglish, pass^3) + WhatsApp simulator | **Second pitch number:** verified resolution rate, reported separately from automation rate |
| 3.5 | Refund sub-timeline (scenario 3) with RBI/UPI escalation routes | Overdue refund produces a correct escalation pack |

## Phase 4 — It runs for real (cloud, ops, first live adapter)

| Iteration | Build | Done when |
|---|---|---|
| 4.1 | AWS Mumbai deploy via SAM (ADR-001 adapters); contract tests on both adapter sets | Same scenarios pass locally and in the cloud |
| 4.2 | **Ops dashboard** + incident detector; December 2025 replay | Incident opens within the first simulated days of the spike |
| 4.3 | First live adapter: Shiprocket (or iThink) with real test shipments | A real parcel's scans drive the widget |
| 4.4 | MCP server (OAuth, tenant-scoped) | Claude can answer "what really happened to order X?" from the engine |

## Phase 5 — Reach and pitch

| Iteration | Build |
|---|---|
| 5.1 | Swiggy Builders Club spike: does any tool return order status? If yes, a real-app demo |
| 5.2 | Shopify app (fulfilment webhooks) as the distributable integration |
| 5.3 | Consumer-side ingestion: forwarded order emails / screenshot → state |
| 5.4 | Urgent-order (medicine) scenario — *deferred by the owner; host to be chosen* |
| 5.5 | Pitch pack: 1-page write-up, architecture one-pager, 3-minute demo video, decision notes |

## Later (not planned)

ONDC participation and IGM as the external case protocol (needs a registered entity); per-tenant breach-prediction model; regional languages.
