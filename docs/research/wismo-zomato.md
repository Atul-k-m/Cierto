# WISMO complaint mining: Zomato

_Restaurant food delivery · delivery model: hyperlocal · generated 2026-09-30 by `python -m wismo_mining report --brand zomato` · taxonomy v2_

WISMO = any shopper complaint about order status, location, ETA, delay, a missing parcel or a date change. Numbers come from a deterministic keyword/regex classifier (`research/wismo_mining/taxonomy.yaml`); every label stores the phrase that triggered it. Categories are multi-label, so shares do not add up to 100%.

## Headline

- **3.6%** of app-store reviews (all ratings, n=5,500) are WISMO-related (95% CI 3.1–4.1%).
- Among **1–2★** app reviews (n=4,682) the share is **12.3%**.
- Among complaint-board posts (n=61) it is **24.6%**.
- Largest WISMO issues among WISMO reviews: eta slip / late delivery (74.0%), not received / where is my order (13.3%), multiple / batched orders (7.7%).
- 21.7% of WISMO app reviews (all pulls) also report a support failure (unreachable, bot loop or a vague/scripted answer).
- Classifier check on a fresh hand-labelled holdout (n=40): WISMO-flag precision 93% (28/30); 1 of 10 sampled 1–2★/complaint rows it called non-WISMO were in fact WISMO, so WISMO shares are lower bounds (section 8).

## 1. What was collected

| Source | Status | Kind | Rows | Date range | 1–2★ | WISMO | Detail |
| :--- | :--- | :--- | ---: | :--- | ---: | ---: | :--- |
| google_play | ok | app_review | 8,377 | 2026-06-29 → 2026-09-29 | 4,600 | 568 | app_id=com.application.zomato, lang=en, country=in; pulls: newest=5000, low_1=3000, low_2=1600 |
| app_store | ok | app_review | 500 | 2026-09-25 → 2026-09-28 | 82 | 27 | app_id=434613896, storefront=in, pages with data=10, feed last page=10 |
| consumercomplaints | ok | complaint_site | 61 | 2023-02-08 → 2026-08-25 | – | 15 | slug=zomato-b115724, listing pages=6, detail pages=25, min_date=2023-01-01, older rows dropped=59 |
| trustpilot | skipped | – | 0 | – | – | 0 | robots.txt: 'User-agent: * / Disallow: /' (only named search bots allowed); pages also return HTTP 403 to non-browser clients |
| mouthshut | skipped | – | 0 | – | – | 0 | robots.txt disallows ClaudeBot site-wide (and Content-Signal ai-train=no); not fetched |
| reddit | skipped | – | 0 | – | – | 0 | robots.txt disallows this path (Disallow: / for all agents); API requires OAuth login |

Google Play windows: all-ratings sample 2026-09-20 → 2026-09-29; 1★ complete from 2026-09-06; 2★ complete from 2026-06-29.
Detected language of app reviews: en 8,620, hi-Latn 208, hi 49 (Play pulled with `lang=en`; `hi-Latn` = romanised Hindi/Hinglish).

## 2. How much of the review stream is WISMO?

| Sample | n | WISMO share (95% CI) |
| :--- | ---: | ---: |
| All ratings (unbiased app sample) | 5,500 | 3.6% (3.1–4.1) |
| 1★ | 3,077 | 15.1% (13.9–16.5) |
| 2★ | 1,605 | 6.9% (5.8–8.3) |
| 3★ | 272 | 2.6% (1.3–5.2) |
| 4–5★ | 3,923 | 0.3% (0.2–0.5) |
| … google_play only (all ratings) | 5,000 | 3.4% (2.9–3.9) |
| … app_store only (all ratings) | 500 | 5.4% (3.7–7.7) |
| Complaint-board posts | 61 | 24.6% (15.5–36.7) |

1★ and 2★ rows include the extra low-star pulls (longer window); 3★ and 4–5★ come from the all-ratings sample only.

## 3. Hypothesis scorecard

Share of WISMO reviews (all-ratings app sample) that mention each hypothesised pain, with the same measure among all 1–2★ reviews and complaint-board posts. Verdict thresholds (share of WISMO reviews): strong ≥15%, moderate 5–15%, weak 2–5%, rare <2%.

| Hypothesis | Categories | % of WISMO reviews (n=196) | % of 1–2★ WISMO (n=577) | % of all 1–2★ (n=4682) | % of complaint posts (n=61) | Verdict | Classifier check (holdout) |
| :--- | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| Poor or vague "where is my order" answers | `vague_support_answer` | 3.1% (1–7) | 4.0% | 1.3% | 4.9% | weak | P 100% (2/2) · R 67% (2/3) |
| Trackers stale, vague or wrong | `tracking_stale_wrong` | 1.0% (0–4) | 0.7% | 0.1% | 0.0% | rare | P – · R 0% (0/2) |
| Rider stuck / not moving | `rider_stuck` | 2.0% (1–5) | 1.7% | 0.2% | 0.0% | weak | P 100% (2/2) · R 100% (2/2) |
| Traffic delays and ETA slips | `eta_slip_late`, `traffic_weather_excuse` | 76.0% (70–81) | 74.0% | 9.1% | 16.4% | strong | P 84% (16/19) · R 80% (16/20) |
| Multiple / batched orders | `multiple_batched_orders` | 7.7% (5–12) | 6.6% | 0.8% | 0.0% | moderate | P 100% (1/1) · R 50% (1/2) |
| Bad address resolution | `address_location` | 2.6% (1–6) | 4.9% | 0.6% | 6.6% | weak | P 100% (3/3) · R 100% (3/3) |
| "Delivered" but not received | `delivered_not_received` | 7.1% (4–12) | 8.7% | 1.1% | 3.3% | moderate | P 83% (5/6) · R 100% (5/5) |
| Support loops / unreachable | `support_unreachable_loop` | 16.8% (12–23) | 19.6% | 10.4% | 18.0% | strong | P 80% (4/5) · R 67% (4/6) |

Classifier check = precision (P) and recall (R) of the hypothesis categories on the fresh hand-labelled holdout (section 8). Low recall means the share is an undercount; tiny n means the check itself is rough.

## 4. Every category

| Category | Group | % all reviews (n=5,500) | % WISMO reviews (n=196) | % 1–2★ (n=4,682) | % complaint posts (n=61) | % curated (n=0) | Holdout precision · recall |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| ETA slip / late delivery | WISMO | 2.6% | 74.0% | 9.0% | 16.4% | – | P 94% (16/17) · R 80% (16/20) |
| Not received / where is my order | WISMO | 0.5% | 13.3% | 1.6% | 11.5% | – | P 67% (2/3) · R 100% (2/2) |
| Marked delivered, not received | WISMO | 0.3% | 7.1% | 1.1% | 3.3% | – | P 83% (5/6) · R 100% (5/5) |
| Multiple / batched orders | WISMO | 0.3% | 7.7% | 0.8% | 0.0% | – | P 100% (1/1) · R 50% (1/2) |
| Address / location resolution | WISMO | 0.1% | 2.6% | 0.6% | 6.6% | – | P 100% (3/3) · R 100% (3/3) |
| Traffic / weather / demand excuse | WISMO | 0.1% | 2.6% | 0.2% | 0.0% | – | P 0% (0/2) · R – |
| Rider / parcel stuck, not moving | WISMO | 0.1% | 2.0% | 0.2% | 0.0% | – | P 100% (2/2) · R 100% (2/2) |
| Tracker stale, vague or wrong | WISMO | 0.0% | 1.0% | 0.1% | 0.0% | – | P – · R 0% (0/2) |
| Support unreachable / bot loop | cross-cutting | 3.0% | 16.8% | 10.4% | 18.0% | – | P 80% (4/5) · R 67% (4/6) |
| Refund stuck / not received | adjacent | 0.8% | 5.1% | 2.8% | 29.5% | – | P 100% (2/2) · R 100% (2/2) |
| Cancelled by platform / restaurant | adjacent | 0.6% | 4.1% | 1.5% | 3.3% | – | P 100% (2/2) · R 50% (2/4) |
| Vague / scripted answer | cross-cutting | 0.4% | 3.1% | 1.3% | 4.9% | – | P 100% (2/2) · R 67% (2/3) |
| Partial / missing item | adjacent | 0.5% | 3.6% | 1.6% | 8.2% | – | P – · R 0% (0/2) |
| Rider behaviour / asked to pick up | adjacent | 0.3% | 1.5% | 1.1% | 0.0% | – | P – · R 0% (0/2) |
| No proactive update | cross-cutting | 0.1% | 0.5% | 0.4% | 0.0% | – | – |
| Other / non-WISMO | derived | 96.4% | – | 87.7% | 75.4% | – | – |

Cross-cutting and adjacent categories do not make a review WISMO on their own; they are counted so their overlap with WISMO can be measured (section 6).

## 5. Trend by month (Google Play)

All-ratings sample (the newest-reviews pull):

| Month | Reviews | WISMO share |  |
| :--- | ---: | ---: | ---: |
| 2026-09 (partial) | 5,000 | 3.4% |  |

1–2★ reviews, months where both star levels are fully covered:

| Month | 1–2★ reviews | WISMO share | ETA slip / late delivery | Not received / where is my order | Marked delivered, not received | Multiple / batched orders |  |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-09 (partial) | 3,385 | 13.9% | 9.7% | 2.0% | 1.4% | 0.9% |  |

The current month is to date. Month-to-month moves under ~5 points on n<200 are within noise.

Complaint-board posts by year: 2023: 11 (36.4% WISMO), 2024: 9 (22.2% WISMO), 2025: 27 (18.5% WISMO), 2026: 14 (28.6% WISMO).

## 6. Co-occurrence

Pool: all WISMO app reviews (any pull) plus WISMO complaint posts, n=610. P(B|A) = share of reviews with A that also mention B; lift >1 means they travel together more than chance.

| A → B | n(A) | n(A∧B) | P(B|A) | P(B) baseline | Lift |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Marked delivered, not received → Support unreachable / bot loop | 53 | 15 | 28.3% | 19.2% | 1.5× |
| Not received / where is my order → Support unreachable / bot loop | 82 | 22 | 26.8% | 19.2% | 1.4× |
| ETA slip / late delivery → Support unreachable / bot loop | 444 | 75 | 16.9% | 19.2% | 0.9× |
| ETA slip / late delivery → Vague / scripted answer | 444 | 14 | 3.2% | 4.1% | 0.8× |
| ETA slip / late delivery → Cancelled by platform / restaurant | 444 | 24 | 5.4% | 4.6% | 1.2× |
| ETA slip / late delivery → No proactive update | 444 | 5 | 1.1% | 0.8% | 1.4× |
| Not received / where is my order → Refund stuck / not received | 82 | 14 | 17.1% | 7.0% | 2.4× |
| Multiple / batched orders → ETA slip / late delivery | 39 | 23 | 59.0% | 72.8% | 0.8× |
| Rider / parcel stuck, not moving → ETA slip / late delivery | 10 | 3 | 30.0% | 72.8% | 0.4× |
| Tracker stale, vague or wrong → ETA slip / late delivery | 4 | 1 | 25.0% | 72.8% | 0.3× |
| Address / location resolution → Rider behaviour / asked to pick up | 32 | 1 | 3.1% | 2.5% | 1.3× |
| Traffic / weather / demand excuse → ETA slip / late delivery | 13 | 5 | 38.5% | 72.8% | 0.5× |

Most frequent pairs overall:

| Category A | Category B | Both | Lift |
| :--- | :--- | ---: | ---: |
| ETA slip / late delivery | Support unreachable / bot loop | 75 | 0.9× |
| Cancelled by platform / restaurant | ETA slip / late delivery | 24 | 1.2× |
| ETA slip / late delivery | Multiple / batched orders | 23 | 0.8× |
| ETA slip / late delivery | Refund stuck / not received | 23 | 0.7× |
| Not received / where is my order | Support unreachable / bot loop | 22 | 1.4× |
| Refund stuck / not received | Support unreachable / bot loop | 16 | 1.9× |
| Marked delivered, not received | Support unreachable / bot loop | 15 | 1.5× |
| Not received / where is my order | Refund stuck / not received | 14 | 2.4× |
| ETA slip / late delivery | Vague / scripted answer | 14 | 0.8× |
| ETA slip / late delivery | Not received / where is my order | 13 | 0.2× |

## 7. What shoppers say (verbatim)

Excerpts are verbatim (line breaks collapsed); `…` marks a cut, and long numbers/emails are masked. Hand-checked rows are shown first, and rows the hand-check rejected for a category are never shown; the rest are a deterministic pseudo-random pick, so an occasional misfire can still appear. App Store links go to the app's review list (Apple has no per-review permalink); the id identifies the review.

### ETA slip / late delivery

> if you're a gold member your delivery is free but your order will be delayed 30 mins and above as they'll assign another delivery to the partner. the worst app. deleting the app which is of no use and their customer care bot is really a dumb
>
> — 1★ · google_play · 2026-09-12 · [gp:06a83330-6e26-4029-bf79-03a102d3c50b](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=06a83330-6e26-4029-bf79-03a102d3c50b) · ✓ hand-checked

> … It appears that Zomato is taking advantage of its limited competition in the city, while customers are left with no choice but to tolerate poor service. Tonight, an order placed at 2:30 AM was delivered at 3:34 AM — more than an hour late — and the food arrived completely cold. This is not acceptable for a paid food-delivery service. …
>
> — 1★ · app_store · 2026-09-26 · [as:14597305727](https://apps.apple.com/in/app/id434613896?see-all=reviews) · ✓ hand-checked

> Refund for order: [number]. Hi team, Zomato have very unprofessional services. I had placed order on their website which took almost an hour to reach me. I ordered this and informed delivery boy to deliver this order without making calls as i might be on work call as i was working from home. …
>
> — consumercomplaints · 2025-03-14 · [cc:3526110](https://www.consumercomplaints.in/zomato-refund-for-order-6687880506-c3526110) · ✓ hand-checked

> At first the experience was fine but now delivery is taking a lot of time like 40min for Even just 3km delivery distance. where the food is already ready in the restaurant and there is no traffic.
>
> — 2★ · google_play · 2026-07-11 · [gp:32e06091-76f6-46c4-8125-a51a11db7829](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=32e06091-76f6-46c4-8125-a51a11db7829) · ✓ hand-checked

### Not received / where is my order

> there delivery partner never reach restaurant to pick order and when you complaint service agent also wastes your time in last after 2 and more hours they told they have cancelled the order. service are becoming worse now days.
>
> — 1★ · google_play · 2026-09-13 · [gp:c9d7db0d-a2bc-42d5-a1e4-4257f4ab0980](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=c9d7db0d-a2bc-42d5-a1e4-4257f4ab0980) · ✓ hand-checked

> Cancelled order by zomato. My order (ORDER ID [protected]) was cancelled due to a location mismatch, even though I had entered the correct address and the delivery partner did not reach out properly. I did not receive my order, but the amount of Rs 635 has also not been refunded. …
>
> — consumercomplaints · 2025-11-13 · [cc:3536906](https://www.consumercomplaints.in/zomato-cancelled-order-by-zomato-c3536906) · ✓ hand-checked

> … I ordered for Someone yesterday night, it took 2 hours until they marked on app, that the food was delivered (which was estimated at time of Order 45-50 minutes), when i asked the recipient in morning, he said order was not received… Shame on these Restaurant, their Delivery Partners, and the company that Supports these behavior… No help has been provided from zomato since then…👎
>
> — 1★ · app_store · 2026-09-27 · [as:14599950802](https://apps.apple.com/in/app/id434613896?see-all=reviews)

> No accountability for the undelivered or partially delivered order.
>
> — 1★ · google_play · 2026-09-22 · [gp:afe23936-4a62-4b05-be97-4c6644686fe2](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=afe23936-4a62-4b05-be97-4c6644686fe2) · ✓ hand-checked

### Marked delivered, not received

> the service from zomato was good until a recent food order I made which was around 2k+ the delivery person reached close to my destination and accidentally clicked delivered but I didn't receive the food he had no way of contacting me directly on top of that from my end there was no way for me to get a person to look into it immediately as the only option you get for I did not receive this order is send an email... …
>
> — 1★ · google_play · 2026-09-28 · [gp:1e94e30b-5464-472e-b446-fad1cda5cff1](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=1e94e30b-5464-472e-b446-fad1cda5cff1) · ✓ hand-checked

> Online scam of delivery partner not delivering the order. Dear Zomato, i have placed an order with you on March 18 th, 2.02 pm, order id -[protected] from the shop Ceylon parota, the expected order time was 30 mins, but the delivery partner delivered it with thin that, but i have never received the order untill now, …
>
> — consumercomplaints · 2023-03-19 · [cc:3403580](https://www.consumercomplaints.in/zomato-online-scam-of-delivery-partner-not-delivering-the-order-c3403580)

> I ordered food at 9:26 pm, order was marked delivered at 10:23 pm. Tried calling the delivery partner, the person who answered the call said he is not a delivery partner. Contacted support, after 15 minutes and post their "out of world" investigation, they connected me with the delivery partner. …
>
> — 1★ · google_play · 2026-09-07 · [gp:fd83e8c1-1d58-4289-a0a4-42f5cf0a7f8d](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=fd83e8c1-1d58-4289-a0a4-42f5cf0a7f8d) · ✓ hand-checked

> … I never thought I’d say this, but Zomato has officially lost my trust. On 21st July 2025, I placed an order from Taste of Tandoor through Zomato (Order ID: [protected]). After waiting two hours, the app marked my food as “delivered.” But nothing arrived. I contacted the restaurant, who shared the delivery rider’s number...
>
> — consumercomplaints · 2025-07-21 · [cc:3532286](https://www.consumercomplaints.in/zomato-the-fraud-company-c3532286)

### Multiple / batched orders

> if you're a gold member your delivery is free but your order will be delayed 30 mins and above as they'll assign another delivery to the partner. the worst app. deleting the app which is of no use and their customer care bot is really a dumb
>
> — 1★ · google_play · 2026-09-12 · [gp:06a83330-6e26-4029-bf79-03a102d3c50b](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=06a83330-6e26-4029-bf79-03a102d3c50b) · ✓ hand-checked

> Multiple deliveries. Multiple time the ly clubs orders which eventually delay orders. Very bad service from zomato. not recommended
>
> — 1★ · app_store · 2026-09-27 · [as:14600058385](https://apps.apple.com/in/app/id434613896?see-all=reviews)

> Their policy of delivering multiple orders at a single time is not making me happy at all. I changed my review of 2018 of 5 to 1 Star due to this issue of them.
>
> — 1★ · google_play · 2026-09-21 · [gp:ccd52666-74ae-43fd-abd0-873dfc993360](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=ccd52666-74ae-43fd-abd0-873dfc993360) · ✓ hand-checked

> … 7. Now a days single delivery person is allocated to multiple order deliveries at the same time. So food gets very cold and dry by the time it reaches your place as delivery persons first delivers another delivery to a location which is not even on the same route. …
>
> — 1★ · app_store · 2026-09-27 · [as:14599089321](https://apps.apple.com/in/app/id434613896?see-all=reviews)

### Address / location resolution

> I placed an order for a dosa, but the delivery person couldn't find the location. Even after I sent the location, he asked me to cancel the order, so I ended up going without food. Now, Zomato is refusing to provide Cash on Delivery (COD) service to me. This wasn't my fault at all, so why are you doing this? …
>
> — 2★ · google_play · 2026-07-31 · [gp:ac9ddfa5-7163-485d-807e-f91b0d242e27](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=ac9ddfa5-7163-485d-807e-f91b0d242e27) · ✓ hand-checked

> … If my address is wrong or i denied order they can cancel order but when address is right just bcuz i havent picked call they cant cancel order and charge complete amount. Also when i texted delivery boy already with alternate no. And details. …
>
> — consumercomplaints · 2025-03-14 · [cc:3526110](https://www.consumercomplaints.in/zomato-refund-for-order-6687880506-c3526110) · ✓ hand-checked

> Very disappointing experience. My order was not delivered to me and was apparently delivered to another location. The delivery partner uploaded a photo as proof, but I never received my order. When the delivery partner called, he simply said that the mistake was mine and disconnected the call. …
>
> — 1★ · google_play · 2026-09-27 · [gp:ff33cf67-6bc9-42b3-be9c-71f566de5684](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=ff33cf67-6bc9-42b3-be9c-71f566de5684) · ✓ hand-checked

> Cancelled order by zomato. My order (ORDER ID [protected]) was cancelled due to a location mismatch, even though I had entered the correct address and the delivery partner did not reach out properly. I did not receive my order, but the amount of Rs 635 has also not been refunded. …
>
> — consumercomplaints · 2025-11-13 · [cc:3536906](https://www.consumercomplaints.in/zomato-cancelled-order-by-zomato-c3536906) · ✓ hand-checked

### Traffic / weather / demand excuse

> fraud people ..I ordered and it was 45min on time suddenly he got some other order and waited for pickup and it got delayed by 35 min .asking support they told traffic but the delivery guy told that some other order is not ready ..food got cold and I talked with support they are giving me 60 rs voucher for next food order .we are beggars or what you frauded us and giving 60rs voucher .zomato are cheaters.pls take this to social media or sending my chat on
>
> — 1★ · google_play · 2026-09-06 · [gp:9eed2e5a-f050-41f5-a37d-fba20171971a](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=9eed2e5a-f050-41f5-a37d-fba20171971a)

> bad experience with customer care and food quality was worst after complaining they are saying that due to temperature, weather etc food quality become worst. I ordered chicken biryani and when I opened it I got worst basmati rice in it which was already highly wet with water and in name of chicken I got ear and etc .
>
> — 2★ · google_play · 2026-08-06 · [gp:e96e9a90-2414-484c-81da-87289a4498a3](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=e96e9a90-2414-484c-81da-87289a4498a3)

> This is a worst delivery app. The issue is not with delivery, boys. it's with assigning deliveries always been delaying by assigning 2 to 3 orders at a time to a delivery by delivering But they were saying like due to high demand they just wanted to save the money.This is worst app.
>
> — 1★ · google_play · 2026-09-24 · [gp:27d5c78a-371a-4cdf-b055-13a3218d9f98](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=27d5c78a-371a-4cdf-b055-13a3218d9f98)

> I ordered food at 3.20am night and it was about to deliver in 45 min it reached location and was showing me 3 mins delayed and th he delivery man told me it's raining health so I cant come ..at the end this GuyS gave me option if I want to cancel @4.40 am after 1 hour 20 mins waste of time ...this app is it's better to try TOING that serves better .
>
> — 1★ · google_play · 2026-09-14 · [gp:2dcd4eda-0656-46c6-8c03-3533db7134a5](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=2dcd4eda-0656-46c6-8c03-3533db7134a5)

### Support unreachable / bot loop (WISMO reviews only)

> … An order placed at 7:00 PM was still stuck at the restaurant at 7:53 PM, with delivery pushed back to 8:25 PM. The support chat was useless, taking 5 minutes just to check the status only to give a generic "running late" excuse. Waiting nearly an hour and a half with zero active resolution is unacceptable.
>
> — 1★ · google_play · 2026-09-16 · [gp:1fd56f28-b94c-4d32-8953-065289c8bef9](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=1fd56f28-b94c-4d32-8953-065289c8bef9) · ✓ hand-checked

> Worst service. Zomato is very worst in customer service. Even for their delay and their mistakes also they don’t compensate. Swiggy is far better.
>
> — 1★ · app_store · 2026-09-26 · [as:14594850301](https://apps.apple.com/in/app/id434613896?see-all=reviews) · ✓ hand-checked

> … I did not receive my order, but the amount of Rs 635 has also not been refunded. Your agent refused to help in this matter by saying that food got wasted and delivery person's time was wasted as well but I also suffered a huge loss. …
>
> — consumercomplaints · 2025-11-13 · [cc:3536906](https://www.consumercomplaints.in/zomato-cancelled-order-by-zomato-c3536906) · ✓ hand-checked

> … Contacted support twice: first they forwarded me to the same delivery partner, then gave two missed calls (1:53 PM, 1:54 PM) with no resolution. Second contact, refund was denied just because he "arrived" at my home — despite me never receiving the order.
>
> — 1★ · google_play · 2026-09-12 · [gp:91a3fbaa-dd01-4faf-9812-49773febac91](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=91a3fbaa-dd01-4faf-9812-49773febac91) · ✓ hand-checked

### Vague / scripted answer (WISMO reviews only)

> Please do not use the app. Your order will be delayed always. they have no answers and just ask you to wait
>
> — 1★ · google_play · 2026-09-21 · [gp:79be6a5d-b39c-4dec-8bec-1525cd43d5be](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=79be6a5d-b39c-4dec-8bec-1525cd43d5be) · ✓ hand-checked

> … As the restaurant from where the order is placed comes under zomato. Receiving rancid food is like you haven't order anything. But they don't look into this matter instead fighting with me and dropping the same mail again and again, also in addition to this they are praising their service after all this. What non sense is this? …
>
> — consumercomplaints · 2024-01-22 · [cc:3495470](https://www.consumercomplaints.in/zomato-full-amount-not-refunded-even-after-delivering-rancid-food-c3495470) · ✓ hand-checked

> … My ₹514 order was marked as delivered, but I never received it. The delivery photo shows it left near someone else’s gate. When I called the delivery partner, he disconnected the call instead of explaining. Support simply asked me to email and wait 24 hours. As a Zomato Gold member, I expected much better and faster support.
>
> — 1★ · google_play · 2026-09-09 · [gp:56c5f522-42e4-4869-9e61-a6de69e65611](https://play.google.com/store/apps/details?id=com.application.zomato&reviewId=56c5f522-42e4-4869-9e61-a6de69e65611) · ✓ hand-checked

> … After i ordered food the agent kept on delaying my order. I called him several times and he informed me he is having multiple business with multiple orders. I also contacted customer care and they kept saying it will be delivered but the order kept on delaying. …
>
> — consumercomplaints · 2023-09-07 · [cc:3467173](https://www.consumercomplaints.in/zomato-delay-in-food-delivery-by-agent-c3467173)

## 8. Classifier validation

Every sampled review was read in full and its true categories recorded (`research/wismo_mining/validation/labels_*.jsonl`, with notes on judgement calls).

- **Sample A** (60 per brand, seeded random): 45 drawn from reviews the v1 classifier called WISMO, 15 from the rest (any rating). Used to fix patterns once (v1 → v2), so v2-on-A is optimistic.
- **Sample B** (40 per brand, drawn after v2 was frozen, never used for tuning): 30 predicted-WISMO, 10 predicted-non-WISMO taken only from 1–2★ reviews and complaint posts, where missed WISMO would hide. **v2 on B is the honest estimate.**

| Run | Labelled | WISMO-flag precision | True WISMO among sampled predicted-non-WISMO |
| :--- | ---: | ---: | ---: |
| v1 on A (before fixes) | 60 | 98% (44/45) | 2/15 |
| v2 on A (tuned) | 60 | 100% (46/46) | 0/15 |
| v2 on B (holdout) | 40 | 93% (28/30) | 1/10 |

| Category | Precision: v1 on A (before fixes) | Precision: v2 on A (tuned) | Precision: v2 on B (holdout) | Recall: v2 on B |
| :--- | ---: | ---: | ---: | ---: |
| ETA slip / late delivery | 90% (28/31) | 97% (30/31) | 94% (16/17) | 80% (16/20) |
| Marked delivered, not received | 100% (5/5) | 100% (8/8) | 83% (5/6) | 100% (5/5) |
| Support unreachable / bot loop | 100% (12/12) | 100% (18/18) | 80% (4/5) | 67% (4/6) |
| Not received / where is my order | 86% (6/7) | 100% (6/6) | 67% (2/3) | 100% (2/2) |
| Address / location resolution | 100% (4/4) | 100% (4/4) | 100% (3/3) | 100% (3/3) |
| Refund stuck / not received | 100% (4/4) | 100% (5/5) | 100% (2/2) | 100% (2/2) |
| Vague / scripted answer | 100% (4/4) | 100% (3/3) | 100% (2/2) | 67% (2/3) |
| Cancelled by platform / restaurant | 100% (3/3) | 100% (4/4) | 100% (2/2) | 50% (2/4) |
| Traffic / weather / demand excuse | 0% (0/1) | – | 0% (0/2) | – |
| Rider / parcel stuck, not moving | 100% (1/1) | 100% (1/1) | 100% (2/2) | 100% (2/2) |
| Multiple / batched orders | 100% (3/3) | 100% (4/4) | 100% (1/1) | 50% (1/2) |
| Rider behaviour / asked to pick up | – | 100% (5/5) | – | 0% (0/2) |
| Tracker stale, vague or wrong | – | 100% (1/1) | – | 0% (0/2) |
| Partial / missing item | – | – | – | 0% (0/2) |

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
- **Sources not collected:** `trustpilot` (skipped: robots.txt: 'User-agent: * / Disallow: /' (only named search bots allowed); pages also return HTTP 403 to non-browser clients); `mouthshut` (skipped: robots.txt disallows ClaudeBot site-wide (and Content-Signal ai-train=no); not fetched); `reddit` (skipped: robots.txt disallows this path (Disallow: / for all agents); API requires OAuth login).
- **Brand note:** consumercomplaints.in lists full complaints first and short posts after them; paging stopped once full complaints fell before 2023, so Zomato's short posts were not reached.
- **Brand note:** Zomato's review volume means the capped Play pulls cover ~10 days (all ratings) and ~3 weeks (1★): a snapshot, not a trend.
