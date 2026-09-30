# WISMO complaint mining: Smytten vs Swish vs Zomato

_Generated 2026-09-30 by `python -m wismo_mining compare` · taxonomy v2 · per-brand detail in [wismo-smytten.md](wismo-smytten.md), [wismo-swish.md](wismo-swish.md), [wismo-zomato.md](wismo-zomato.md)_

## Headline numbers

| Brand | Delivery | App reviews (all ratings) | WISMO share (95% CI) | 1–2★ reviews | WISMO share of 1–2★ | Complaint posts | WISMO share |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Smytten | courier | 5,450 | 6.1% (5.5–6.7) | 4,848 | 24.7% (23.5–26.0) | 216 | 34.3% |
| Swish | hyperlocal | 2,734 | 5.6% (4.8–6.6) | 1,311 | 10.4% (8.8–12.1) | – | – |
| Zomato | hyperlocal | 5,500 | 3.6% (3.1–4.1) | 4,682 | 12.3% (11.4–13.3) | 61 | 24.6% |

## The eight hypotheses, measured

Cell = share of WISMO app reviews (all-ratings sample) that mention the pain · in brackets the share among 1–2★ WISMO reviews. Verdicts use the brand's all-ratings share: strong ≥15%, moderate 5–15%, weak 2–5%, rare <2%.

| Hypothesis | Smytten (n=330/1199) | Swish (n=154/136) | Zomato (n=196/577) |
| :--- | ---: | ---: | ---: |
| Poor or vague "where is my order" answers | 5.2% (4.6%) · moderate | 5.2% (5.9%) · moderate | 3.1% (4.0%) · weak |
| Trackers stale, vague or wrong | 4.8% (5.1%) · weak | 2.6% (2.2%) · weak | 1.0% (0.7%) · rare |
| Rider stuck / not moving | 0.9% (0.4%) · rare | 11.7% (13.2%) · moderate | 2.0% (1.7%) · weak |
| Traffic delays and ETA slips | 47.3% (35.4%) · strong | 71.4% (70.6%) · strong | 76.0% (74.0%) · strong |
| Multiple / batched orders | 3.6% (2.6%) · weak | 0.6% (0.7%) · rare | 7.7% (6.6%) · moderate |
| Bad address resolution | 1.2% (1.8%) · rare | 5.8% (4.4%) · moderate | 2.6% (4.9%) · weak |
| "Delivered" but not received | 13.3% (29.0%) · moderate | 6.5% (7.4%) · moderate | 7.1% (8.7%) · moderate |
| Support loops / unreachable | 23.3% (30.1%) · strong | 16.2% (18.4%) · strong | 16.8% (19.6%) · strong |

## Category mix among WISMO reviews

Cell = % of WISMO reviews (all-ratings sample) / % of all 1–2★ reviews.

| Category | Group | Smytten | Swish | Zomato |
| :--- | :--- | ---: | ---: | ---: |
| Tracker stale, vague or wrong | WISMO | 4.8% / 1.3% | 2.6% / 0.2% | 1.0% / 0.1% |
| ETA slip / late delivery | WISMO | 47.3% / 8.7% | 69.5% / 7.2% | 74.0% / 9.0% |
| Rider / parcel stuck, not moving | WISMO | 0.9% / 0.1% | 11.7% / 1.4% | 2.0% / 0.2% |
| Traffic / weather / demand excuse | WISMO | 0.3% / 0.1% | 4.5% / 0.4% | 2.6% / 0.2% |
| Multiple / batched orders | WISMO | 3.6% / 0.6% | 0.6% / 0.1% | 7.7% / 0.8% |
| Address / location resolution | WISMO | 1.2% / 0.4% | 5.8% / 0.5% | 2.6% / 0.6% |
| Marked delivered, not received | WISMO | 13.3% / 7.2% | 6.5% / 0.8% | 7.1% / 1.1% |
| Not received / where is my order | WISMO | 46.1% / 9.4% | 14.3% / 1.6% | 13.3% / 1.6% |
| No proactive update | cross-cutting | 3.3% / 2.1% | 2.6% / 1.1% | 0.5% / 0.4% |
| Support unreachable / bot loop | cross-cutting | 23.3% / 16.2% | 16.2% / 8.2% | 16.8% / 10.4% |
| Vague / scripted answer | cross-cutting | 5.2% / 2.0% | 5.2% / 1.7% | 3.1% / 1.3% |
| Partial / missing item | adjacent | 4.5% / 4.0% | 1.3% / 1.5% | 3.6% / 1.6% |
| Rider behaviour / asked to pick up | adjacent | 0.3% / 0.5% | 5.2% / 1.7% | 1.5% / 1.1% |
| Cancelled by platform / restaurant | adjacent | 3.3% / 2.7% | 6.5% / 2.4% | 4.1% / 1.5% |
| Refund stuck / not received | adjacent | 8.8% / 6.8% | 2.6% / 2.3% | 5.1% / 2.8% |

## Where WISMO and support failure meet

| Brand | WISMO pool | …also support failure | Delivered-not-received → support failure | Late → support failure | …also 'nobody told me' |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Smytten | 1313 | 31.0% | 42.7% (n=358) | 27.5% (n=469) | 4.3% |
| Swish | 154 | 19.5% | 20.0% (n=10) | 14.0% (n=107) | 2.6% |
| Zomato | 610 | 22.3% | 39.6% (n=53) | 19.4% (n=444) | 0.8% |

Pool = WISMO app reviews from every pull plus WISMO complaint posts. Support failure = unreachable/bot loop or vague/scripted answer.

## How far to trust the classifier

| Brand | WISMO-flag precision, v1 (sample A) | WISMO-flag precision, v2 (holdout B) | Holdout: true WISMO among 1–2★ rows called non-WISMO |
| :--- | ---: | ---: | ---: |
| Smytten | 98% (44/45) | 87% (26/30) | 3/10 |
| Swish | 73% (33/45) | 87% (26/30) | 0/10 |
| Zomato | 98% (44/45) | 93% (28/30) | 1/10 |

One round of pattern fixes (v1 → v2) was made on sample A; sample B was drawn afterwards and never used for tuning. Per-category precision and recall are in each brand report (section 8).

## Findings (computed)

- WISMO is a minority of all reviews but a large block of angry ones: Smytten 6.1% of all vs 24.7% of 1–2★; Swish 5.6% of all vs 10.4% of 1–2★; Zomato 3.6% of all vs 12.3% of 1–2★.
- Top WISMO issue among WISMO reviews — Smytten: eta slip / late delivery (47.3%), then not received / where is my order (46.1%); Swish: eta slip / late delivery (69.5%), then not received / where is my order (14.3%); Zomato: eta slip / late delivery (74.0%), then not received / where is my order (13.3%).
- Hypotheses at ≥15% of WISMO reviews for every brand: Traffic delays and ETA slips; Support loops / unreachable.
- Hypotheses under 5% of WISMO reviews for every brand (little explicit evidence in review text, which does not mean the problem is absent): Trackers stale, vague or wrong (holdout recall 2/10, so partly a detection gap).
- Biggest brand gap — Traffic delays and ETA slips: Zomato 76% vs Smytten 47% of WISMO reviews.
- Biggest brand gap — Rider stuck / not moving: Swish 12% vs Smytten 1% of WISMO reviews.
- Biggest brand gap — Support loops / unreachable: Smytten 23% vs Swish 16% of WISMO reviews.
- Share of WISMO complaints (all pulls + complaint posts) that also describe a support failure: Smytten 31.0%, Swish 19.5%, Zomato 22.3%.

## Data coverage

| Source | Smytten | Swish | Zomato |
| :--- | :--- | :--- | :--- |
| google_play | 8,327 (2022-05 → 2026-09) | 2,315 (2024-07 → 2026-09) | 8,377 (2026-06 → 2026-09) |
| app_store | 450 (2025-04 → 2026-09) | 419 (2024-09 → 2026-09) | 500 (2026-09 → 2026-09) |
| consumercomplaints | 216 (2023-01 → 2026-08) | not_configured | 61 (2023-02 → 2026-08) |
| manual_research | 196 (2019-09 → 2026-09) | – | – |
| trustpilot | skipped | skipped | skipped |
| mouthshut | skipped | not_configured | skipped |
| reddit | skipped | skipped | skipped |

Not collected: **trustpilot**: robots.txt: 'User-agent: * / Disallow: /' (only named search bots allowed); pages also return HTTP 403 to non-browser clients; **mouthshut**: robots.txt disallows ClaudeBot site-wide (and Content-Signal ai-train=no); not fetched; **reddit**: robots.txt disallows this path (Disallow: / for all agents); API requires OAuth login.
No brand page: consumercomplaints (Swish); mouthshut (Swish).

## Read this before quoting a number

- App-store reviews over-represent angry and delighted shoppers; the WISMO share of reviews is not the share of tickets. It is a ranking of what hurts enough to be written down in public.
- Windows are not aligned. The all-ratings Google Play sample covers: Smytten 244 days (2026-01-28 → 2026-09-28); Swish 805 days (2024-07-17 → 2026-09-29); Zomato 10 days (2026-09-20 → 2026-09-29). Treat cross-brand gaps of a few points as noise.
- Categories come from a rule-based classifier with hand-checked precision (above, and section 8 of each brand report). Recall is only partly measured and is weakest for tracker and support complaints, so those shares are undercounts.
- Smytten: Courier model: 'late' means days, and 'not received' usually means a parcel stuck with the courier, so these two categories overlap more than for food apps.
- Swish: Many Swish 1–2★ reviews are about price, serviceability and the 'experiencing surge' / 'kitchen on break' can't-order message. That dilutes its WISMO share; 'surge' counts as a delay excuse only when tied to a delay.
- Swish: Swish's Play review history is small (~2,300 text reviews since July 2024), so its all-ratings sample is the app's whole life, not a recent window.
- Zomato: consumercomplaints.in lists full complaints first and short posts after them; paging stopped once full complaints fell before 2023, so Zomato's short posts were not reached.
- Zomato: Zomato's review volume means the capped Play pulls cover ~10 days (all ratings) and ~3 weeks (1★): a snapshot, not a trend.
