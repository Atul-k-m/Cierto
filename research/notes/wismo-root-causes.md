# WISMO root causes: what makes people ask "where is my order", and how the best teams fix each cause

Researched 2026-09-30. This note **extends** `best-wismo-practices.md`, which already covers the consumer-app survey, the vendor table, delivery proof and refunds. It does not repeat those facts. Where this note builds on one of them, it points back to it.

Markers (the same as in the earlier note, plus two):
- **[vendor claim]**: a number a company published about itself, not independently audited.
- **[3rd-party]**: a review, comparison, news or SEO page, which may have its own agenda.
- **[unverified]**: could not be confirmed against a primary source.
- **(snippet)**: the page blocked fetching (bytes.swiggy.com, Medium, careersatdoordash.com, zomato.com/blog), so the claim rests on the search-result text.
- **[inferred]**: my own design reasoning, not a sourced fact.

> **Method and limits.**
> - Four research threads ran in parallel: trackers and ETA, batching and comms, Indian addresses, and conversational agents.
> - Several threads hit a 200-search cap, and some primary pages blocked fetching. Claims resting on search-result text are marked (snippet).
> - **No Indian platform publishes its batching share, its tracker copy for batching, or how often riders call customers for directions.** Where this note needs those numbers, it says so.

The three target hosts need different answers:
- **Smytten** (D2C sample boxes shipped by third-party couriers).
  - Signals are **sparse courier scans**, hours or days apart, plus an EDD, NDR reasons and a typed address.
  - There is no rider GPS.
- **Swish** (10-minute food).
  - It owns its kitchens, supply chain and delivery fleet, and works in hyperlocal clusters with **about 1 km delivery radii**. It handled about 20,000 orders/day in Mar 2026 (https://techcrunch.com/2026/03/23/bengaluru-food-startup-swish-raises-38m-in-its-third-round-in-18-months/).
  - Its signals are **dense and first-party**: kitchen state and rider GPS every few seconds.
  - A 3-minute stall is a large share of the promise.
- **Zomato** (marketplace food delivery).
  - It has dense rider GPS, but prep time belongs to a third-party restaurant.
  - Riders are batched.
  - The platform already has its own ETA model and map.

Every Pakka feature below therefore has to work with both dense and sparse signals, and each lists a fallback **[inferred]**.

---

## 1. Vague, stale or wrong trackers

### Root cause
1. **Predicted movement shown as fact.**
   - A USPS Office of Inspector General audit (May 15, 2023) checked 500 packages. In **318 (64%)**, the tracking did not match the actual location, time or date.
     - **163 showed "Out for Delivery" while still at the post office.**
     - The causes were missed scans and "programming logic [that] reports anticipated package movement through the network rather than describing the actual package location".
     - Sources: https://www.uspsoig.gov/reports/audit-reports/package-tracking-messaging, summarised at https://postaltimes.com/usps-oig-package-tracking-messaging/.
   - **Lesson: a predicted milestone drawn as a confirmed one makes a tracker *wrong*, not just stale.**
2. **Long silent gaps between scans are normal.**
   - One tracker analysed 120 days of parcels across 3,200+ carriers. The median longest silence per parcel was **about 4 days**, and **more than 1 in 4** parcels went a week unscanned yet still arrived.
   - A flat 7-day "stuck" alert would therefore false-flag about 25% of healthy cross-border parcels (https://dev.to/support24htrack/the-last-scan-is-not-the-last-mile-modelling-the-carrier-handover-in-shipment-tracking-4n2b, Sept 2026) **[3rd-party]**.
   - In India, 24-48 h of hub sorting shows as "In transit"; 3+ days is the usual point to escalate, and "Manifested" for over 24-48 h usually means the seller hasn't handed the parcel over yet (https://www.trackparcel.in/carriers/delhivery) **[3rd-party]**.
3. **Coarse, carrier-specific status words.**
   - Delhivery One's seller help lists 9 coarse states, with no EDD or delay flag (https://help.delhivery.com/docs/track-orders).
   - AfterShip normalises every carrier to 9 tags plus sub-statuses such as `Exception_007` (https://www.aftership.com/docs/tracking/enum/delivery-statuses).
4. **Frozen countdowns.**
   - Deccan Chronicle (Jun 2023) found food-app "delivered in 30 minutes" messages that stayed fixed while orders ran late.
   - Swiggy moved to absolute times ("tentatively by 4 pm") (https://www.deccanchronicle.com/nation/current-affairs/250623/swiggy-delivery-time-changes-time-scam-expose.html).
5. **Promises are made before checkout and not revisited.**
   - Flipkart's Promise Engine computes the pre-order promise from inventory, serviceability, SLAs, holidays and live capacity "in milliseconds". Its documentation does not cover re-promising after the order (https://docs.flipkartcommercecloud.com/docs/digital-commerce/fulfilment/docs/overview) **[vendor claim]**.
6. **ETAs that jump.**
   - Swiggy says customers "anchor themselves to the ETA shown on the tracking screen", and that sudden jumps "cause customer anxiety and erode trust" and drive chats and calls (https://bytes.swiggy.com/how-ml-powers-when-is-my-order-coming-part-i-4ef24eae70da) (snippet).

### What the best implementations do
**Stage granularity (food and q-com)**
- **Swiggy**: the post-order ETA is four separately modelled legs, each with its own live signals (https://bytes.swiggy.com/how-ml-powers-when-is-my-order-coming-part-ii-eae83575e3a9) (snippet):
  - O2A (order to rider assigned);
  - First Mile (rider to restaurant);
  - Wait Time at the restaurant;
  - Last Mile.
- **Zomato**: the ETA is built from four parts (https://blog.zomato.com/the-accurate-eta-to-customer-satisfaction-part-one) (snippet):
  - rider travel time, **measured to entry into a geofenced drop zone** around the customer;
  - kitchen preparation time;
  - localised rider-arrival times;
  - **"real-time dynamic buffers"** for demand, traffic, closures, rider supply, weather and "real-time stress".

  Zomato says the ETA drives "order tracking, and delay communication".
- **Swiggy Instamart's public MCP `track_order`** returns:
  - `statusMessage`, `subStatusMessage`, `etaMinutes`, `etaText` and `mapInfo.riderLocation`;
  - a **server-set `pollingIntervalSeconds`**, which clients must respect.

  Source: https://mcp.swiggy.com/builders/docs/reference/instamart/track_order/. The server decides how fresh the client can be.

**How the ETA is displayed**
- **Uber Eats shows two numbers**:
  - a moving estimate;
  - a **"Latest Arrival By"** time, "confirmed when your order is accepted by the restaurant". If that time passes, the app tells the customer to contact support.

  Source: https://help.uber.com/en/ubereats/restaurants/article/delayed-order-arrival?nodeId=a733429a-624b-44b6-99b9-041a9928d089. **This is the cleanest pattern for an honest ETA: a best guess plus a commitment.**
- **Amazon** shows **2-4 hour delivery windows** in the tracker and in notifications, and warns that they can shift (https://www.amazon.com/gp/help/customer/display.html?nodeId=GK8CZJ8DR2J2WS5H) (snippet; the page returned 503).
- **DoorDash NextGen ETA** (Mar 2024) (https://careersatdoordash.com/blog/improving-etas-with-multi-task-models-deep-learning-and-probabilistic-forecasts/) (snippet):
  - a probabilistic base layer predicts the whole distribution, replacing an earlier Weibull assumption;
  - a separate **"decision layer"** chooses which quantile to show for each use case;
  - claimed result: +20% relative accuracy **[vendor claim]**.
- **Instacart** sets the buffer with quantile regression rather than a fixed pad (https://tech.instacart.com/how-instacart-delivers-on-time-using-quantile-regression-2383e2e03edb) (snippet).
- **Google Fleet Engine** (the platform behind many last-mile trackers) exposes `remainingStopCount`, ETA, remaining distance and vehicle location.
  - By default these are visible "when the task is assigned to the vehicle and when the vehicle is within 5 stops of the task".
  - Each field can instead be gated by stops, time or distance, or set to always or never.
  - Google's example: the route shows within 3 stops, the ETA shows under 5,000 m, and the stop count is never shown.
  - Source: https://developers.google.com/maps/documentation/mobility/fleet-engine/journeys/tasks/configure-tasks.
  - Together with Amazon's "10 stops away" map (earlier note), the rule is: **reveal precision only once it is trustworthy.**

**Keeping parcel ETAs fresh when scans are sparse** (beyond AfterShip AI EDD, which the earlier note covers)
- **ClickPost ML EDD** (updated Sept 17, 2026) (https://www.clickpost.ai/blog/edd-prediction-machine-learning-behind-accurate-dates) **[vendor claim]**:
  - **Inputs.** The lane (origin to destination pincode) is the strongest feature, alongside carrier and service, time, and the current network state.
  - **Training.** It trains on in-flight shipments too, because "a lane performing normally this morning may be congested by the afternoon".
  - **Re-prediction.** The EDD is re-predicted on every scan, and changes go out by WhatsApp, SMS, email and the tracking page.
  - **Two breach models:**
    - T-1 model (5 pm the day before): about 90-92% precision, 30-35% recall.
    - Same-day model (12 pm on the EDD): about 90-92% precision, 80-85% recall.
  - **Revised EDDs.** These get a 3-day buffer and reach 87-90% adherence.
  - **Case study.** EDD accuracy rose from 55% to 75%.
- **parcelLab**:
  - **Promise dates** are "92% accurate" on 1B+ shipments (https://parcellab.com/set-predictive-delivery-promise/) **[vendor claim]**.
  - **Trending Late AI** (Jul 10, 2024) shows three states: "predicted to be on time", "might be delayed" and "predicted to be delayed". The delay-probability thresholds can be set per carrier or region (https://docs.parcellab.com/docs/engage/trending-late, https://parcellab.com/predict-delivery-delays/).
  - It claims to "predict 90% of delays with over 85% accuracy" **[vendor claim]**.
- **Narvar Notify** has triggers for carrier delay, missed delivery, fulfilment delay and carrier pickup delay. Narvar Monitor sends predictive at-risk alerts (https://corp.narvar.com/notify) (snippet).

**Rules for "stuck in transit"**

| Source | Rule |
|---|---|
| AfterShip Flows | A "Trigger Status Unchanged" block with minutes, hours or days (Premium plan). Their example: 4 days stuck in InfoReceived (https://support.aftership.com/en/tracking/articles/15441725-notify-both-shopper-and-your-team-about-a-shipping-delay) (snippet). |
| AfterShip guidance | Domestic: contact the carrier after 3 days with no update. International: after 30 days (https://support.aftership.com/en/tracking/articles/15441890-why-is-my-package-stuck-in-transit-for-so-long) (snippet). |
| India practice | 24-48 h at the hub is normal; escalate at 3+ days (trackparcel.in, above) **[3rd-party]**. |
| Evidence against flat thresholds | A flat 7 days false-flags about 25% of healthy parcels (24hTrack, above). **The threshold should be per lane and per leg.** |

### Data signals
- **OMS events**: placed, accepted, packed or food-ready, handed over, manifested, pickup scan.
- **Courier scans**: the normalised tag and sub-tag, **event time vs time received**, location, and time since the last scan.
- **Per-lane gap statistics**: p50/p90 silence per leg (first mile, line-haul, destination hub, out for delivery).
- **Promise history**: the checkout promise, the carrier EDD, re-predicted EDDs, and breach probabilities.
- **Food**: stage events, rider pings, remaining stops, and drop-zone geofence entry.
- **For both**: the **age of the newest fact** and **who asserted it**.

### Pakka recommendation: "Honest Tracker"
- **Freshness and provenance on every line.** Show, for example, "Courier last scanned at Bhiwandi hub, 6:02 pm". Never show a bare "In transit".
- **Predicted milestones are drawn differently from confirmed ones** (the USPS OIG lesson).
- **Two-number ETA** (the Uber Eats pattern): a best guess shown as a range, plus a "latest by" commitment. The range narrows as the stop count or distance falls (the Fleet Engine / Amazon pattern).
- **Overdue-scan clock per lane and leg.** When the next scan is overdue against the lane's p90 gap:
  - Pakka polls the carrier (the poll-on-silence rule in `sdk-design.md` B7);
  - the tracker says "Running late at the hub; we've checked with the courier".
- **ETA jump smoothing.** Pakka publishes a new customer-facing ETA only when it moves by at least X minutes, and always with a reason. This follows Swiggy's anxiety finding **[inferred]**.

---

## 2. Rider stuck or not moving, and traffic delays

### Root cause
1. **A stationary dot is ambiguous.** The common case is waiting for food, not being stuck.
   - Zomato's old food-prep-time label mixed in rider behaviour, so it added a **Food Order Ready (FOR) button** for restaurants (https://blog.zomato.com/predicting-fpt-optimally) (snippet).
   - Uber says "GPS data is too unreliable for our needs" on its own to detect waiting (https://www.uber.com/us/en/blog/uber-eats-trip-optimization/).
2. **GPS noise.**
   - Urban GPS error can be "50 meters or more" (https://www.uber.com/us/en/blog/rethinking-gps/, Apr 2018).
   - Swiggy drops pings with accuracy worse than 100 m and cleans duplicate timestamps and impossible speeds (https://bytes.swiggy.com/solving-the-last-last-mile-maps-poi-entry-gates-f7fb0d5ddd47) (snippet).
   - Indoors (for example, malls), GPS fails outright. That is why Grab put Bluetooth beacons at pickup counters: 1,000+ in Singapore and about 100 per city in five other markets (https://www.grab.com/inside-grab/stories/these-little-bluetooth-devices-are-helping-grab-predict-food-preparation-time/, May 2023).
3. **Spoofing and cloned apps.**
   - Swiggy detects mock locations (`isFromMockProvider`).
   - It then blocks login, or warns the rider and pauses new orders, but lets an in-progress order finish (https://bytes.swiggy.com/detecting-app-cloning-location-spoofing-on-android-452dd420f390) (snippet).
4. **Batching and restaurant stress.** Swiggy classes an ETA bump from these as "justified" recalibration (Part I, above).
5. **Weather and poor maps in small towns** (Zomato Part One, above).
   - Zomato built **Weather Union**: 650+ stations in 45 cities, with a free API (https://entrackr.com/2024/05/zomato-launches-real-time-hyperlocal-weather-info-network/, May 2024).
6. **Connectivity and OS background limits.** A silent rider looks the same as a stopped rider.
   - Zomato's Pulse library keeps MQTT connections alive on Android (https://www.eternal.com/blog/pulse/, Jun 23, 2026).

### What the best implementations do: ETA and stall engineering
- **Uber**
  - **DeepETA** (Feb 2022):
    - A routing engine produces the base ETA, and ML predicts the residual.
    - The model is a linear-transformer encoder-decoder with multi-resolution geo-embeddings, trained with an **asymmetric Huber loss** so lateness can be penalised more than earliness.
    - A bias layer adjusts per segment (delivery vs rides).
    - It runs in milliseconds and is "the highest QPS model at Uber".
    - Sources: https://www.uber.com/in/en/blog/deepeta-how-uber-predicts-arrival-times/, https://arxiv.org/abs/2206.02127.
  - **Uber Eats trip-state model** (Jun 2018): a CRF over GPS, accelerometer, gyroscope and Android Activity Recognition. It infers five states: arrived at the restaurant, parked, **waiting at the restaurant**, walking to the car, en route (https://www.uber.com/us/en/blog/uber-eats-trip-optimization/).
  - **RideCheck** (Sep 2019) flags "an unexpected long stop" or an off-course trip, and pings both parties (https://www.uber.com/us/en/newsroom/ridecheck/). **This is the direct template for a rider-stall detector.**
- **Zomato**
  - Food prep time uses a **bi-directional LSTM**. MAE fell from 4.64 to 4.13 min (https://www.zomato.com/blog/food-preparation-time/) (snippet) **[vendor claim]**.
  - The FOR button gave **+9% within-5-minute accuracy**. The model also predicts rider wait and "hand-shake time" at the counter.
  - Rider travel time uses LightGBM with a Tweedie loss for the long tail (https://www.zomato.com/blog/the-accurate-eta-to-customer-satisfaction-part-two) (snippet).
- **Swiggy**
  - The four-leg model moved from gradient-boosted trees to neural networks.
  - The Last Mile leg buckets live pings into time windows, drops outliers, and computes current speed from the haversine distance between pings (Part II, above) (snippet).
  - A third-party write-up says legs are re-predicted mid-order, with an update shown only past a threshold of about 5 minutes (https://www.bhupeshkumar.blog/blogs/why-your-swiggy-eta-jumps-mid-order) **[3rd-party, unverified]**.
  - Entry gates to buildings and societies are learned from rider traces; suggested paths were followed within 50 m 92% of the time (entry-gates post, above) **[vendor claim]**.
- **DoorDash**
  - **Long-tail ETA** (Apr 2021): +10% long-tail accuracy, using real-time features and a quadratic loss. The north-star metric is on-time within ± a margin (https://careersatdoordash.com/blog/improving-eta-prediction-accuracy-for-long-tail-events/) (snippet) **[vendor claim]**.
  - **Mixture-of-experts multi-task ETA** (https://careersatdoordash.com/blog/deep-learning-for-smarter-eta-predictions/) (snippet).
  - **Auto Order Release**: the kitchen receives the order only when the Dasher enters a "release distance" geofence (https://careersatdoordash.com/blog/lifecycle-of-a-successful-ml-product-reducing-dasher-wait-times/) (snippet).
  - **Merchant "Dasher waiting" timer**: it starts when the Dasher is **within 25 m** and the prep time has passed; the target is under 2 minutes of avoidable wait (https://merchants.doordash.com/en-us/learning-center/avoidable-wait).
- **Zepto**
  - **"If a rider stays stationary for more than 10 minutes, the agent now gives an honest update and proactively offers cancellation for a full refund."**
  - This followed an incident in which the agent kept repeating a cached "arriving in 10 mins" (https://www.databricks.com/blog/evaluation-first-ai-agents-how-zepto-scales-customer-support-databricks-and-mlflow, Sept 9, 2026).
- **Zomato's support LLM** can only escalate with a predefined reason such as **`DP_MOVEMENT_ISSUE`**, which a policy layer checks against order data (https://www.together.ai/customers/zomato).
- **Fallback when the host has no ETA model**: the Google Routes API `TWO_WHEELER` mode is traffic-aware and uses India as its example. It is **beta**, must be labelled as beta to users, and bills higher (https://developers.google.com/maps/documentation/routes/route_two_wheel).

### What customers are told
- **Uber Eats**: the moving estimate plus "Latest Arrival By" (above).
  - The 2017 guarantee gave $4.99 off if a 35-minute promise was missed (https://www.uber.com/us/en/newsroom/guaranteed-delivery/).
- **DoorDash**: the help centre explains delays as the Dasher being "stuck in traffic", taking a detour, or the restaurant being busy (https://help.doordash.com/en-us/consumers/article/customer-where-is-my-order) (snippet).
- **Swiggy**:
  - absolute "tentatively by 4 pm" times (above);
  - a Rs 25 rain fee (https://www.taxscan.in/top-stories/govt-slaps-18-gst-on-swiggys-25-rain-fee-consumers-cry-foul-1433803) **[3rd-party]**.
- **Zomato**:
  - It tells Gold members, in-app, that the rain surge-fee waiver ends and that "this fee helps us compensate our delivery partners better during rains" (https://yourstory.com/2025/05/zomato-rain-fee-waiver-foodtech) (snippet).
  - In extreme rain it pauses ordering altogether: "We are not currently accepting online orders" (https://www.dnaindia.com/business/report-we-are-not-currently-accepting-orders-zomato-amid-heavy-rain-2988140) (snippet).
- **Context.** After Labour Ministry pressure over rider safety, Blinkit, Zepto, Instamart and Flipkart Minutes reportedly dropped "10-minute" branding (https://www.peoplematters.in/news/business/blinkit-zepto-pull-back-10-minute-delivery-claims-after-govt-intervention-48019) **[3rd-party]**. That makes honest delay copy more important, not less.

### Data signals
- **Rider GPS.** Fleet Engine expects an update "at least once every minute and at most once every 5 seconds" (https://developers.google.com/maps/documentation/mobility/fleet-engine/essentials/vehicles/on-demand-update-vehicle).
  - Keep the accuracy, speed, heading and mock-location flag with each ping.
- **Phone activity and sensor state**, to tell waiting apart from riding.
- **Geofence and beacon events**: merchant or store, customer drop zone, building gate.
- **Merchant events**: accepted, food ready / packed, handover, batch or reassignment.
- **ETAs**: the routing-engine ETA plus traffic, and the host's ML ETA if it has one.
- **Environment and connection**: hyperlocal rain signal, and a connection heartbeat so that "silent" is not read as "stopped".

### Pakka recommendation: "Rider Motion Watch"
- **Stall classifier.** It labels every stall with a reason and the evidence. This is my synthesis of Uber, DoorDash, Zomato and Grab **[inferred]**.

  | Reason | Rule |
  |---|---|
  | `waiting_at_merchant` | Inside the merchant geofence, and food not marked ready |
  | `stationary_en_route` | Outside all geofences, and speed ≈ 0 for N min |
  | `slow_traffic` | Rider is moving, but the ETA drifts past the threshold |
  | `finding_address` | Inside the customer drop zone, and not yet delivered (links to section 4) |
  | `signal_lost` | No ping for N seconds, or a mock location detected |
  | `weather` | Rain flag is on |
- **Each reason maps to two things**: customer copy, and an ops webhook (nudge the rider, call the rider, reassign).
- **Only `stationary_en_route` past the threshold** triggers the Zepto-style honest update with a cancel / refund / wait choice.
- **The AI agent can say "your rider is stuck" only when the classifier says so.** It then quotes the evidence, for example "hasn't moved for 9 minutes near Silk Board".
- **Thresholds scale with the host.** Swish (own riders, about 1 km radius) can use about 3 minutes. Zomato-like marketplaces need about 8-10 minutes and must separate merchant delay from rider delay.

---

## 3. Multiple or batched orders, and split shipments

### Root cause
1. **Batching is a cost decision the customer never sees.**
   - The dispatcher groups orders to lower cost per delivery (CPD).
   - To the customer, the rider goes "the wrong way", the ETA stalls, and the food arrives colder.
   - Swiggy counts a batching-driven ETA bump as "justified" recalibration (section 2). Nobody tells the customer it was justified.
2. **An order is not a shipment.**
   - One checkout can become several shipments. A tracker built at order level says "Delivered" after the first box, and the customer thinks half the order is missing.
3. **Partial fulfilment in quick commerce.**
   - Stock shown in the app is gone at pick time, so the item is dropped and refunded. The customer experiences this as a missing item.
   - Indian users say support bots "falter on nuanced problems like partially fulfilled orders" (https://www.storyboard18.com/brand-marketing/why-ai-led-customer-support-frustrates-swiggy-zomato-users-ws-l-92842.htm, Mar 2026) **[3rd-party]**.
4. **Paid "no-batching" promises that dispatch does not enforce.**
   - These create a new kind of complaint (see the Uber lawsuit below).

### What the best implementations do
**How much batching happens, and what it costs**
- Intouch Insight mystery-shopped 300 US orders. **About 12% were batched**, and **direct deliveries arrived 13 min 34 s faster**. Batched orders also scored worse on food temperature and satisfaction (https://www.intouchinsight.com/press-releases/doordash-leads-thirdparty-delivery, https://www.nrn.com/delivery-takeout-solutions/why-the-restaurant-delivery-wars-have-a-clear-winner, Sep 2024) **[3rd-party]**.

**How the platforms decide to batch**
- **Uber Eats "triple batching"** (Feb 2023) (https://www.uber.com/au/en/blog/triple-batching-for-restaurants/) **[vendor claim]**:
  - up to 3 orders per courier;
  - weighs merchant-to-eater distance, prep times, predicted delivery time and courier supply;
  - "limit[s] orders from being batched if delivery times are expected to be extensive".
- **DoorDash DeepRed**:
  - ML predicts ready time, travel time and the chance a Dasher accepts;
  - a mixed-integer program then decides assignment and batching, and may deliberately delay dispatch.
  - Source: https://careersatdoordash.com/blog/using-ml-and-optimization-to-solve-doordashs-dispatch-problem/ (snippet).
- **Swiggy** (Gurobi Days, Apr 2023; primary PDF, https://cdn.gurobi.com/wp-content/uploads/SwiggY.pdf):
  - Each candidate batch is scored against delivering the orders separately.
  - Batching is reduced when demand stress is low, when a batch "has worse CX (based on delay beyond promise)", or when the CPD saving is small.
  - Instamart batches are capped by weight, item count, number of orders, and pickup/drop time windows.
  - Batch pickup is held "till the SLA time".
- **Swiggy's batch-specific ETA models** gave about **6% more deliveries within the estimate** (CODS-COMAD, Jan 2021: https://dl.acm.org/doi/10.1145/3430984.3430999) **[vendor claim]**.
- **Swiggy's IEEM 2022 paper** found that more priority orders degrade standard orders' experience (https://ieeexplore.ieee.org/document/9989782/).
- **Zepto started batching in Aug 2025**, for orders within 500 m during surges, and claims "no impact on delivery timelines" (https://www.business-standard.com/amp/industry/news/zepto-blinkit-instamart-club-orders-to-cut-costs-boost-efficiency-125110401584_1.html) (snippet) **[vendor claim]**.

**How the tracker explains batching**
- **DoorDash** shows customers that their Dasher is delivering another order (https://financialpanther.com/do-doordash-drivers-pick-up-multiple-orders/) **[3rd-party; exact wording unconfirmed]**.
- **Uber Eats** has a 5-stage bar plus "Latest Arrival By" (https://www.restaurantdive.com/news/uber-eats-boosts-delivery-tracker-transparency-with-colorful-animations/552513/). It has no documented batching message.
- **Swiggy and Zomato**: no official in-tracker batching copy found **[unverified]**.
  - Zomato's terms only say an order may be "grouped or batched with another order" (https://www.zomato.com/policies/terms-of-service/) (snippet).
- **Google Fleet Engine's `remainingStopCount`** is a standard way to say "2 stops before yours" without exposing other addresses. It can be hidden, or shown within N stops (https://developers.google.com/maps/documentation/mobility/fleet-engine/journeys/tasks/configure-tasks).

**Customer controls: batching as an explicit, priced choice**
- **Uber Eats Priority.**
  - At launch (Jun 2020) it promised "no other Uber Eats orders delivered before yours" (https://www.uber.com/us/en/newsroom/introducing-priority-delivery-and-restaurant-rewards-programs/).
  - The current help page is narrower: the order is "dropped off first" in a batch.
  - The same page offers **"No Rush"**, a discount for sharing a courier (https://help.uber.com/en/ubereats/restaurants/article/fonctionnement-des-diff%C3%A9rentes-options-de-livraison?nodeId=b11a4cf0-efb6-4334-96b4-b6ad34481253).
  - A **class action filed Jul 27, 2026** (N.D. Cal.) alleges that couriers cannot see which orders are priority, and that refunds were refused even after the failure was admitted (https://www.nrn.com/restaurant-technology/uber-eats-sued-over-priority-delivery-fees).
- **DoorDash Express.**
  - DoorDash says the assignment system "doesn't combine it with other orders" (https://about.doordash.com/en-us/news/how-doordash-is-different) (snippet) **[vendor claim]**.
  - A driver blog says Dashers aren't told an order is Express (https://www.ridesharingdriver.com/doordash-express-delivery/) **[3rd-party]**.
- **Zomato Priority (India).**
  - Rs 19-29, "up to five minutes sooner".
  - The customer chooses priority "or have [the] order grouped with others".
  - Gold members objected to paying extra (May 2024: https://www.republicworld.com/india/zomato-expands-priority-delivery-service-amid-controversy-over-charges).
- **Swiggy**: no confirmed consumer no-batching product **[unverified]**.
- **Lesson.** A priority promise needs:
  - a hard rule in dispatch;
  - a flag the rider can see;
  - automatic verification from GPS and events, with a refund when the promise fails.

**E-commerce split shipments**
- **Flipkart's seller API** models Order, Order Item and Shipment separately:
  - "A single customer order can be splitted into multiple shipments even though all the products are from the same seller."
  - Packed, shipped and delivered events carry **both item ID and shipment ID**.
  - A "Dispatch Dates Changed" event works as a delay signal.
  - Sources: https://seller.flipkart.com/api-docs/order-api-docs/OMAPIOverview.html, https://seller.flipkart.com/api-docs/order-api-docs/NotifIntro.html.
- **Amazon.in**: each item can have its own date and tracking, and "If you received a package that's missing an item, it may have been shipped separately" (https://www.amazon.in/gp/help/customer/display.html?nodeId=GENAFPTNLHV7ZACW) (snippet).
- **Amazon Day consolidation**: Amazon claims 20% fewer boxes (https://www.aboutamazon.com/news/operations/what-is-amazon-day-delivery) **[vendor claim]**. Consumer Reports volunteers found it failed to consolidate more than 80% of the time (Jul 2023: https://urbanfreightlab.com/in_the_media/we-tried-combining-amazon-deliveries-with-amazon-day-shipping-often-it-didnt-work/) **[3rd-party]**.
- **Fluent Commerce** advises telling the customer about a split immediately and offering to consolidate (https://fluentcommerce.com/resources/blog/7-questions-retailers-should-ask-about-split-shipments/) **[3rd-party]**.

**Quick-commerce partial fulfilment**
- **Swiggy's refund policy** says the buyer is contacted when an item is unavailable and may cancel for a full refund (https://www.swiggy.com/refund-policy) (snippet).
- **Fill rates**: Blinkit reportedly expects brands to keep fill rate above 90%, while individual dark stores can run around 72% (https://base.com/en-IN/blog/quick-commerce-for-d2c-brands-the-complete-guide-2026/) **[3rd-party]**.

### Data signals
- **Dispatch**: `batch_id`, this order's position, picked/dropped state per order, planned stop sequence, priority flag, added minutes from the batch.
- **Location**: rider GPS, and distance to this customer vs to the next stop (to detect "moving away").
- **OMS**: order → shipment → line item, with per-shipment and per-item events (packed, shipped, OFD, delivered, dispatch date changed, item cancelled or out of stock).
- **Refunds**: refund ledger per line item.

### Pakka recommendation: "Multi-drop and Split Explainer"
- **Batched food orders.**
  - If the host sends the stop sequence, the tracker says "Your rider is dropping 1 other order first, about 4 minutes from you".
  - The host can switch this to generic copy or hide it.
  - When the rider moves away from this customer, Pakka explains it *before* the customer notices (the labour-illusion finding in section 5).
- **Priority verification.**
  - If the customer paid for priority or Express, Pakka checks the stop sequence and GPS. If another drop came first, it refunds the fee automatically (the Uber lawsuit lesson).
- **Split parcels.**
  - The tracker shows an **item-to-shipment map**: "2 of 3 items delivered; the serum ships separately, arriving Thu".
  - The agent checks this map first when someone says "I only got half".
  - On a "dispatch date changed" event, Pakka sends a split-specific notice.
- **Partial fulfilment.**
  - The notice and agent answer list the dropped items, the refund amount and the refund reference **before** delivery, so the customer never discovers the gap at the door.
- **Several active orders.**
  - The agent picks the order by recency and state, and asks "which order?" only when it is genuinely ambiguous.

---

## 4. Bad address resolution in India

### Root cause
1. **The address is written for a person, not a machine.** Sources: Rustogi et al., Jan 2018, lead author then heading data science at Delhivery (https://arxiv.org/pdf/1801.06540); DoP's DHRUVA policy, May 2025 (https://www.indiapost.gov.in/documents/offerings/intiatives/IP_30052025_Digipin_English.pdf).
   - **About 80% of addresses are written relative to a landmark 50-1,500 m away** (average about 400 m), "so landmarks don't significantly improve resolution".
   - Only about 30% of addresses are structured, and about 70% of sites have no street name.
   - **20-30% of written pincodes are wrong.**
   - The average pincode covers about 170-179 km².
   - The DHRUVA policy estimates poor addressing costs India **$10-14B a year (about 0.5% of GDP)**.
2. **The map pin is unreliable too** (same paper).
   - Of 500k Delhivery-captured GPS points, only 50% reported accuracy within 50 m.
   - **Only 25% of customers dropped a pin within 100 m of the ground truth.**
   - Swiggy cites multipath errors off tall buildings, with pins 117-195 m off (https://bytes.swiggy.com/address-correction-for-q-commerce-part-1-location-inaccuracy-classifier-e72b88a33d2f) (snippet).
3. **Cold-start addresses have no history to learn from.**
   - Amazon's example address has only a locality and a landmark.
   - Once an address has deliveries, geocoding "reduces to aggregation of past delivery scans" (EMNLP 2022: https://aclanthology.org/2022.emnlp-industry.33.pdf).
4. **Vertical and gated ambiguity.**
   - A roughly 4 m grid code "does not tell the user the address of a specific place" in a tower (https://www.medianama.com/2025/07/223-mapmyindias-mapplspin-india-posts-digipin/).
   - Map routing often ignores a society's real entry gate (https://bytes.swiggy.com/solving-the-last-last-mile-maps-poi-entry-gates-f7fb0d5ddd47) (snippet).
5. **Failures are mislabelled.**
   - An address failure surfaces as a "customer not available" NDR, a rider call, or, on Zomato, a cancellation "not attributable to Zomato" with no refund (https://www.zomato.com/policies/terms-of-service/) (snippet).
   - Each of these becomes a WISMO contact or a refund dispute, not an address fix.

### What the best implementations do
**Government stack (India Post)**
- **DIGIPIN** (technical doc, Mar 2025: https://www.indiapost.gov.in/documents/offerings/intiatives/DIGIPIN_Technical_document.pdf):
  - built with IIT Hyderabad and NRSC-ISRO;
  - **10 characters** from a 16-symbol alphabet; level-10 cells are **about 3.8 m x 3.8 m**;
  - a pure function of latitude and longitude that stores no personal data;
  - open source under Apache-2.0 (https://github.com/INDIAPOST-gov/digipin).
  - The "Know Your DIGIPIN" and GNSS PIN-boundary portals launched May 27, 2025 (https://www.insightsonindia.com/2025/05/28/department-of-posts-new-digital-platforms/) **[3rd-party summary of PIB]**.
- **DHRUVA** (May 2025 policy):
  - a UPI-like label (`name@dhruva`) that resolves, with consent, to the descriptive address plus the DIGIPIN;
  - the policy's own logistics example: "As more deliveries are completed successfully at a given address, its confidence score within DHRUVA improves".
- **Draft Post Office Act amendment** (Dec 2025): address service providers and validation agencies; addresses treated as personal data under the DPDP Act (https://www.medianama.com/2025/12/223-dhruva-digital-address-system-india-post/).
- **Pilot**: about 30 users in 5 states in May 2026, with a nationwide rollout expected in about 18 months (https://www.onmanorama.com/news/business/2026/05/09/india-post-digital-ids-precision-delivery.html) **[3rd-party]**.
- **Adoption**:
  - MapmyIndia integrated DIGIPIN (Jul 2025), with its Mappls PIN adding floor and apartment.
  - **No e-commerce mandate, and no Swiggy, Zomato, Amazon or Flipkart adoption found** **[unverified]**.

**Google**
- **Address Descriptors** (GA in India Mar 25, 2025: https://developers.google.com/maps/documentation/geocoding/release-notes):
  - `extra_computations=ADDRESS_DESCRIPTORS` returns **up to 5 landmarks**, each with straight-line and travel distance and a `spatial_relationship` (NEAR, BESIDE, ACROSS_THE_ROAD, BEHIND and others);
  - also **up to 3 areas**, each with a containment value;
  - request/response doc: https://developers.google.com/maps/documentation/geocoding/address-descriptors/requests-address-descriptors.
- **Address Validation API for India**: in preview since Jul 2024 and **still pre-GA as of Sept 24, 2026** (https://developers.google.com/maps/documentation/address-validation/coverage).
- **Reference architecture** (updated Sept 24, 2026: https://developers.google.com/maps/architecture/india-address-feedback). An LLM flow that:
  - moves "near/landmark" text into a descriptors field;
  - flags a missing pincode;
  - shows a **dual pin** (original vs cleaned) so the user can spot the gap.

**Platforms**
- **Swiggy Address Location Correction** (AIMLSystems '22: https://dl.acm.org/doi/10.1145/3564121.3564800):
  - a self-supervised classifier flags pins that disagree with the address text (**84.5% precision, 49% recall**);
  - a geocoder then corrects them.
  - Entry gates and paths are learned from rider traces (92% followed within 50 m) **[vendor claim]**.
- **Zomato**:
  - **voice delivery instructions** (Sep 2020: https://officechai.com/startups/zomatos-new-feature-allows-users-add-voice-instructions-delivery-personnel/);
  - its own **building footprints**, which drive **dynamic address forms** (tower, floor) so riders "don't have to call and confirm the lane, tower, or floor" (https://www.zomato.com/blog/to-help-us-locate-you-better/) (snippet);
  - Mygate integration to pre-approve the rider at a society gate (https://mygate.com/blog/society-focus/silences-deliveries/).
- **Amazon**: metric learning supervised by past delivery scans gave **22% fewer delivery defects** and 43% lower median error on hard Indian addresses (EMNLP 2022, above).
- **Meesho GeoIndia LLM**: +20 pp geocoding accuracy and more than 50% fewer misroutes (https://www.cioandleader.com/where-ai-meets-geography-rethinking-logistics-for-bharat/, Sept 2026) **[vendor claim]**.
- **Masked rider-customer calls** are standard (https://exotel.com/use-cases/number-masking/). **No public figure exists** for how often riders call for directions **[unverified]**.

**what3words**
- **Adoption in India**:
  - Ecom Express, whose own data puts **15% of returns** down to incorrect or insufficient addresses (https://what3words.com/news/logistics/ecom-express-partners-with-what3words-for-efficient-last-mile-deliveries) **[vendor claim]**;
  - DTDC (Dec 2022);
  - iThink Logistics.
- **Critiques**:
  - it is proprietary and patented;
  - a PLOS ONE analysis estimates about **two-thirds of addresses have a confusable twin** (https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0292491);
  - DHRUVA explicitly argues against closed address systems.

**Address-intelligence vendors** (all numbers **[vendor claim]**)

| Vendor | Mechanism | Claim |
|---|---|---|
| Delhivery Maps (AddFix; Naksha LLM, Jun 2026) | Parsing, validation, and **verification against Delhivery's own delivery history**; returns an "error radius" (https://www.delhivery.com/maps/developer) | Built on 4B+ deliveries |
| Shiprocket Address Intelligence | NLP plus spatial reasoning, learned from delivery outcomes (https://www.shiprocket.in/blog/shiprocket-address-intelligence/amp/) | 72.69% within 100 m, 90.57% within 500 m, under 200 ms |
| GoKwik RTO API | Scores each COD order before payment options are shown. Address-model reasons include "Address too short", "Address incomplete" and "Address or customer seems fake" (https://cdn.gokwik.co/rto-doc/rto-predict-api.pdf) | Addresses under 10 characters drive 35% (fashion) to about 60% (electronics) of RTOs (https://www.gokwik.co/blog/address-prefill) |
| LogiNext | Four geocode states: System, Approximate (review), Manual (rider-corrected pins reused) and Not Geocoded (blocked from dispatch) (https://www.loginextsolutions.com/blog/geocoding-intelligence-that-reduces-exceptions-before-they-happen/) | Address errors cause "nearly 30%" of urban last-mile exceptions |
| ClickPost | Pincode and address checks at checkout; NDR recovery (https://www.clickpost.ai/blog/ai-in-reducing-ndr) | RTO -20-40% |
| Latlong.ai | India geocoder (https://www.latlong.ai/pages/Blog/B11) | 297 m mean error vs 1,280 m for Google, on its own test set |

**RTO rates and cost**
- **Rates**:
  - COD RTO averages **20-25%**, and up to 40% in fashion (https://www.shiprocket.in/blog/rto-protection-for-sellers/) **[vendor claim]**;
  - COD about 26% vs prepaid under 2% (https://www.clickpost.ai/blog/what-is-ndr-rto-in-ecommerce) **[3rd-party]**.
- **Cost per RTO**:
  - about **Rs 160** in direct logistics (Rs 85 forward + Rs 75 return);
  - about **Rs 561** fully loaded, once packaging, damage, blocked capital and wasted CAC are added (https://www.hillteck.com/blog/rto-cost-indian-d2c-brands.html) **[3rd-party]**.
- **Share of RTO caused by bad addresses**: estimates range from 15% to 35%+, and every one is vendor-reported. The widely repeated "45%" figure has **no source** **[unverified]**.

### Data signals

| Signal | Use |
|---|---|
| Geocoder output with **confidence / granularity** (rooftop … pincode) and error radius | Decide how to dispatch; trigger a confirmation |
| **Pin vs typed-address geocode distance**; landmark descriptors | Flag a mismatch at capture (Swiggy classifier; Google dual pin) |
| Device GPS accuracy at pin capture; whether the pin was dragged by hand | Weight how far to trust the pin |
| **Rider GPS trace at the attempt and at the "delivered" scan** | Tell "address not found" apart from a fake attempt; learn gates |
| **Past successful drop points** per customer and building | A learned geocode whose confidence grows with each delivery (Amazon, DHRUVA) |
| Instruction text or voice note; tower and floor fields | Rider guidance; completeness score |
| Address-text quality: length, flat number present, pincode matches the point | RTO / NDR risk (GoKwik features) |
| Masked-call logs and NDR reason codes | Proxy for "couldn't find"; WISMO prediction (no public benchmark, so instrument it) |
| DIGIPIN, Mappls PIN or Plus Code, if supplied | A precise fallback anchor |

### Pakka recommendation: "Address Confidence and Fix"
- **Pre-dispatch address score** from the signals above.
  - **Low score**: Pakka sends a WhatsApp **location request** or opens an in-app confirm screen, showing a **dual pin** plus Google address descriptors ("Is this 50 m behind Hanuman Temple?").
    - The WhatsApp request has a native "Send location" button and works only within 24 h of the user's last message, so outside that window a template has to go first (https://docs.360dialog.com/docs/messaging/message-types/interactive/location-request-message).
    - The customer can also add tower/floor, a voice note or a DIGIPIN.
  - **COD orders with a low score**: the host can require confirmation or push the customer to prepay (the GoKwik pattern).
- **"Rider can't find it" guard.**
  - Before an attempt can be marked failed, Pakka checks the rider's GPS against the pin and requires a logged masked call or WhatsApp location request.
  - An NDR reason of "address issue" opens a fix flow instead of sending a blind reattempt to the same wrong place.
- **Learned drop points.**
  - Every successful delivery updates a per-customer and per-building drop point with a confidence score, the same loop DHRUVA describes.
  - Rider-corrected pins are stored and reused (the LogiNext pattern).
- **Evidence in the agent's answer.**
  - For example: "The rider reached your pin at 4:12 pm; it is 600 m from the typed address. Which one is right?"
  - This avoids Zomato's "not attributable" dead end.

---

## 5. Proactive communication

### Root cause
- **Customers discover delays by watching the ETA.**
  - Swiggy says the tracking-screen ETA "shapes how often the customer reaches out via chat or call and/or decides to cancel" (https://bytes.swiggy.com/how-ml-powers-when-is-my-order-coming-part-i-4ef24eae70da) (snippet).
- **Messages fire on milestones, not on drift.**
  - Nothing triggers when the prediction starts to slip away from the promise.
- **No reason is given, or the only "reason" is a fee.**
  - Rain and surge fees appear on the bill, but are not tied to the ETA.
  - A Bengaluru customer was charged a rain surge for 4 hours under clear skies, and Zomato did not explain the trigger (https://www.dnaindia.com/viral/report-bengaluru-man-alleges-zomato-charged-rain-surge-fees-even-after-clear-skies-company-responds-3159595, Jun 2025).
- **Optimistic pre-order promises.**
  - **Blinkit dropped its 10-minute promise on Jan 13, 2026** after the labour ministry intervened (https://thelogicalindian.com/after-government-intervention-blinkit-scraps-10-minute-delivery-zepto-swiggy-likely-to-follow/).
  - In the Apr 2026 heatwave, rider shortages persisted even with Rs 8-15 extra incentives per order (https://newskarnataka.com/business/heatwave-delays-zepto-blinkit-deliveries/29042026).

### What the best implementations do
**Research on how to word a delay notice** (the most useful new finding)
- **Jenkins, Fombelle and Steffel, *Journal of Consumer Research*, Jun 2026** (field study with a US food-delivery firm, orders up to 15 minutes late; https://phys.org/news/2026-03-customer-backfire.html, https://hbr.org/2026/04/when-apologizing-to-customers-hurts-more-than-it-helps):
  - **Proactive apologies *lowered* reorders within 90 days**, and cut order count and spend.
  - **Neutral delay notices did better than apologies.**
  - Apologise only when the customer already knows (after a complaint or cancellation), or when the failure is serious.
- **Halperin, Ho, List and Muir, *Economic Journal* 2022** (1.5M Uber riders with late trips; https://www.nber.org/papers/w25676):
  - an apology **plus a coupon** worked best;
  - apologising and then failing again was worse than not apologising;
  - explicit promises were the worst option.
- **Buell and Norton, *Management Science* 2011, "labor illusion"** (https://pubsonline.informs.org/doi/10.1287/mnsc.1110.1376): people value a service more, even with a longer wait, when it shows the work being done. This supports "rider is waiting at the restaurant" or "dropping a nearby order" over a bare countdown.
- **Salari, Liu and Shen, MSOM 2022** (https://pubsonline.informs.org/doi/10.1287/msom.2022.1081): forecasting the full delivery-time distribution lets a retailer set promises that maximise satisfaction and sales.

**Channels and costs in India**
- **WhatsApp**:
  - Meta moved to **per-message pricing on Jul 1, 2025** (https://developers.facebook.com/docs/whatsapp/pricing/).
  - Utility templates are **free inside the 24-hour customer-service window**.
  - India list rates: **utility Rs 0.11, marketing Rs 0.78, authentication Rs 0.12** (https://www.medianama.com/2025/07/223-whatsapp-business-per-message-pricing-india/).
  - Status webhooks report sent, delivered, read and failed (https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks/).
- **Delhivery's WhatsApp service** triggers on manifested, picked up, OFD, OFD with OTP, delivered, and NDR verification (https://help.delhivery.com/docs/communication).
  - Price per message: **Rs 1 standard, Rs 1.50 OFD, Rs 2 OFD with OTP**; NDR messages are free.
  - That is about 9-18x Meta's utility rate, which is the case for a brand sending directly.
- **Amazon.in** sends WhatsApp delivery updates by default; customers reply STOP to opt out (https://www.amazon.in/gp/help/customer/display.html?nodeId=TDpudWaaWHFdZfYRft) (snippet).
- **Amazon Shipping India's SMB guidance** (May 2026: https://shipping.amazon.in/blog/proactive-delivery-updates-indian-smbs) **[vendor claim]**:
  - one channel per milestone, across 6 milestones;
  - **send the delay alert before the EDD is missed**;
  - send a WhatsApp message **within 30 minutes of a failed attempt**;
  - it also cites a national RTO of about 23%.
- **Swiggy** began WhatsApp order updates in 2018, with SMS as the fallback (https://www.gizbot.com/apps/news/swiggy-will-soon-begin-using-whatsapp-order-updates-instead-of-sms-051030.html).

**Trackers that show the work**
- **Domino's tracker update** (Mar 24, 2026: https://www.prnewswire.com/news-releases/dominos-updates-its-iconic-industry-first-tracker-for-an-even-better-customer-experience-302722163.html) **[vendor claim]**:
  - stages Placed, Make, Deliver/Pick Up, "Mmm!", with sub-details (oven time, driver departure, GPS);
  - an AI engine that "blends multiple real-time inputs from store team members with machine learning models".
- **Zepto** pairs its honest delay update with one concrete option (cancel for a full refund) (section 2).
- **Parcels: predict the breach before it happens.**
  - ClickPost and parcelLab both predict breaches ahead of time (section 1).
  - ClickPost claims its notifications cut WISMO **60%** (https://www.clickpost.ai/notifications) **[vendor claim]**.
  - Decagon claims proactive notices remove **30-50%** of WISMO contacts (https://decagon.ai/glossary/what-is-wismo-where-is-my-order) **[vendor claim]**.

**Guarantees keep promises honest, but they are costly.** Zomato ended the Gold on-time guarantee in Nov 2023 as a cost driver (covered in the earlier note).

### Data signals
- **ETA**: promised vs live predicted ETA and its uncertainty; the breach probability.
- **Reason**: rider state (at restaurant, batch stop n), kitchen or store stress, and the rain or surge flag with its zone and time window.
- **Parcels**: courier scans, NDR codes, and "dispatch date changed" events.
- **Delivery of the notice**: channel opt-ins; WhatsApp window state (cost); sent/delivered/read/failed receipts; SMS/DLT fallback.
- **Outcome**: message IDs joined to later contacts, cancellations and reorders, to measure deflection and to test neutral notices against apologies.

### Pakka recommendation: "Promise Keeper"
- **Notify on predicted breach, not actual breach.**
  - The trigger is a breach probability above the threshold, or ETA drift beyond N minutes.
  - The notice carries a **specific reason**, the new window, and **one** action (wait, cancel or reschedule).
- **Tone follows the research.**
  - A **neutral** status update for small delays (under about 15 minutes, or `apology_threshold`).
  - An apology **plus** a capped credit only when the delay is large, or the customer has already contacted support.
  - Never promise twice.
- **Channel ladder with caps.**
  - Push → WhatsApp utility template (Rs 0.11, or free inside the 24 h window) → SMS.
  - Frequency caps and quiet hours apply.
  - Pakka stops escalating once the customer opens the tracker or replies.
- **Honest fees.**
  - When a rain or surge fee applies, the tracker and agent show the triggering signal ("heavy rain in Koramangala since 7:10 pm").
- **One reason taxonomy** shared by the tracker, the notices and the AI agent.
- **Built-in A/B testing** of notice variants on contacts, cancellations and 90-day reorders, so each host learns its own best wording.

---

## 6. Conversational WISMO: how AI agents answer "where is my order"

### Root cause
- **The answer is a lookup plus judgement.** Most bots do only the lookup, and often from a stale copy of the data.
  - Zepto's tracking agent repeated "arriving in 10 mins" while "reading cached data" as the rider sat still (https://www.databricks.com/blog/evaluation-first-ai-agents-how-zepto-scales-customer-support-databricks-and-mlflow, Sept 9, 2026).
- **Self-service rarely closes the loop.** A Gartner survey of 5,728 customers (Dec 2023) found (https://www.gartner.com/en/newsroom/press-releases/2024-08-19-gartner-survey-finds-only-14-percent-of-customer-service-issues-are-fully-resolved-in-self-service):
  - **only 14% of service issues are fully resolved in self-service**;
  - **only 36% even for issues customers call "very simple"**;
  - 45% said the company "didn't understand what they were trying to do".

  The survey is independent, but not WISMO-specific.
- **Indian bots break on anything unscripted.** Users say the bots work for scripted cases but "falter on nuanced problems like partially fulfilled orders or delivery disruptions" (https://www.storyboard18.com/brand-marketing/why-ai-led-customer-support-frustrates-swiggy-zomato-users-ws-l-92842.htm, Mar 21, 2026) **[3rd-party]**.
- **Legal exposure.** In *Moffatt v. Air Canada* (2024 BCCRT 149, Feb 14, 2024), the tribunal held the company liable for its chatbot's wrong statement and rejected the idea that the bot was "a separate entity" (https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-february/bc-tribunal-confirms-companies-remain-liable-information-provided-ai-chatbot/). **A bot that invents an ETA is making a promise on the company's behalf.**

### What the best implementations do
(Headline numbers already in the earlier note, such as Nugget's automation and Swiggy's Databricks agent, are not repeated here.)

- **Zepto's "WIMO" specialist agent** (Sept 9, 2026, Databricks link above).
  - **Routing.** A router sends each ticket to one of seven vertical agents: **WIMO (tracking/ETA)**, Missing, Expiry, Returns, Quality, Unable to Pay, General. Horizontal agents check images. "The router can hand off to a human at any point."
  - **The stale-ETA fix.** Automated scorers caught the repeated-ETA bug within 5 minutes. The team then added multi-step state validation and the rule that a rider stationary for more than 10 minutes gets an honest update and a cancel-for-refund offer.
  - **Evaluation.**
    - Tracing on every call.
    - Deterministic checks first; LLM judges only where judgement is needed, calibrated to 80-90% agreement with humans.
    - The golden set grew from 500 to 5,247 examples, and the gap between dev and prod scores shrank from 8 points to 0.4.
    - About 14,400 traces are sampled per day.
  - **Results.** 80%+ of more than 100,000 daily tickets fully handled by AI; cost -65%; CSAT +20% **[vendor claim]**.
- **Zomato's function-calling bot** (https://www.together.ai/customers/zomato).
  - **Three stages.** Intent classification, then **targeted API calls that fetch only what the intent needs** (for delivery timing, only location and ETA, not the full order), then JSON-to-text.
  - **Escalations** must carry a predefined reason code (for example, `DP_MOVEMENT_ISSUE`), which is validated against order data.
  - **Actions** need a user-confirmation pop-up.
  - **Models.** A 70B model for intent and an 8B model for chat.
- **Fin (formerly Intercom).**
  - **How it gets order data.** A "data connector" is one configured API call. "'Where's my order?' (requires a single API call to retrieve order status)". Identity verification sits in Procedures (https://fin.ai/help/en/articles/12646350-fin-tasks-and-data-connectors-explained).
  - **Illustrative maths.** About 30% of 10k monthly tickets are WISMO; "↓ 80%" WISMO tickets; cost per ticket $4.50 → <$1 (https://fin.ai/learn/automate-order-tracking-ai-agents) **[vendor claim, illustrative]**.
- **Gorgias.**
  - **Shipment-state gating.** Self-service "Track" and the AI Agent read Shopify and 3PL tracking, and **gate the offered actions by shipment status** (https://helpcenter.gorgias.com/en-US/articles/ai-agent-and-automations-135134).
  - **Automation claims.** Gorgias claims **up to 60% of email and chat** automated overall. That figure is **not WISMO-specific**, although SEO pages misquote it as one (https://www.gorgias.com/ai-agent/support-skills) **[vendor claim]**. A review says the self-service portal alone "can automate up to 30% of live chat ticket volume" (https://www.eesel.ai/blog/gorgias-ai-shopify-integration) **[3rd-party]**.
- **Decagon.**
  - **Recommended approach.** Carrier APIs for "current shipment status, last scan location, and estimated delivery date", plus automatic exception workflows.
  - **Claims.** **90-95% deflection on WISMO** (Decagon glossary, above) **[vendor claim]**.
- **Richpanel.**
  - **Claim.** "50% autonomous resolution at maturity across 3,000+ brands" (https://www.richpanel.com/learn/ai-customer-service-statistics-2026) **[vendor claim]**.
  - **Why it matters.** It is a useful counterweight to the 80-95% headlines.
- **Klarna.**
  - **Launch claim.** Two-thirds of chats in month one, Feb 2024 (https://www.prnewswire.com/news-releases/klarna-ai-assistant-handles-two-thirds-of-customer-service-chats-in-its-first-month-302072740.html) **[vendor claim]**.
  - **Reversal.** In **May 2025** it began re-hiring humans. The CEO said cost had been "a too predominant evaluation factor" and "there will be always a human if you want" (https://www.customerexperiencedive.com/news/klarna-reinvests-human-talent-customer-service-AI-chatbot/747586/).
- **New channel: the customer's own AI assistant.**
  - **Swiggy MCP** (Jan 27, 2026) exposes `get_food_orders`, `track_food_order`, `get_food_order_details` and `get_food_delivery_status` ("latest delivery ETA and terminal delivery state") to ChatGPT, Claude and Gemini (https://mcp.swiggy.com/builders/docs/reference/food/, https://www.swiggy.com/corporate/press-release/swiggy-now-lets-you-order-food-dineout-and-shop-on-instamart-directly-inside-chatgpt-and-claude/).
    - It is COD only, and orders cannot be cancelled (https://github.com/Swiggy/swiggy-mcp-server-manifest).
  - **Zepto** runs an official MCP; no official **Blinkit** MCP had been verified as of Sept 23, 2026 (https://trucommerce.ai/insights/india-quick-commerce-agentic-mcp) **[3rd-party]**.
- **Measure the right thing.** WISMOlabs defines **WISMO rate = WISMO inquiries / shipments x 100** (https://wismolabs.com/what-is-wismo/, Jul 2026) **[vendor claim]**:

  | Band | WISMO rate |
  |---|---|
  | World class | under 2% |
  | Healthy | 3-4% |
  | Average | 5-8% |
  | Crisis | over 15% |

  This is a better north star than "deflection", which can reward a bot that makes people give up.

### Data signals

| Question | Minimum data | Better data |
|---|---|---|
| "Where is it?" (parcel) | Order → shipments → AWB; latest normalised status and timestamp | Scan history, last scan location, re-predicted EDD and breach probability, open exceptions |
| "Where is it?" (food / q-com) | Stage and promised ETA | Rider GPS (last fix and its age), live ETA, stall-classifier reason, batch position |
| "Why is it late?" | Promised vs current ETA | A reason code with evidence (prep delay, stall, rain, hub delay, address) |
| "Which order?" | Session identity (app login, WhatsApp number, email) → active orders | Recency and state ranking |
| "Can you do something?" | Policy table and action APIs | Trust/risk score, remedy history, remedy cost |
| Every answer | **Age of the newest fact** | Provenance (carrier, rider app, model, merchant) |

### Pakka recommendation: the "grounded answer contract"
1. **One tool, sliced by intent.**
   - `get_order_truth(order_ref, slice)` returns the Pakka view model.
   - Like Zomato, the agent fetches only the slice the intent needs: `eta`, `rider`, `shipments`, `address` or `refund`.
2. **An answer contract enforced in code, not in the prompt.** Every WISMO reply must include:
   - the state;
   - an ETA **only if** one exists from the carrier or a model, shown as a range;
   - the time of the last confirmed event;
   - the next step, and when Pakka will follow up.

   A deterministic checker blocks any date or time that is not in the tool output (the Air Canada lesson).
3. **Staleness guard** (the Zepto lesson).
   - If the newest fact is older than `max_fact_age`, the agent says so and re-polls.
   - It never repeats a stale ETA.
4. **Reason-coded escalations and remedies** (the Zomato lesson). They must use a code from a fixed list, and Pakka checks the code against the detector signals before acting.
5. **Channels.** In-app, WhatsApp (the phone number is the identity), email, voice, and an **MCP server**, so a customer's own assistant can ask "where is my order" (the Swiggy and Zepto precedent).
6. **KPIs.**
   - Headline metrics:
     - WISMO rate per 100 orders;
     - repeat contact on the same order within 24 h;
     - stale-answer rate;
     - broken-promise rate (the agent said X, and X didn't happen);
     - time to a human handoff.
   - Deflection is reported, but it is not the headline.

---

## Pakka offer

Integration effort assumes the host already sends order and shipment events to Pakka (`sdk-design.md` B7). Rough sizing **[inferred]**:
- **S** = a config change plus a mapping, a few days.
- **M** = a new data feed, 1-2 weeks.
- **L** = a new real-time feed plus ops wiring, 3-6 weeks.

| Problem | Pakka feature | Config knobs (tenant YAML) | Data needed | Integration effort (Smytten / Swish / Zomato) |
|---|---|---|---|---|
| 1. Vague, stale or wrong tracker | **Honest Tracker**: freshness and provenance on every line; predicted vs confirmed milestones; a two-number ETA (range plus "latest by"); overdue-scan clock and poll-on-silence; ETA jump smoothing | `eta.display: range\|point\|range+latest_by`, `eta.range_quantiles: [p20,p80]`, `eta.min_change_to_publish: 5m`, `stall.threshold: lane_p90\|fixed:72h`, `milestones.show_predicted: true`, `freshness.badge_after: 2h` | Courier scans (event time and received time); carrier EDD; lane history; OMS stage events; host or Pakka EDD model | **S** (aggregator webhook) / **S** / **S** (host keeps its map; Pakka supplies the truth and copy) |
| 2. Rider stuck or delays | **Rider Motion Watch**: a stall classifier (waiting at merchant, stationary en route, slow traffic, finding address, signal lost, weather) with evidence; ops webhooks; honest update with cancel/refund/wait past the threshold | `rider.stationary_minutes: 3 (Swish) \| 8 (Zomato)`, `geofence.merchant_m: 50`, `geofence.drop_zone_m: 150`, `eta.drift_threshold: 5m`, `on_stall: [notify_customer, webhook.ops_reassign]`, `offer_cancel_after: 10m`, `copy.reasons.*` | Rider GPS every 5-10 s (accuracy, speed, mock flag); merchant/store and customer geofences; food-ready/packed events; routing or traffic ETA (host model or Google Routes `TWO_WHEELER` fallback); rain flag | n/a / **M** (first-party GPS stream) / **M-L** (marketplace, and merchant delay must be separated) |
| 3. Batched or multiple orders; split shipments | **Multi-drop and Split Explainer**: "1 other drop first, ~4 min" before the customer notices; automatic priority-fee refund when another drop went first; item-to-shipment map ("2 of 3 delivered"); split and partial-fulfilment notices with the refund reference; multi-order disambiguation in chat | `batching.disclose: exact\|generic\|hidden`, `batching.show_stop_count_within: 3`, `priority.verify_and_refund: true`, `split.show_item_map: true`, `split.notify_on: [dispatch_date_changed, shipment_split]`, `partial_fulfilment.notify_before_delivery: true`, `assistant.disambiguate: recency_then_ask` | Dispatch batch ID, stop sequence, position and priority flag; rider GPS; order → shipment → line item with item and shipment IDs on each event (the Flipkart model); out-of-stock and refund events | **S** (shipments already in the OMS) / **M** (dispatch feed) / **M** |
| 4. Bad address (India) | **Address Confidence and Fix**: pre-dispatch score (text quality, pin-vs-text gap, geocode confidence, drop history); dual-pin confirmation with Google address descriptors; WhatsApp location request; tower/floor, voice note or DIGIPIN; "can't find it" guard before a failed attempt; learned drop points; evidence-based agent answers | `address.min_confidence: 0.7`, `address.min_text_length: 12`, `address.confirm_when: [low_conf, cod_over_inr:999, pin_text_gap_m>300]`, `address.geocoder: google\|mappls\|latlong\|host`, `address.show_descriptors: true`, `address.channels: [whatsapp_location_request, in_app]`, `address.accept: [pin, landmark, tower_floor, voice_note, digipin]`, `attempt.require_before_fail: [gps_within_m:200, call_logged]` | Typed address; geocoder output with confidence and error radius; dropped pin and its GPS accuracy; pin-vs-geocode distance; DIGIPIN; historical drop points; rider GPS at attempt; masked-call logs; NDR reasons | **M** (geocoder plus WhatsApp; the biggest RTO lever for COD) / **S** (small radius, known customers) / **M** |
| 5. Proactive communication | **Promise Keeper**: notify on *predicted* breach with a specific reason and one action; neutral tone for small delays, apology plus a credit only for big ones (JCR 2026); channel ladder with caps and quiet hours; fee reasons shown; one reason taxonomy; built-in A/B on contacts, cancellations and reorders | `notify.on: [breach_prob>0.6, eta_drift>5m, stall, ndr, split_shipped]`, `notify.tone: {neutral_below: 15m, apologize_when: [delay>15m, customer_contacted]}`, `notify.ladder: [push, whatsapp_utility, sms]`, `notify.max_per_order: 3`, `quiet_hours`, `notify.stop_if: [tracker_opened, replied]`, `notify.actions: [wait, cancel, reschedule]`, `experiments.notify_variants` | Breach probability or ETA drift; reason codes; weather or surge flags with zone and time; opt-ins; WhatsApp templates (DLT for SMS); sent/delivered/read/failed receipts; tracker-open, contact, cancel and reorder events | **S-M** (template approval is the long pole) / **S** / **S** |
| 6. Conversational WISMO | **Grounded answer contract**: an intent-sliced `get_order_truth`; code-enforced answer contract (no invented dates); staleness guard; reason-coded escalations and remedies; channels in-app, WhatsApp, email, voice and **MCP**; KPI dashboard led by WISMO rate and repeat contacts | `assistant.max_fact_age: {food: 90s, parcel: 12h}`, `assistant.answer_contract: strict`, `assistant.escalation_codes: [...]`, `assistant.channels: [in_app, whatsapp, email, voice, mcp]`, `handoff.always_available: true`, plus the `policies` and `escalation` blocks in `sdk-design.md` B6 | Everything above via `get_order_truth`; session identity (login, phone, email); policy table; action endpoints (cancel, reattempt, refund); customer trust score | **S** (widget plus WhatsApp number) / **S** / **M** (sits beside the host's existing bot, or replaces it for the WISMO intent only) |

**Build order for the POC** (my recommendation) **[inferred]**:
1. **6 plus 1 first.** A grounded agent over an honest tracker is the core promise.
2. **Then 2**, which gives the Swish and Zomato demo drama.
3. **Then 5.**
4. **4 and 3 last**, because they need host-specific feeds (a geocoder, a dispatch stop sequence). For Smytten, 4 is the biggest RTO lever, so pitch it there first.
