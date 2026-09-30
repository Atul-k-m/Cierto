# WISMO complaint mining: Swish

_10-minute food delivery (Bengaluru) · delivery model: hyperlocal · generated 2026-09-30 by `python -m wismo_mining report --brand swish` · taxonomy v2_

WISMO = any shopper complaint about order status, location, ETA, delay, a missing parcel or a date change. Numbers come from a deterministic keyword/regex classifier (`research/wismo_mining/taxonomy.yaml`); every label stores the phrase that triggered it. Categories are multi-label, so shares do not add up to 100%.

## Headline

- **5.6%** of app-store reviews (all ratings, n=2,734) are WISMO-related (95% CI 4.8–6.6%).
- Among **1–2★** app reviews (n=1,311) the share is **10.4%**.
- Largest WISMO issues among WISMO reviews: eta slip / late delivery (69.5%), not received / where is my order (14.3%), rider / parcel stuck, not moving (11.7%).
- 20.7% of WISMO app reviews (all pulls) also report a support failure (unreachable, bot loop or a vague/scripted answer).
- Classifier check on a fresh hand-labelled holdout (n=40): WISMO-flag precision 87% (26/30); 0 of 10 sampled 1–2★/complaint rows it called non-WISMO were in fact WISMO, so WISMO shares are lower bounds (section 8).

## 1. What was collected

| Source | Status | Kind | Rows | Date range | 1–2★ | WISMO | Detail |
| :--- | :--- | :--- | ---: | :--- | ---: | ---: | :--- |
| google_play | ok | app_review | 2,315 | 2024-07-17 → 2026-09-29 | 1,056 | 102 | app_id=com.swishapp, lang=en, country=in; pulls: newest=2315, low_1=976, low_2=80 |
| app_store | ok | app_review | 419 | 2024-09-03 → 2026-09-27 | 255 | 52 | app_id=6504881715, storefront=in, pages with data=9, feed last page=9 |
| consumercomplaints | not_configured | – | 0 | – | – | 0 | no page for this brand on this source |
| trustpilot | skipped | – | 0 | – | – | 0 | robots.txt: 'User-agent: * / Disallow: /' (only named search bots allowed); pages also return HTTP 403 to non-browser clients |
| mouthshut | not_configured | – | 0 | – | – | 0 | no page for this brand on this source |
| reddit | skipped | – | 0 | – | – | 0 | robots.txt disallows this path (Disallow: / for all agents); API requires OAuth login |

Google Play windows: all-ratings sample 2024-07-17 → 2026-09-29; 1★ complete from 2024-07-17; 2★ complete from 2024-07-17.
Detected language of app reviews: en 2,710, hi-Latn 24 (Play pulled with `lang=en`; `hi-Latn` = romanised Hindi/Hinglish).

## 2. How much of the review stream is WISMO?

| Sample | n | WISMO share (95% CI) |
| :--- | ---: | ---: |
| All ratings (unbiased app sample) | 2,734 | 5.6% (4.8–6.6) |
| 1★ | 1,209 | 10.5% (8.9–12.4) |
| 2★ | 102 | 8.8% (4.7–15.9) |
| 3★ | 75 | 5.3% (2.1–12.9) |
| 4–5★ | 1,348 | 1.0% (0.6–1.7) |
| … google_play only (all ratings) | 2,315 | 4.4% (3.6–5.3) |
| … app_store only (all ratings) | 419 | 12.4% (9.6–15.9) |

1★ and 2★ rows include the extra low-star pulls (longer window); 3★ and 4–5★ come from the all-ratings sample only.

## 3. Hypothesis scorecard

Share of WISMO reviews (all-ratings app sample) that mention each hypothesised pain, with the same measure among all 1–2★ reviews and complaint-board posts. Verdict thresholds (share of WISMO reviews): strong ≥15%, moderate 5–15%, weak 2–5%, rare <2%.

| Hypothesis | Categories | % of WISMO reviews (n=154) | % of 1–2★ WISMO (n=136) | % of all 1–2★ (n=1311) | % of complaint posts (n=0) | Verdict | Classifier check (holdout) |
| :--- | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| Poor or vague "where is my order" answers | `vague_support_answer` | 5.2% (3–10) | 5.9% | 1.7% | – | moderate | P 100% (1/1) · R 100% (1/1) |
| Trackers stale, vague or wrong | `tracking_stale_wrong` | 2.6% (1–6) | 2.2% | 0.2% | – | weak | P – · R 0% (0/3) |
| Rider stuck / not moving | `rider_stuck` | 11.7% (8–18) | 13.2% | 1.4% | – | moderate | P 100% (5/5) · R 83% (5/6) |
| Traffic delays and ETA slips | `eta_slip_late`, `traffic_weather_excuse` | 71.4% (64–78) | 70.6% | 7.3% | – | strong | P 86% (18/21) · R 90% (18/20) |
| Multiple / batched orders | `multiple_batched_orders` | 0.6% (0–4) | 0.7% | 0.1% | – | rare | – |
| Bad address resolution | `address_location` | 5.8% (3–11) | 4.4% | 0.5% | – | moderate | P 50% (1/2) · R 100% (1/1) |
| "Delivered" but not received | `delivered_not_received` | 6.5% (4–12) | 7.4% | 0.8% | – | moderate | P 100% (2/2) · R 67% (2/3) |
| Support loops / unreachable | `support_unreachable_loop` | 16.2% (11–23) | 18.4% | 8.2% | – | strong | P 100% (5/5) · R 83% (5/6) |

Classifier check = precision (P) and recall (R) of the hypothesis categories on the fresh hand-labelled holdout (section 8). Low recall means the share is an undercount; tiny n means the check itself is rough.

## 4. Every category

| Category | Group | % all reviews (n=2,734) | % WISMO reviews (n=154) | % 1–2★ (n=1,311) | % complaint posts (n=0) | % curated (n=0) | Holdout precision · recall |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| ETA slip / late delivery | WISMO | 3.9% | 69.5% | 7.2% | – | – | P 86% (18/21) · R 90% (18/20) |
| Not received / where is my order | WISMO | 0.8% | 14.3% | 1.6% | – | – | P 33% (1/3) · R 100% (1/1) |
| Rider / parcel stuck, not moving | WISMO | 0.7% | 11.7% | 1.4% | – | – | P 100% (5/5) · R 83% (5/6) |
| Marked delivered, not received | WISMO | 0.4% | 6.5% | 0.8% | – | – | P 100% (2/2) · R 67% (2/3) |
| Address / location resolution | WISMO | 0.3% | 5.8% | 0.5% | – | – | P 50% (1/2) · R 100% (1/1) |
| Traffic / weather / demand excuse | WISMO | 0.3% | 4.5% | 0.4% | – | – | P 100% (5/5) · R 100% (5/5) (tuned sample) |
| Tracker stale, vague or wrong | WISMO | 0.1% | 2.6% | 0.2% | – | – | P – · R 0% (0/3) |
| Multiple / batched orders | WISMO | 0.0% | 0.6% | 0.1% | – | – | – |
| Support unreachable / bot loop | cross-cutting | 4.1% | 16.2% | 8.2% | – | – | P 100% (5/5) · R 83% (5/6) |
| Cancelled by platform / restaurant | adjacent | 1.2% | 6.5% | 2.4% | – | – | P 0% (0/1) · R – |
| Vague / scripted answer | cross-cutting | 0.8% | 5.2% | 1.7% | – | – | P 100% (1/1) · R 100% (1/1) |
| Rider behaviour / asked to pick up | adjacent | 0.9% | 5.2% | 1.7% | – | – | P – · R 0% (0/1) |
| No proactive update | cross-cutting | 0.5% | 2.6% | 1.1% | – | – | P 100% (2/2) · R 100% (2/2) (tuned sample) |
| Refund stuck / not received | adjacent | 1.1% | 2.6% | 2.3% | – | – | P 100% (1/1) · R 100% (1/1) |
| Partial / missing item | adjacent | 0.8% | 1.3% | 1.5% | – | – | P – · R 0% (0/1) |
| Other / non-WISMO | derived | 94.4% | – | 89.6% | – | – | – |

Cross-cutting and adjacent categories do not make a review WISMO on their own; they are counted so their overlap with WISMO can be measured (section 6).

## 5. Trend by month (Google Play)

All-ratings sample (the newest-reviews pull):

| Month | Reviews | WISMO share |  |
| :--- | ---: | ---: | ---: |
| 2024-07 (partial) | 1 | 0.0% | low n |
| 2024-08 | 16 | 0.0% | low n |
| 2024-09 | 10 | 0.0% | low n |
| 2024-10 | 10 | 10.0% | low n |
| 2024-11 | 64 | 6.2% |  |
| 2024-12 | 42 | 4.8% |  |
| 2025-01 | 44 | 2.3% |  |
| 2025-02 | 57 | 1.8% |  |
| 2025-03 | 40 | 5.0% |  |
| 2025-04 | 50 | 4.0% |  |
| 2025-05 | 57 | 1.8% |  |
| 2025-06 | 44 | 2.3% |  |
| 2025-07 | 62 | 11.3% |  |
| 2025-08 | 51 | 3.9% |  |
| 2025-09 | 53 | 0.0% |  |
| 2025-10 | 38 | 2.6% |  |
| 2025-11 | 66 | 6.1% |  |
| 2025-12 | 84 | 1.2% |  |
| 2026-01 | 62 | 6.5% |  |
| 2026-02 | 86 | 4.7% |  |
| 2026-03 | 122 | 6.6% |  |
| 2026-04 | 135 | 10.4% |  |
| 2026-05 | 190 | 5.3% |  |
| 2026-06 | 162 | 1.2% |  |
| 2026-07 | 241 | 3.3% |  |
| 2026-08 | 276 | 5.1% |  |
| 2026-09 | 252 | 3.2% |  |

1–2★ reviews, months where both star levels are fully covered:

| Month | 1–2★ reviews | WISMO share | ETA slip / late delivery | Not received / where is my order | Rider / parcel stuck, not moving | Marked delivered, not received |  |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-08 | 6 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | low n |
| 2024-09 | 2 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | low n |
| 2024-10 | 8 | 12.5% | 12.5% | 0.0% | 0.0% | 12.5% | low n |
| 2024-11 | 20 | 20.0% | 5.0% | 5.0% | 0.0% | 10.0% | low n |
| 2024-12 | 25 | 8.0% | 8.0% | 0.0% | 0.0% | 0.0% | low n |
| 2025-01 | 23 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | low n |
| 2025-02 | 29 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | low n |
| 2025-03 | 27 | 7.4% | 0.0% | 3.7% | 0.0% | 0.0% | low n |
| 2025-04 | 25 | 8.0% | 8.0% | 0.0% | 0.0% | 0.0% | low n |
| 2025-05 | 33 | 3.0% | 3.0% | 0.0% | 0.0% | 0.0% |  |
| 2025-06 | 21 | 4.8% | 0.0% | 4.8% | 0.0% | 0.0% | low n |
| 2025-07 | 29 | 13.8% | 10.3% | 6.9% | 0.0% | 0.0% | low n |
| 2025-08 | 31 | 6.5% | 3.2% | 3.2% | 0.0% | 0.0% |  |
| 2025-09 | 29 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | low n |
| 2025-10 | 20 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | low n |
| 2025-11 | 32 | 12.5% | 12.5% | 0.0% | 3.1% | 0.0% |  |
| 2025-12 | 28 | 3.6% | 0.0% | 0.0% | 3.6% | 0.0% | low n |
| 2026-01 | 24 | 16.7% | 16.7% | 0.0% | 0.0% | 0.0% | low n |
| 2026-02 | 46 | 6.5% | 6.5% | 0.0% | 2.2% | 0.0% |  |
| 2026-03 | 69 | 8.7% | 8.7% | 1.4% | 1.4% | 0.0% |  |
| 2026-04 | 81 | 14.8% | 9.9% | 2.5% | 3.7% | 0.0% |  |
| 2026-05 | 78 | 12.8% | 7.7% | 1.3% | 1.3% | 1.3% |  |
| 2026-06 | 56 | 3.6% | 3.6% | 0.0% | 0.0% | 0.0% |  |
| 2026-07 | 90 | 8.9% | 6.7% | 1.1% | 0.0% | 0.0% |  |
| 2026-08 | 119 | 9.2% | 4.2% | 1.7% | 0.0% | 1.7% |  |
| 2026-09 | 105 | 6.7% | 3.8% | 2.9% | 1.0% | 0.0% |  |

The current month is to date. Month-to-month moves under ~5 points on n<200 are within noise.

## 6. Co-occurrence

Pool: all WISMO app reviews (any pull) plus WISMO complaint posts, n=154. P(B|A) = share of reviews with A that also mention B; lift >1 means they travel together more than chance.

| A → B | n(A) | n(A∧B) | P(B|A) | P(B) baseline | Lift |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Marked delivered, not received → Support unreachable / bot loop | 10 | 2 | 20.0% | 16.2% | 1.2× |
| Not received / where is my order → Support unreachable / bot loop | 22 | 9 | 40.9% | 16.2% | 2.5× |
| ETA slip / late delivery → Support unreachable / bot loop | 107 | 11 | 10.3% | 16.2% | 0.6× |
| ETA slip / late delivery → Vague / scripted answer | 107 | 5 | 4.7% | 5.2% | 0.9× |
| ETA slip / late delivery → Cancelled by platform / restaurant | 107 | 9 | 8.4% | 6.5% | 1.3× |
| ETA slip / late delivery → No proactive update | 107 | 3 | 2.8% | 2.6% | 1.1× |
| Not received / where is my order → Refund stuck / not received | 22 | 1 | 4.5% | 2.6% | 1.8× |
| Multiple / batched orders → ETA slip / late delivery | 1 | 1 | 100.0% | 69.5% | 1.4× |
| Rider / parcel stuck, not moving → ETA slip / late delivery | 18 | 12 | 66.7% | 69.5% | 1.0× |
| Tracker stale, vague or wrong → ETA slip / late delivery | 4 | 1 | 25.0% | 69.5% | 0.4× |
| Address / location resolution → Rider behaviour / asked to pick up | 9 | 1 | 11.1% | 5.2% | 2.1× |
| Traffic / weather / demand excuse → ETA slip / late delivery | 7 | 4 | 57.1% | 69.5% | 0.8× |

Most frequent pairs overall:

| Category A | Category B | Both | Lift |
| :--- | :--- | ---: | ---: |
| ETA slip / late delivery | Rider / parcel stuck, not moving | 12 | 1.0× |
| ETA slip / late delivery | Support unreachable / bot loop | 11 | 0.6× |
| Not received / where is my order | Support unreachable / bot loop | 9 | 2.5× |
| Cancelled by platform / restaurant | ETA slip / late delivery | 9 | 1.3× |
| ETA slip / late delivery | Rider behaviour / asked to pick up | 6 | 1.1× |
| ETA slip / late delivery | Not received / where is my order | 5 | 0.3× |
| ETA slip / late delivery | Vague / scripted answer | 5 | 0.9× |
| Rider / parcel stuck, not moving | Support unreachable / bot loop | 4 | 1.4× |
| ETA slip / late delivery | Traffic / weather / demand excuse | 4 | 0.8× |
| Rider / parcel stuck, not moving | Traffic / weather / demand excuse | 3 | 3.7× |

## 7. What shoppers say (verbatim)

Excerpts are verbatim (line breaks collapsed); `…` marks a cut, and long numbers/emails are masked. Hand-checked rows are shown first, and rows the hand-check rejected for a category are never shown; the rest are a deterministic pseudo-random pick, so an occasional misfire can still appear. App Store links go to the app's review list (Apple has no per-review permalink); the id identifies the review.

### ETA slip / late delivery

> first time user, ordered for my kid, waited 50 minutes, no movement, they seemed more than happy to cancel in a giffy. looks like they never had the intention to deliver the order in the first place. not ordering ever again
>
> — 1★ · google_play · 2026-05-23 · [gp:a911ee78-513a-4988-9bc2-11d73cb7143e](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=a911ee78-513a-4988-9bc2-11d73cb7143e) · ✓ hand-checked

> Worst app. This is the worst app that you can use to order your food. I have placed order twice on the app every time. My food is delivered after an hour on top of that. The app reflects fake locations of the driver making you think that your order has reached your location when the rider is completely at a different location. …
>
> — 1★ · app_store · 2026-05-06 · [as:14034858563](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> very bad experience with timely delivery, shows 10 to 15 minutes but my order was delayed beyond an hour, without letting me cancel it
>
> — 1★ · google_play · 2026-09-13 · [gp:bb1d8ead-ea20-4903-b7da-2bb0de0de188](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=bb1d8ead-ea20-4903-b7da-2bb0de0de188) · ✓ hand-checked

> Took 50 mins to deliver a small order. I order Vadapav and chai and they took 50 mins to deliver it to my house. They don’t respect other people’s time. Not even a single order I placed has been delivered on time. All of their orders take 25mins or more. It’s an absolute scam application
>
> — 1★ · app_store · 2026-08-22 · [as:14461377932](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

### Not received / where is my order

> ordered at 8pm, now its 10...till order not reached...no customer support..! worst service
>
> — 1★ · google_play · 2025-03-22 · [gp:a2d24a9b-7a14-4a83-87f9-5e68c3067b59](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=a2d24a9b-7a14-4a83-87f9-5e68c3067b59) · ✓ hand-checked

> Not delivered on time. I will order my food my order is not delivered by hour
>
> — 1★ · app_store · 2026-08-05 · [as:14393671916](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> Poor experience on this app... Food has not been delivered even in 90 mins. Food has been prepared but there is no delivery partner. There is no option to cancel the order as well.
>
> — 1★ · google_play · 2026-03-25 · [gp:41965892-1863-4642-be72-35f511531f3d](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=41965892-1863-4642-be72-35f511531f3d) · ✓ hand-checked

> Scam Title. The "10-Min Delivery" is a blatant lie they tell the customers just to get more orders. I have never received a single order before 20 minutes. And apparently, you can lie about anything, no one can complain about this
>
> — 1★ · app_store · 2026-09-18 · [as:14567013897](https://apps.apple.com/in/app/id6504881715?see-all=reviews)

### Rider / parcel stuck, not moving

> They advertise 10 mins delivery. I placed an order, Waited for 30 mins, no delivery partner was assigned and then upon my request, they cancelled the order. Why advertise something which you can't even fulfill. Just a marketing gimmick. Packing already made food and making fool of people
>
> — 1★ · google_play · 2026-04-07 · [gp:a405fedb-1c58-4528-a30c-bd6a7d278077](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=a405fedb-1c58-4528-a30c-bd6a7d278077) · ✓ hand-checked

> … There was a slight drizzle due to which the delivery guy said that the food will be delayed which is understandable. But for the past half an hour the delivery guy is not even moving from the kitchen. He has my food that I have already paid for and he straight up said no to delivering my food even though the rain has stopped right now. …
>
> — 1★ · app_store · 2026-05-26 · [as:14108816451](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> Poor experience on this app... Food has not been delivered even in 90 mins. Food has been prepared but there is no delivery partner. There is no option to cancel the order as well.
>
> — 1★ · google_play · 2026-03-25 · [gp:41965892-1863-4642-be72-35f511531f3d](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=41965892-1863-4642-be72-35f511531f3d) · ✓ hand-checked

> Poor Delivery Experience. The Swish kitchen is just 0.9 km from my home. Whenever I place an order, it will show delivery in 10 min, but after preparing it, it will take too much time to assign a delivery partner. I think you guys need to improve on riders and delivery timing. …
>
> — 1★ · app_store · 2026-04-06 · [as:13930848020](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

### Marked delivered, not received

> Pathetic app....I have ordered 2 bowls and the delivery guy dropped both of it saying he had a accident.. he even gaved me and went and these guys marked as delivered....at such initial level you guys are cheating... pathetic
>
> — 1★ · google_play · 2024-11-28 · [gp:d7246285-c2f7-450b-bd89-f6d85e4ec45b](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=d7246285-c2f7-450b-bd89-f6d85e4ec45b) · ✓ hand-checked

> Worst customer service ever. I didn’t get item out of my order list so I didn’t accept the order but delivery person marked as delivered and insisted me get help in the app. I contacted customer service and wasted my time as they are asking me to wait for 5-7 days for refund. Such a pathetic service will never order again
>
> — 1★ · app_store · 2026-05-19 · [as:14082691850](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> worst app ever - bunch of frauds never ever use this app - they never deliver the order and mark it as delivered and there is no customer support - money is gone now ! you will be stuck - please avoid this fraud app
>
> — 1★ · google_play · 2026-08-13 · [gp:c0eac127-1fee-4999-8784-2c6ebaf0232f](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=c0eac127-1fee-4999-8784-2c6ebaf0232f)

> Very poor service. Hi, my food was not delivered, but the Swish app shows the order as delivered.
>
> — 1★ · app_store · 2026-07-22 · [as:14333991000](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

### Address / location resolution

> location markers are incorrect
>
> — 1★ · google_play · 2026-04-14 · [gp:549dcea5-aa6d-44a4-956d-5bf6bcaa6035](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=549dcea5-aa6d-44a4-956d-5bf6bcaa6035) · ✓ hand-checked

> Delivery boys are not aware of location and when they cant find they speak like rowdy in Bangalore. Today 1st order i did and disappointed with delivery experience! …
>
> — 1★ · app_store · 2025-04-03 · [as:12498803822](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> i ordered food but they ordered at the wrong location very very bad and no refund got yet
>
> — 1★ · google_play · 2026-08-14 · [gp:02f208bc-e793-4ae9-8da5-b5dae3c2831d](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=02f208bc-e793-4ae9-8da5-b5dae3c2831d) · ✓ hand-checked

> so I tried it. App is horrible. Delivery was even worse for both my orders because of this app issue. they kept going to the wrong building
>
> — 1★ · google_play · 2026-05-28 · [gp:ffdeb6e5-2b52-49dd-ab6e-23e4cf39f224](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=ffdeb6e5-2b52-49dd-ab6e-23e4cf39f224)

### Traffic / weather / demand excuse

> … Makes no sense if I have to wait for 45 mins for my food, I will prefer swiggy zomato then. Defies the complete purpose of 10 minute delivery. Customer experience very weak every-time same automated answers regarding surge of orders. Majority of times while trying to order it shows come back after some time due to surge. …
>
> — 2★ · app_store · 2026-04-08 · [as:13936455024](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> App promises to deliver food under 10 mins but surprisingly it will wait till rain starts and will inform you after 30 mins of placing your order that they won't be able to deliver food "Due to Rain". Stupid Business model and support team, they are only there to waste time and effort.
>
> — 1★ · google_play · 2026-05-26 · [gp:cd02b6ef-c8be-43f9-9a45-8b2d889f13da](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=cd02b6ef-c8be-43f9-9a45-8b2d889f13da) · ✓ hand-checked

> False Promise of 10 mins delivery. They do not have enough delivery partners to make delivery in 10 mins. I placed my order and after 20 mins it still says no delivery partner assigned. Customer care says due to sudden order spike which there was no mention in the app. I cancelled my order and took refund. Uninstalled the app. …
>
> — 1★ · app_store · 2026-04-12 · [as:13949880315](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> … But for the past half an hour the delivery guy is not even moving from the kitchen. He has my food that I have already paid for and he straight up said no to delivering my food even though the rain has stopped right now. The delivery guy as well as the support agent that I was talking to were misbehaving with me the whole time. …
>
> — 1★ · app_store · 2026-05-26 · [as:14108816451](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

### Support unreachable / bot loop (WISMO reviews only)

> They tell 10 min and its been 1 hour i am still waiting. Ordered at 7:33 pm and even after 1 hour no delivery partner assigned customer care is not helping they just repeating the same line again and again
>
> — 1★ · app_store · 2026-05-14 · [as:14063828528](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> No customer service. They delivered the wrong order but when trying to complain no one is there to answer you on their WhatsApp channel. Also, did not get the food in 10minutes.
>
> — 1★ · google_play · 2024-11-28 · [gp:7eff9f0e-626f-4c89-9583-70e3807aea06](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=7eff9f0e-626f-4c89-9583-70e3807aea06) · ✓ hand-checked

> … I understand delivery Bike can breakdown, but the least I expect is that I can see where the Rider actually is. What they show is just a projection of where the Rider would be or should be. Again horrible food quality to and pretty much no support to take care of that.
>
> — 1★ · app_store · 2026-05-06 · [as:14034858563](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> Very poor service and a terrible experience. I placed an order that was never delivered. I contacted customer support and waited over 2 hours with no proper response, no resolution, and no refund. This is completely unacceptable. A platform that fails to deliver orders and ignores customers doesn't deserve trust. …
>
> — 1★ · google_play · 2026-07-12 · [gp:bfb29d6f-973f-48d9-bb67-804f4542f56d](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=bfb29d6f-973f-48d9-bb67-804f4542f56d) · ✓ hand-checked

### Vague / scripted answer (WISMO reviews only)

> … The support agent was named Partha. Horrible experience. He kept apologising and repeating his pre-rehearsed response which didn’t help anyone at all. Just wasted my time. It is 10:30 in the night, all shops are closed and I’m sick (hence I ordered from this god-forsaken app). …
>
> — 1★ · app_store · 2026-05-26 · [as:14108816451](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> This is one of the worst experiences I’ve had with any delivery app. I waited almost 40 minutes and still didn’t receive my order. After all that delay, when I tried to escalate the issue, they simply cancelled the order without any proper explanation. There is clearly no respect for customers’ time. …
>
> — 1★ · google_play · 2026-04-27 · [gp:187272f9-2888-469e-8143-6d33523555b8](https://play.google.com/store/apps/details?id=com.swishapp&reviewId=187272f9-2888-469e-8143-6d33523555b8)

> They tell 10 min and its been 1 hour i am still waiting. Ordered at 7:33 pm and even after 1 hour no delivery partner assigned customer care is not helping they just repeating the same line again and again
>
> — 1★ · app_store · 2026-05-14 · [as:14063828528](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

> … Makes no sense if I have to wait for 45 mins for my food, I will prefer swiggy zomato then. Defies the complete purpose of 10 minute delivery. Customer experience very weak every-time same automated answers regarding surge of orders. Majority of times while trying to order it shows come back after some time due to surge. …
>
> — 2★ · app_store · 2026-04-08 · [as:13936455024](https://apps.apple.com/in/app/id6504881715?see-all=reviews) · ✓ hand-checked

## 8. Classifier validation

Every sampled review was read in full and its true categories recorded (`research/wismo_mining/validation/labels_*.jsonl`, with notes on judgement calls).

- **Sample A** (60 per brand, seeded random): 45 drawn from reviews the v1 classifier called WISMO, 15 from the rest (any rating). Used to fix patterns once (v1 → v2), so v2-on-A is optimistic.
- **Sample B** (40 per brand, drawn after v2 was frozen, never used for tuning): 30 predicted-WISMO, 10 predicted-non-WISMO taken only from 1–2★ reviews and complaint posts, where missed WISMO would hide. **v2 on B is the honest estimate.**

| Run | Labelled | WISMO-flag precision | True WISMO among sampled predicted-non-WISMO |
| :--- | ---: | ---: | ---: |
| v1 on A (before fixes) | 60 | 73% (33/45) | 0/15 |
| v2 on A (tuned) | 60 | 100% (31/31) | 0/15 |
| v2 on B (holdout) | 40 | 87% (26/30) | 0/10 |

| Category | Precision: v1 on A (before fixes) | Precision: v2 on A (tuned) | Precision: v2 on B (holdout) | Recall: v2 on B |
| :--- | ---: | ---: | ---: | ---: |
| ETA slip / late delivery | 90% (19/21) | 100% (24/24) | 86% (18/21) | 90% (18/20) |
| Support unreachable / bot loop | 90% (9/10) | 100% (11/11) | 100% (5/5) | 83% (5/6) |
| Rider / parcel stuck, not moving | 33% (1/3) | 83% (5/6) | 100% (5/5) | 83% (5/6) |
| Not received / where is my order | 38% (3/8) | 100% (3/3) | 33% (1/3) | 100% (1/1) |
| Address / location resolution | 29% (2/7) | 100% (2/2) | 50% (1/2) | 100% (1/1) |
| Marked delivered, not received | 100% (2/2) | 100% (2/2) | 100% (2/2) | 67% (2/3) |
| Vague / scripted answer | 29% (2/7) | 100% (3/3) | 100% (1/1) | 100% (1/1) |
| Refund stuck / not received | 67% (2/3) | 100% (2/2) | 100% (1/1) | 100% (1/1) |
| Cancelled by platform / restaurant | 100% (1/1) | 100% (2/2) | 0% (0/1) | – |
| Traffic / weather / demand excuse | 57% (4/7) | 100% (5/5) | – | – |
| Rider behaviour / asked to pick up | 100% (1/1) | 100% (4/4) | – | 0% (0/1) |
| Tracker stale, vague or wrong | 100% (1/1) | 100% (2/2) | – | 0% (0/3) |
| No proactive update | – | 100% (2/2) | – | – |
| Partial / missing item | – | 100% (1/1) | – | 0% (0/1) |

Small n per category means wide error bars (8/10 is compatible with ~50–95%). Recall on B is measured within a WISMO-enriched sample, so treat it as indicative. Known v2 failure modes seen on the holdout: tracker complaints phrased as 'shows wrong delivery time' / 'time shown is not correct' are missed (tracker share is an undercount); generic 'poor customer support' is not counted as support failure; 'taking too much charges' and 'took forever to refund' can trip the ETA rule; 'rain' as a fee can trip the weather rule.

## 9. Sampling bias and limitations

- **Reviews are not contacts.** App-store reviews are written by a self-selected few, skew to extremes, and are shaped by in-app rating prompts (which inflate 5★). The WISMO share of reviews is not the WISMO share of support tickets or orders; it measures what hurts enough to be written about publicly.
- **Windows differ by source and brand** (section 1). Each Play pull is newest-first and capped, so high-volume apps get short windows. Shares are only comparable across brands as rough levels.
- **Low-star pulls** extend the 1–2★ window; they feed the 1–2★ columns only, never the 'all reviews' denominator.
- **English only on Play** (`lang=en`): Devanagari-script reviews are largely absent; romanised Hindi is included and matched by Hinglish patterns, but coverage of it is thinner.
- **Apple RSS** returns at most 500 most-recent reviews and intermittently returns empty pages; gaps are listed in section 1.
- **Complaint boards are complaint-only by construction**, so their WISMO share is a mix measure, not a rate. Listing excerpts were expanded to full text where the post had its own page.
- **Rule-based classifier.** Precision is estimated from small hand-checked samples (section 8); recall is not fully measured (only the miss rate among sampled 'non-WISMO' rows). Short reviews ('worst app', 'late') carry little signal, and sarcasm or negation outside the handled patterns can slip through. Shares should be read as ±a few points.
- **Duplicates across sources** (for example a curated App Store complaint that is also in the Apple feed) are not reconciled; the curated set is small and never pooled into shares of reviews.
- **Sources not collected:** `consumercomplaints` (not_configured: no page for this brand on this source); `trustpilot` (skipped: robots.txt: 'User-agent: * / Disallow: /' (only named search bots allowed); pages also return HTTP 403 to non-browser clients); `mouthshut` (not_configured: no page for this brand on this source); `reddit` (skipped: robots.txt disallows this path (Disallow: / for all agents); API requires OAuth login).
- **Brand note:** Many Swish 1–2★ reviews are about price, serviceability and the 'experiencing surge' / 'kitchen on break' can't-order message. That dilutes its WISMO share; 'surge' counts as a delay excuse only when tied to a delay.
- **Brand note:** Swish's Play review history is small (~2,300 text reviews since July 2024), so its all-ratings sample is the app's whole life, not a recent window.
