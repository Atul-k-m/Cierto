# WISMO complaint mining: Smytten

_D2C beauty and lifestyle sample boxes · delivery model: courier · generated 2026-09-30 by `python -m wismo_mining report --brand smytten` · taxonomy v2_

WISMO = any shopper complaint about order status, location, ETA, delay, a missing parcel or a date change. Numbers come from a deterministic keyword/regex classifier (`research/wismo_mining/taxonomy.yaml`); every label stores the phrase that triggered it. Categories are multi-label, so shares do not add up to 100%.

## Headline

- **6.1%** of app-store reviews (all ratings, n=5,450) are WISMO-related (95% CI 5.5–6.7%).
- Among **1–2★** app reviews (n=4,848) the share is **24.7%**.
- Among complaint-board posts (n=216) it is **34.3%**.
- Largest WISMO issues among WISMO reviews: eta slip / late delivery (47.3%), not received / where is my order (46.1%), marked delivered, not received (13.3%).
- 31.5% of WISMO app reviews (all pulls) also report a support failure (unreachable, bot loop or a vague/scripted answer).
- Classifier check on a fresh hand-labelled holdout (n=40): WISMO-flag precision 87% (26/30); 3 of 10 sampled 1–2★/complaint rows it called non-WISMO were in fact WISMO, so WISMO shares are lower bounds (section 8).

## 1. What was collected

| Source | Status | Kind | Rows | Date range | 1–2★ | WISMO | Detail |
| :--- | :--- | :--- | ---: | :--- | ---: | ---: | :--- |
| google_play | ok | app_review | 8,327 | 2022-05-09 → 2026-09-28 | 4,600 | 1,165 | app_id=com.app.smytten, lang=en, country=in; pulls: newest=5000, low_1=3000, low_2=1600 |
| app_store | ok | app_review | 450 | 2025-04-27 → 2026-09-27 | 248 | 74 | app_id=1100171914, storefront=in, pages with data=9, feed last page=10, empty/failed pages after retries=[5] |
| consumercomplaints | ok | complaint_site | 216 | 2023-01-01 → 2026-08-16 | – | 74 | slug=smytten-b115980, listing pages=14, detail pages=5, min_date=2023-01-01, older rows dropped=64 |
| manual_research | ok | curated | 196 | 2019-09-11 → 2026-09-10 | – | 81 | data/complaints.json: 196 rows kept, 8 marked duplicate dropped |
| trustpilot | skipped | – | 0 | – | – | 0 | robots.txt: 'User-agent: * / Disallow: /' (only named search bots allowed); pages also return HTTP 403 to non-browser clients |
| mouthshut | skipped | – | 0 | – | – | 0 | robots.txt disallows ClaudeBot site-wide (and Content-Signal ai-train=no); not fetched |
| reddit | skipped | – | 0 | – | – | 0 | robots.txt disallows this path (Disallow: / for all agents); API requires OAuth login |

Google Play windows: all-ratings sample 2026-01-28 → 2026-09-28; 1★ complete from 2025-08-07; 2★ complete from 2022-05-09.
Detected language of app reviews: en 8,420, hi-Latn 350, hi 7 (Play pulled with `lang=en`; `hi-Latn` = romanised Hindi/Hinglish).

## 2. How much of the review stream is WISMO?

| Sample | n | WISMO share (95% CI) |
| :--- | ---: | ---: |
| All ratings (unbiased app sample) | 5,450 | 6.1% (5.5–6.7) |
| 1★ | 3,237 | 30.4% (28.8–32.0) |
| 2★ | 1,611 | 13.3% (11.8–15.1) |
| 3★ | 227 | 6.2% (3.7–10.1) |
| 4–5★ | 3,702 | 0.7% (0.5–1.0) |
| … google_play only (all ratings) | 5,000 | 5.1% (4.5–5.8) |
| … app_store only (all ratings) | 450 | 16.4% (13.3–20.2) |
| Complaint-board posts | 216 | 34.3% (28.3–40.8) |
| Curated complaints (manual research) | 196 | 41.3% (34.7–48.3) |

1★ and 2★ rows include the extra low-star pulls (longer window); 3★ and 4–5★ come from the all-ratings sample only.

## 3. Hypothesis scorecard

Share of WISMO reviews (all-ratings app sample) that mention each hypothesised pain, with the same measure among all 1–2★ reviews and complaint-board posts. Verdict thresholds (share of WISMO reviews): strong ≥15%, moderate 5–15%, weak 2–5%, rare <2%.

| Hypothesis | Categories | % of WISMO reviews (n=330) | % of 1–2★ WISMO (n=1199) | % of all 1–2★ (n=4848) | % of complaint posts (n=216) | Verdict | Classifier check (holdout) |
| :--- | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| Poor or vague "where is my order" answers | `vague_support_answer` | 5.2% (3–8) | 4.6% | 2.0% | 1.4% | moderate | P 67% (2/3) · R 50% (2/4) |
| Trackers stale, vague or wrong | `tracking_stale_wrong` | 4.8% (3–8) | 5.1% | 1.3% | 0.5% | weak | P 100% (2/2) · R 40% (2/5) |
| Rider stuck / not moving | `rider_stuck` | 0.9% (0–3) | 0.4% | 0.1% | 0.0% | rare | – |
| Traffic delays and ETA slips | `eta_slip_late`, `traffic_weather_excuse` | 47.3% (42–53) | 35.4% | 8.8% | 9.7% | strong | P 92% (11/12) · R 79% (11/14) |
| Multiple / batched orders | `multiple_batched_orders` | 3.6% (2–6) | 2.6% | 0.6% | 0.5% | weak | P 50% (1/2) · R 100% (1/1) |
| Bad address resolution | `address_location` | 1.2% (0–3) | 1.8% | 0.4% | 0.9% | rare | – |
| "Delivered" but not received | `delivered_not_received` | 13.3% (10–17) | 29.0% | 7.2% | 3.2% | moderate | P 83% (5/6) · R 100% (5/5) |
| Support loops / unreachable | `support_unreachable_loop` | 23.3% (19–28) | 30.1% | 16.2% | 10.6% | strong | P 100% (10/10) · R 56% (10/18) |

Classifier check = precision (P) and recall (R) of the hypothesis categories on the fresh hand-labelled holdout (section 8). Low recall means the share is an undercount; tiny n means the check itself is rough.

## 4. Every category

| Category | Group | % all reviews (n=5,450) | % WISMO reviews (n=330) | % 1–2★ (n=4,848) | % complaint posts (n=216) | % curated (n=196) | Holdout precision · recall |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| Not received / where is my order | WISMO | 2.8% | 46.1% | 9.4% | 22.7% | 17.9% | P 89% (8/9) · R 62% (8/13) |
| ETA slip / late delivery | WISMO | 2.9% | 47.3% | 8.7% | 9.3% | 5.1% | P 92% (11/12) · R 79% (11/14) |
| Marked delivered, not received | WISMO | 0.8% | 13.3% | 7.2% | 3.2% | 15.3% | P 83% (5/6) · R 100% (5/5) |
| Tracker stale, vague or wrong | WISMO | 0.3% | 4.8% | 1.3% | 0.5% | 3.6% | P 100% (2/2) · R 40% (2/5) |
| Multiple / batched orders | WISMO | 0.2% | 3.6% | 0.6% | 0.5% | 0.5% | P 50% (1/2) · R 100% (1/1) |
| Address / location resolution | WISMO | 0.1% | 1.2% | 0.4% | 0.9% | 0.5% | P 100% (2/2) · R 100% (2/2) (tuned sample) |
| Traffic / weather / demand excuse | WISMO | 0.0% | 0.3% | 0.1% | 0.5% | 0.0% | – |
| Rider / parcel stuck, not moving | WISMO | 0.1% | 0.9% | 0.1% | 0.0% | 1.0% | – |
| Support unreachable / bot loop | cross-cutting | 4.4% | 23.3% | 16.2% | 10.6% | 11.7% | P 100% (10/10) · R 56% (10/18) |
| Refund stuck / not received | adjacent | 2.1% | 8.8% | 6.8% | 6.9% | 13.8% | P 100% (2/2) · R 40% (2/5) |
| Vague / scripted answer | cross-cutting | 0.7% | 5.2% | 2.0% | 1.4% | 1.5% | P 67% (2/3) · R 50% (2/4) |
| No proactive update | cross-cutting | 0.7% | 3.3% | 2.1% | 2.8% | 2.0% | P 100% (2/2) · R 100% (2/2) |
| Partial / missing item | adjacent | 1.4% | 4.5% | 4.0% | 13.4% | 4.6% | P 100% (3/3) · R 100% (3/3) |
| Cancelled by platform / restaurant | adjacent | 0.6% | 3.3% | 2.7% | 1.9% | 3.1% | P 100% (1/1) · R 100% (1/1) |
| Rider behaviour / asked to pick up | adjacent | 0.2% | 0.3% | 0.5% | 0.9% | 0.5% | – |
| Other / non-WISMO | derived | 93.9% | – | 75.3% | 65.7% | 58.7% | – |

Cross-cutting and adjacent categories do not make a review WISMO on their own; they are counted so their overlap with WISMO can be measured (section 6).

## 5. Trend by month (Google Play)

All-ratings sample (the newest-reviews pull):

| Month | Reviews | WISMO share |  |
| :--- | ---: | ---: | ---: |
| 2026-01 (partial) | 84 | 7.1% |  |
| 2026-02 | 557 | 6.6% |  |
| 2026-03 | 656 | 4.6% |  |
| 2026-04 | 605 | 6.3% |  |
| 2026-05 | 746 | 3.5% |  |
| 2026-06 | 667 | 5.7% |  |
| 2026-07 | 693 | 2.9% |  |
| 2026-08 | 604 | 6.8% |  |
| 2026-09 | 388 | 5.2% |  |

1–2★ reviews, months where both star levels are fully covered:

| Month | 1–2★ reviews | WISMO share | Not received / where is my order | ETA slip / late delivery | Marked delivered, not received | Tracker stale, vague or wrong |  |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2025-08 (partial) | 187 | 18.2% | 10.2% | 9.1% | 0.0% | 0.5% |  |
| 2025-09 | 225 | 14.2% | 6.2% | 7.6% | 0.9% | 0.0% |  |
| 2025-10 | 212 | 20.3% | 8.0% | 12.3% | 0.9% | 0.0% |  |
| 2025-11 | 242 | 18.6% | 7.9% | 10.7% | 0.4% | 0.8% |  |
| 2025-12 | 614 | 51.8% | 14.3% | 8.5% | 30.0% | 2.1% |  |
| 2026-01 | 545 | 49.9% | 18.3% | 10.8% | 21.1% | 3.3% |  |
| 2026-02 | 150 | 19.3% | 8.7% | 6.7% | 4.7% | 2.0% |  |
| 2026-03 | 153 | 15.7% | 9.2% | 7.2% | 2.0% | 0.0% |  |
| 2026-04 | 227 | 15.4% | 8.4% | 6.2% | 0.0% | 0.9% |  |
| 2026-05 | 177 | 12.4% | 5.6% | 8.5% | 0.6% | 1.1% |  |
| 2026-06 | 159 | 22.0% | 11.9% | 10.7% | 0.6% | 0.6% |  |
| 2026-07 | 146 | 13.0% | 6.2% | 4.1% | 2.7% | 3.4% |  |
| 2026-08 | 147 | 23.8% | 14.3% | 11.6% | 0.7% | 0.0% |  |
| 2026-09 | 89 | 18.0% | 11.2% | 5.6% | 2.2% | 0.0% |  |

The current month is to date. Month-to-month moves under ~5 points on n<200 are within noise.

Complaint-board posts by year: 2023: 194 (34.0% WISMO), 2024: 10 (10.0% WISMO), 2025: 9 (44.4% WISMO), 2026: 3 (100.0% WISMO).

## 6. Co-occurrence

Pool: all WISMO app reviews (any pull) plus WISMO complaint posts, n=1,313. P(B|A) = share of reviews with A that also mention B; lift >1 means they travel together more than chance.

| A → B | n(A) | n(A∧B) | P(B|A) | P(B) baseline | Lift |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Marked delivered, not received → Support unreachable / bot loop | 358 | 144 | 40.2% | 28.6% | 1.4× |
| Not received / where is my order → Support unreachable / bot loop | 517 | 133 | 25.7% | 28.6% | 0.9× |
| ETA slip / late delivery → Support unreachable / bot loop | 469 | 118 | 25.2% | 28.6% | 0.9× |
| ETA slip / late delivery → Vague / scripted answer | 469 | 18 | 3.8% | 4.4% | 0.9× |
| ETA slip / late delivery → Cancelled by platform / restaurant | 469 | 17 | 3.6% | 2.7% | 1.4× |
| ETA slip / late delivery → No proactive update | 469 | 18 | 3.8% | 4.3% | 0.9× |
| Not received / where is my order → Refund stuck / not received | 517 | 52 | 10.1% | 9.3% | 1.1× |
| Multiple / batched orders → ETA slip / late delivery | 35 | 10 | 28.6% | 35.7% | 0.8× |
| Rider / parcel stuck, not moving → ETA slip / late delivery | 5 | 2 | 40.0% | 35.7% | 1.1× |
| Tracker stale, vague or wrong → ETA slip / late delivery | 62 | 10 | 16.1% | 35.7% | 0.5× |
| Address / location resolution → Rider behaviour / asked to pick up | 24 | 0 | 0.0% | 0.5% | – |
| Traffic / weather / demand excuse → ETA slip / late delivery | 8 | 4 | 50.0% | 35.7% | 1.4× |

Most frequent pairs overall:

| Category A | Category B | Both | Lift |
| :--- | :--- | ---: | ---: |
| Marked delivered, not received | Support unreachable / bot loop | 144 | 1.4× |
| Not received / where is my order | Support unreachable / bot loop | 133 | 0.9× |
| ETA slip / late delivery | Support unreachable / bot loop | 118 | 0.9× |
| ETA slip / late delivery | Not received / where is my order | 78 | 0.4× |
| Not received / where is my order | Refund stuck / not received | 52 | 1.1× |
| Refund stuck / not received | Support unreachable / bot loop | 51 | 1.5× |
| Marked delivered, not received | Refund stuck / not received | 38 | 1.1× |
| ETA slip / late delivery | Refund stuck / not received | 31 | 0.7× |
| Not received / where is my order | No proactive update | 31 | 1.4× |
| Support unreachable / bot loop | Vague / scripted answer | 26 | 1.6× |

## 7. What shoppers say (verbatim)

Excerpts are verbatim (line breaks collapsed); `…` marks a cut, and long numbers/emails are masked. Hand-checked rows are shown first, and rows the hand-check rejected for a category are never shown; the rest are a deterministic pseudo-random pick, so an occasional misfire can still appear. App Store links go to the app's review list (Apple has no per-review permalink); the id identifies the review.

### Not received / where is my order

> fraud application the product not delivered to you after you paid the money
>
> — 1★ · google_play · 2026-03-09 · [gp:87a1f8aa-ce69-423b-9d3f-c17ef353ef5b](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=87a1f8aa-ce69-423b-9d3f-c17ef353ef5b) · ✓ hand-checked

> Trail order #[number] not received. Hii I had placed order on smytten on 6 may 2023 but still I have not received the order. Status had not changed since 10 may 2023. Try to talk to them through email but that has not helped at all. So request you to get the refund of the order as I don't want the order now. Thank you
>
> — consumercomplaints · 2023-05-12 · [cc:3429133](https://www.consumercomplaints.in/smytten-b115980/page/6#cl3429133)

> Order missing. Firstly I lost trust on this app. I order trial pack on 18 Dec 2025 and it should be delivered to me on 23 Dec 2025. Till now I didn’t received my order . And I kept mail to this Smytten they are not responding and I want to raise a ticket in Smytten but it’s not at all accept . This was the worst experience for me. …
>
> — 1★ · app_store · 2026-01-06 · [as:13602108936](https://apps.apple.com/in/app/id1100171914?see-all=reviews)

> order ni aya 10 bar hmne msg krke pucha
>
> — manual research (Trustpilot) · 2026-07-19 · [mr:TP-04](https://dk.trustpilot.com/reviews/6a5cb9e5e0d332a1f509db99)

### ETA slip / late delivery

> There is no delivery on time and you can't cancel the order once placed...even the customer support is not helping. My money is stuck with them for a week now.
>
> — 1★ · google_play · 2026-02-19 · [gp:c008ba7c-0d47-4291-a871-1b8485519586](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=c008ba7c-0d47-4291-a871-1b8485519586) · ✓ hand-checked

> … These guys don’t care one bit about the customer. Eating this food makes will definitely make any one sick. It took 45 minutes to get past their useless AI Chat Bot to an agent claiming to be “human” who was just as useless as the Chat Bot. Please don’t waste your money. Discounted items don’t have to mean expired items. …
>
> — 1★ · app_store · 2026-05-15 · [as:14066796850](https://apps.apple.com/in/app/id1100171914?see-all=reviews)

> Delay & Partial Delivery of Order #4806132 Urgent Assistance Required.
>
> — consumercomplaints · 2025-12-30 · [cc:3538375](https://www.consumercomplaints.in/smytten-delay-partial-delivery-of-order-4806132-urgent-assistance-required-c3538375) · ✓ hand-checked

> smytten didn't provide delivery partner and it is delayed very day
>
> — manual research (Voxya) · 2025-10-28 · [mr:VX-02](https://voxya.com/consumer-complaints/package-not-delivered/252807)

### Marked delivered, not received

> I did not receive my order and this is showing that and delivered and it's pre paid my 600 is not refundable now soo please I request you give 50 rupees but don't make it pre paid😭😭😭😭😭😭😭😭😭
>
> — 1★ · google_play · 2026-01-03 · [gp:4cdb1dc1-775b-4f78-b6ca-a0e1c20320df](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=4cdb1dc1-775b-4f78-b6ca-a0e1c20320df) · ✓ hand-checked

> Bad app. Hi guys there are now doing frauds …don’t buy anything from this app…. they have marked my order as delivered but I didn’t received any order…. when i raised d complaint no one has listened my… my money got wasted
>
> — 1★ · app_store · 2025-12-27 · [as:13561393425](https://apps.apple.com/in/app/id1100171914?see-all=reviews) · ✓ hand-checked

> The tracking status shows that the parcel has been delivered
>
> — manual research (IndiaCustomerCare (comments)) · 2025-12-24 · [mr:IC-213268](https://www.indiacustomercare.com/smytten-customer-care-no#comment-213268)

> Items not delivered yet. I haven't received my order yet and it's showing delivered status on the app
>
> — consumercomplaints · 2023-07-30 · [cc:3456251](https://www.consumercomplaints.in/smytten-b115980/page/5#cl3456251)

### Tracker stale, vague or wrong

> … I have sent complaint mail to their customer care email, but doesn't seem like they care. Be careful with your money. Undelivered package order id is [number]. Update on 28 Aug: Not delivered yet, still shows 'will be delivered by 21st'
>
> — 1★ · google_play · 2025-08-28 · [gp:f1219613-2272-49b0-b3a9-20016a63878c](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=f1219613-2272-49b0-b3a9-20016a63878c) · ✓ hand-checked

> Such a big disappointment. Very poor service, i ordered 3 kajal, & some trial products neither kajal delivered nor trial products, i paid whole amount already, app shows out for delivery order for 3-4days still didn't received a single order, no customer care number they have! …
>
> — 1★ · app_store · 2025-10-15 · [as:13269902075](https://apps.apple.com/in/app/id1100171914?see-all=reviews)

> their app has not updated the order status
>
> — manual research (Voxya) · 2026-01-06 · [mr:VX-07](https://voxya.com/consumer-complaints/refund-pending-due-to-incorrect-order-status-/256565)

> Order not delivered even after out of delivery. I am unable to track mt order it showing consignee did not receive code . And it has not delivered yet .
>
> — consumercomplaints · 2023-03-17 · [cc:3402771](https://www.consumercomplaints.in/smytten-b115980/page/10#cl3402771)

### Multiple / batched orders

> … nothing changed even after several emails and contacting the agent on the app... one of my items is still not dispatched and one is not being delivered and the problem is not on my end. The team is at the end of the issue because the number given to the delivery partner was wrong even when I entered the right no. in the app.
>
> — 1★ · google_play · 2026-01-13 · [gp:0e183a8c-972a-4d26-bdad-b99626b7195d](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=0e183a8c-972a-4d26-bdad-b99626b7195d) · ✓ hand-checked

> … I have ordered items and there were my 3 packages from which one is delivered late and one is marked delivered but it did not arrived and the third one package is showing estimated delivery date which is already gone but no delivery parter called me and when i contacted to help support chat it only sends computerised messages and at the end it does not even reply they are not doing it right i have already paid for my orders and what they do is only mark
>
> — 1★ · app_store · 2026-01-02 · [as:13585187201](https://apps.apple.com/in/app/id1100171914?see-all=reviews)

> … I've placed an order on 13th April, 2023. Order id: #2857445. I've ordered total 4 items from smytten shop, it was PREPAID and they were divided into 2 shipments, each shipment had 2 products. One shipment was delivered rightly. But the other shipment was supposed to deliver 2 products- maybelline highlighter and the derma co sunscreen. …
>
> — consumercomplaints · 2023-04-19 · [cc:3418550](https://www.consumercomplaints.in/smytten-b115980/page/8#cl3418550)

> Product is good but showing money less amount collected amount is extra price its not good and your order any 2more products will get 2 shipment not only one delivery he will send different parcel I expireance very bad and I am not reffer any one this app
>
> — 2★ · google_play · 2022-09-03 · [gp:a7a3fadc-02ae-42e5-8e7e-c0eb5c1057fb](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=a7a3fadc-02ae-42e5-8e7e-c0eb5c1057fb) · ✓ hand-checked

### Address / location resolution

> i please two order parcel tracking show rech at my local areas but then send other location and other and other after one month says parcel received back to smytten so we give refund so it significant give discount for collect money form customer use for couple of times and refund i talk to customer care if you received product so send it back i dont want refund i need product they say not possible we give only refund
>
> — 1★ · google_play · 2025-09-29 · [gp:55fca77d-f081-4c12-b618-b4d082ceb2d3](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=55fca77d-f081-4c12-b618-b4d082ceb2d3) · ✓ hand-checked

> Order delayed (unable to locate my location).
>
> — consumercomplaints · 2023-05-06 · [cc:3426571](https://www.consumercomplaints.in/smytten-b115980/page/7#cl3426571)

> just state that your address is wrong
>
> — manual research (IndiaCustomerCare (comments)) · 2025-12-26 · [mr:IC-213295](https://www.indiacustomercare.com/smytten-customer-care-no#comment-213295)

> This has been the worst delivery experience; for five days, they have been unable to deliver the package and keep going to the wrong address. Even though we shared the location and called 20 times, there is no response.
>
> — 1★ · google_play · 2026-08-10 · [gp:1f8012c9-4816-4bbc-85d5-3eb60fe978e5](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=1f8012c9-4816-4bbc-85d5-3eb60fe978e5) · ✓ hand-checked

### Support unreachable / bot loop (WISMO reviews only)

> it's worst experience with smytten, I'm yet to receive my prepaid order which should be delivered yesterday, there's no any customer care number to reach and complain
>
> — 1★ · google_play · 2026-09-07 · [gp:8236a5c6-a332-45fb-bfb0-64a9edb75fe7](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=8236a5c6-a332-45fb-bfb0-64a9edb75fe7) · ✓ hand-checked

> Bad app. Hi guys there are now doing frauds …don’t buy anything from this app…. they have marked my order as delivered but I didn’t received any order…. when i raised d complaint no one has listened my… my money got wasted
>
> — 1★ · app_store · 2025-12-27 · [as:13561393425](https://apps.apple.com/in/app/id1100171914?see-all=reviews) · ✓ hand-checked

> … Stop cheating customers I ordered guess night deodorant on 8th april 2023, but till now 1st may 2023, product not delivered.in product details it shows delivered. I mailed many times for this issue on [email] but there is no answer from smytten. After many mails they reply on 25th april 2023 and accept his mistake. …
>
> — consumercomplaints · 2023-05-10 · [cc:3428229](https://www.consumercomplaints.in/smytten-b115980/page/7#cl3428229)

> order didn't received and it was prepaidd no response by agents
>
> — manual research (IndiaCustomerCare (comments)) · 2025-12-31 · [mr:IC-213395](https://www.indiacustomercare.com/smytten-customer-care-no#comment-213395)

### Vague / scripted answer (WISMO reviews only)

> I have ordered somw product from Smytten thoroug online payment and it's been more than 9 days and still didn't get the parcel from your service. And if i go to the help section there is just an AI robo who just apologize but not response well and provide you service. …
>
> — 1★ · google_play · 2025-11-03 · [gp:272a77c5-33e8-4e42-b4b4-633ed3936b46](https://play.google.com/store/apps/details?id=com.app.smytten&reviewId=272a77c5-33e8-4e42-b4b4-633ed3936b46) · ✓ hand-checked

> … At last when I tried cancelling the order app is not allowing to cancel the product stating tech error in the request. When I try to raise concern it gives automated response. …
>
> — 1★ · app_store · 2025-12-23 · [as:13547231397](https://apps.apple.com/in/app/id1100171914?see-all=reviews)

> … I ordered trial pack on 20 April onwards which has to deliver by 24 April . At first the delivery agent called and said your order will delivered by tomorrow as he said he is not able to deliver the order today. But then he called next day and again said that he will deliver the order tomorrow . …
>
> — consumercomplaints · 2023-04-27 · [cc:3422391](https://www.consumercomplaints.in/smytten-b115980/page/7#cl3422391)

> no proper information about the order till date in the help center
>
> — manual research (IndiaCustomerCare (comments)) · 2025-03-19 · [mr:IC-207829](https://www.indiacustomercare.com/smytten-customer-care-no#comment-207829)

## 8. Classifier validation

Every sampled review was read in full and its true categories recorded (`research/wismo_mining/validation/labels_*.jsonl`, with notes on judgement calls).

- **Sample A** (60 per brand, seeded random): 45 drawn from reviews the v1 classifier called WISMO, 15 from the rest (any rating). Used to fix patterns once (v1 → v2), so v2-on-A is optimistic.
- **Sample B** (40 per brand, drawn after v2 was frozen, never used for tuning): 30 predicted-WISMO, 10 predicted-non-WISMO taken only from 1–2★ reviews and complaint posts, where missed WISMO would hide. **v2 on B is the honest estimate.**

| Run | Labelled | WISMO-flag precision | True WISMO among sampled predicted-non-WISMO |
| :--- | ---: | ---: | ---: |
| v1 on A (before fixes) | 60 | 98% (44/45) | 3/15 |
| v2 on A (tuned) | 60 | 100% (47/47) | 0/15 |
| v2 on B (holdout) | 40 | 87% (26/30) | 3/10 |

| Category | Precision: v1 on A (before fixes) | Precision: v2 on A (tuned) | Precision: v2 on B (holdout) | Recall: v2 on B |
| :--- | ---: | ---: | ---: | ---: |
| ETA slip / late delivery | 92% (11/12) | 100% (16/16) | 92% (11/12) | 79% (11/14) |
| Support unreachable / bot loop | 100% (14/14) | 100% (20/20) | 100% (10/10) | 56% (10/18) |
| Not received / where is my order | 72% (13/18) | 83% (15/18) | 89% (8/9) | 62% (8/13) |
| Marked delivered, not received | 92% (12/13) | 100% (14/14) | 83% (5/6) | 100% (5/5) |
| Partial / missing item | 100% (2/2) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| Vague / scripted answer | 50% (1/2) | 50% (1/2) | 67% (2/3) | 50% (2/4) |
| Refund stuck / not received | 75% (3/4) | 88% (7/8) | 100% (2/2) | 40% (2/5) |
| Tracker stale, vague or wrong | 100% (2/2) | 100% (4/4) | 100% (2/2) | 40% (2/5) |
| No proactive update | 50% (1/2) | 100% (1/1) | 100% (2/2) | 100% (2/2) |
| Multiple / batched orders | – | 100% (2/2) | 50% (1/2) | 100% (1/1) |
| Cancelled by platform / restaurant | – | – | 100% (1/1) | 100% (1/1) |
| Address / location resolution | 100% (2/2) | 100% (2/2) | – | – |

Small n per category means wide error bars (8/10 is compatible with ~50–95%). Recall on B is measured within a WISMO-enriched sample, so treat it as indicative. Known v2 failure modes seen on the holdout: tracker complaints phrased as 'shows wrong delivery time' / 'time shown is not correct' are missed (tracker share is an undercount); generic 'poor customer support' is not counted as support failure; 'taking too much charges' and 'took forever to refund' can trip the ETA rule; 'rain' as a fee can trip the weather rule.

### Agreement with the manual Smytten research labels

The curated dataset carries a researcher's primary and secondary category per complaint. Recall here = share of complaints with that manual label where the classifier fired a matching category. Text is the verbatim fragment plus the researcher's summary.

| Manual category (primary or secondary) | Expected taxonomy ids | n | Recall |
| :--- | :--- | ---: | ---: |
| Delivery delay | `eta_slip_late`, `order_not_delivered` | 44 | 59.1% |
| Order not received | `delivered_not_received`, `order_not_delivered` | 18 | 55.6% |
| Marked delivered but not received | `delivered_not_received` | 41 | 70.7% |
| Tracking/status issue | `tracking_stale_wrong` | 12 | 41.7% |
| Courier/delivery attempt issue | `address_location`, `order_not_delivered`, `rider_behaviour`, `rider_stuck` | 10 | 40.0% |
| Lost/returned shipment | `order_not_delivered` | 3 | 33.3% |
| Missing item | `partial_missing_item` | 16 | 50.0% |
| Partial shipment | `multiple_batched_orders`, `partial_missing_item` | 11 | 0.0% |
| Cancellation | `cancelled_by_platform` | 13 | 30.8% |
| Refund delay | `refund_stuck` | 6 | 83.3% |
| Refund not received | `refund_stuck` | 27 | 66.7% |
| Incorrect/partial refund | `refund_stuck` | 3 | 0.0% |
| Customer-support accessibility | `support_unreachable_loop` | 20 | 50.0% |
| Customer-support resolution failure | `support_unreachable_loop`, `vague_support_answer` | 24 | 50.0% |

Manual primary category in the WISMO-core group (n=114): classifier flags 67.5% as WISMO.

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
- **Curated Smytten dataset** (`data/complaints.json`): hand-picked complaints from Trustpilot, Voxya, IndiaCustomerCare, MouthShut and the App Store (2019–2026). Its text is partly a researcher's paraphrase; it is used for mix and as a cross-check, never for shares of reviews. Only its verbatim fragments are quoted.
- **Brand note:** Courier model: 'late' means days, and 'not received' usually means a parcel stuck with the courier, so these two categories overlap more than for food apps.
