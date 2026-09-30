# Best-in-class WISMO / order-tracking practices, and how to fix Smytten + quick-commerce failures

Researched 2026-09-30. Sources are inline. Markers used below:
- **[vendor claim]**: a number published by the vendor or the brand itself, with no independent audit.
- **[3rd-party]**: from a review, comparison or blog site, which may have its own agenda (competitor blogs, SEO sites).
- **[unverified]**: could not confirm against a primary source.

Context from the complaint dataset: about 37.6% "marked delivered but not received", about 39% support failures (no reply, tickets closed, bot loops), late or stuck orders, and refunds stuck at "initiated".

---

## 0. Why this matters (India context, 2025-26)

- **Complaint volume.** NCH (National Consumer Helpline) logged **47,743 e-commerce refund grievances between Apr 25, 2025 and Jan 31, 2026**. That is the highest of 31 sectors, and led to Rs 36.79 cr in refunds.
  - The Department of Consumer Affairs said: *"In the name of AI adoption, companies have created multiple layers of bots that are acting as barriers to effective grievance redressal."* It plans deadlines, with penalties for missing them.
  - Source: https://www.tradingview.com/news/moodys:8345905a4b917:0-govt-may-step-in-to-help-consumers-crack-ai-chatbot-maze/ (the page shows the date as Aug 17, 2025, but quotes data up to Jan 2026, so the date is inconsistent).
- **Complaints by platform, 2025.** Flipkart about 1.33 lakh, Amazon 91,248, Meesho 29,284 (https://the420.in/flipkart-ecommerce-consumer-complaints-national-helpline-refunds/) **[3rd-party]**.
  - NCH convergence partners grew from 263 (2017) to 1,142 (Sept 2025). Companies are expected to respond within 30 days (https://www.pib.gov.in/PressReleasePage.aspx?PRID=2179780).
- **Regulation.** The Consumer Protection (E-Commerce) Rules 2020 require:
  - a named grievance officer;
  - **acknowledgement within 48 h and resolution within 1 month**;
  - refunds "within a reasonable period as per RBI guidelines".

  Sources: https://www.lexology.com/library/detail.aspx?g=88018b31-3e34-4650-803b-cbfdef2adede and https://www.icsi.edu/media/webmodules/Consumer_Protection_E-Commerce_Rules_2020.pdf
- **2026 amendment.** The E-Commerce (Amendment) Rules 2026 were notified Sept 9, 2026. They:
  - make **NCH convergence mandatory for every e-commerce entity**;
  - require a customer-care email, landline and mobile number to be shown;
  - keep the 48 h / 1 month timelines.

  Reported in force from **Jan 1, 2027** (https://www.indialaw.in/blog/consumer/consumer-protection-e-commerce-amendment-rules-2026/, https://www.mondaq.com/india/corporate-and-company-law/1846008/overview-of-the-consumer-protection-e-commerce-amendment-rules-2026). The article I read has no chatbot or human-escalation clause.
- **RBI failed-transaction rules** (circular of Sept 19, 2019): UPI P2P auto-reversal by T+1; P2M (person-to-merchant) by **T+5**; **Rs 100/day compensation**, paid suo motu, for delays beyond that (https://www.rbi.org.in/scripts/NotificationUser.aspx?Id=11693, summarised at https://zeenews.india.com/personal-finance/failed-upi-transactions-banks-to-pay-rs-100-per-day-penalty-for-delay-beyond-2-days-2352699.html). This is the benchmark a "refund initiated" status should be held against.
- **Smytten itself.** Trustpilot score is 2.5/5 from 27 reviews, 78% one-star, and **no replies to negative reviews**. Recent complaints:
  - Sept 10, 2026: a Rakhi hamper was not delivered, the customer could not cancel, and asked for a refund "since 10 days on chats only … no official has called me".
  - Aug 22, 2026: paid, 15 days, not received.

  Source: https://www.trustpilot.com/review/smytten.com

  Voxya complaints cover "shows delivered but not received", "refund pending due to incorrect order status", and a chatbot "repeatedly asking to wait" (https://voxya.com/consumer-complaints/in-smytten-app-they-show-order-is-delivered-but-i-have-not-received-it-yet-not-my-family-members-or-/255570, https://voxya.com/consumer-complaints/refund-pending-due-to-incorrect-order-status-/256565).
- **WISMO is the biggest ticket category.** It is up to about 30% of inbound volume per Gorgias's 12k-store data, and 50%+ at peak (https://www.gorgias.com/blog/customer-service-statistics; https://alhena.ai/blog/wismo-ai-order-tracking/) **[vendor claim / 3rd-party]**.

---

## 1. Consumer apps: what they actually do

### Amazon (US and India)
- **Delivery OTP (India).** A 6-digit code is sent when the order is Out for Delivery. It must be shared only in person at handover (https://www.amazon.in/gp/help/customer/display.html?nodeId=GXHYX22CS752PLE3; I could only see the search snippet, because the page returned 503).
  - Known abuse: agents ask for the OTP by phone before arriving, then the case is treated as closed (https://digilawyer.ai/blogs/how-to-complain-to-amazon) **[3rd-party]**.
- **"Delivered but not received" (India): self-serve "Raise a query".** The delivery station is notified and attempts a **"rescue"** (recovery).
  - The customer must report **within 7 days**.
  - **Pay-on-Delivery orders are not eligible for rescue.**

  Source: https://www.amazon.in/gp/help/customer/display.html?nodeId=GCU8BWGTQNJKQEBS (search snippet; the page returned 503).
- **US flow.** Orders > Problem with order > "Package didn't arrive" > refund or replacement, backed by the A-to-z Guarantee.
  - Amazon asks customers to wait **48 h**, because packages are sometimes scanned as delivered early.
  - The claim window runs up to 90 days.

  Source: https://parcelpath.com/ecommerce/amazon/amazon-delivery/amazon-product-never-arrived/ **[3rd-party]**
- **Photo on Delivery (POD).** A photo of where the package was left is attached to the delivery notice.
  - Coverage is reported as about 70-80% of packages and 89% in metros (https://parcelpath.com/does-amazon-always-take-pictures-of-delivery/) **[3rd-party, unverified]**.
  - Original programme: https://www.marketingdive.com/news/amazon-adds-app-based-photo-confirmation-for-deliveries/518388/
- **Map Tracking.** A live map with an ETA once the driver is **10 stops away**, plus a push alert. It covers Amazon Logistics deliveries only (https://www.amazon.com/gp/help/customer/display.html?nodeId=GU9B4LE26DKWVQTN; https://www.supplychaindive.com/news/amazon-puts-live-mobile-tracking-feature-on-the-map/524395/). India availability is unconfirmed.
- **Delivery instructions up front** (access code, hours, location) to cut missed deliveries (https://shipping.amazon.com/insights-and-news/amazon-shipping-product-update-july-2025).
- **AI.** Rufus handles tracking, returns, refund status, cancellations and replacements for damaged items. It had 300M+ users in 2025 and was folded into "Alexa for Shopping" in May 2026 (https://www.customerexperiencedive.com/news/amazon-ai-rufus-convenience-fast-delivery/739602/, https://www.axios.com/2026/05/13/amazon-alexa-ai-shopping-assistant).
- **Amazon Now (10-minute delivery)** runs across about 100 Indian cities from 750+ micro-fulfilment centres, at $1B+ annualised GMS (https://www.aboutamazon.in/news/retail/amazon-now-10-minute-delivery-launch).

### Flipkart
- **Open Box Delivery.** The agent opens the outer and inner packaging in front of the customer, who checks for damage or a wrong item, **then** shares the OTP. It is free on eligible high-value categories (https://stories.flipkart.com/open-box-delivery-flipkart-customer-trust).
  - Failure mode: agents force the OTP before opening (https://voxya.com/consumer-complaints/open-box-delivery-violation-forced-otp-for-order-/256122).
- **Support.** 24/7 in-app chat with the "Flippi" bot, then escalation to a human by chat, a scheduled callback or email (https://www.19pine.ai/customer-service/retail-and-ecommerce/how-to-contact-flipkart-customer-service) **[3rd-party]**.
  - Flipkart launched the "Shop Like a Pro (SLAP)" AI assistant in Jan 2026 (https://www.medianama.com/2026/01/223-flipkart-conversational-ai-commerce-slap/).
  - Paper on the Flippi GenAI architecture: https://arxiv.org/html/2507.05788v2
- **Caveat.** Flipkart is the **#1 e-commerce company by NCH complaints in 2025**, so praised features do not equal praised outcomes.

### Myntra / Nykaa
- Not widely praised for post-purchase. Trustpilot and PissedConsumer reviews cite "no OTP, marked delivered", tracking that never updates, and refunds late against the stated 7-10 working days (https://www.trustpilot.com/review/www.myntra.com?page=2, https://www.reviews.io/company-reviews/store/myntra/insights/refund).
- Nykaa offers chat 8am-10pm, a toll-free number, WhatsApp, SMS and email (https://www.elliott.org/company-contacts/nykaa-customer-service-contacts/).
- I found no published WISMO metrics for either. **Treat them as peers, not benchmarks.**

### Meesho
- **GenAI multilingual voice bot** (Nov 2024), Hindi and English with more languages planned. It handles about **60,000 calls/day with a 95% resolution rate** **[vendor claim]**, and reports:
  - **AHT -50%**;
  - **CSAT +10%**;
  - **cost per call -75%**.

  Sources: https://yourstory.com/2024/11/meesho-launches-gen-ai-powered-multilingual-voice-bot-customer-service, https://www.business-standard.com/companies/news/meesho-unveils-multilingual-gen-ai-powered-voice-bot-for-human-like-support-124112601001_1.html. Built with ElevenLabs voice (https://elevenlabs.io/blog/meesho).

### Zomato / Blinkit (Eternal)
- **Nugget** (Zomato's in-house AI support platform, now sold as a product):
  - automation went from 60% to **80%+**, with an 85% average resolution rate reported for Jan 2026;
  - **about 11M tickets/month**;
  - agents went from **4,000+ to about 1,000**;
  - support cost went from **$20M to $9M**;
  - AHT from 13 to 9 min;
  - CSAT +25%.

  It automates **up to 70% of refund cases**, cancellations and escalations. It also uses **image analysis to detect damaged or spilled items, wrong items, stock photos and brand mismatches**, and audits 100% of AI chats. Source: https://www.nugget.com/resources/zomato-case-study/ **[vendor claim; updated Jul 27, 2026]**, also https://www.mongodb.com/company/blog/innovation/zomato-ai-solution-nugget-reduces-support-costs
- **Earlier LLM bot** (Together AI / Llama): **2x CSAT, responses under 10 s (-75%)**, 1,000+ messages/min, 80k customers on Mother's Day. It handles order status, ETA, changes to delivery instructions and cancellations (https://www.together.ai/customers/zomato) **[vendor claim]**.
- **Guaranteed-time compensation, withdrawn.** The Zomato Gold "On-Time Guarantee" gave a coupon (about Rs 100, reportedly scaled to how late the order was). It was **dropped for new or renewed Gold memberships from Nov 25, 2023** because it was too costly (https://inc42.com/buzz/no-more-on-time-guarantee-benefits-for-new-zomato-gold-members/).
- **No official food-delivery OTP found.** Users are publicly asking for one after fake "delivered" statuses (https://x.com/Rushu_Tushu/status/2015627504573469055). Zomato's CEO has acknowledged delivery-partner fraud, including the COD loophole (https://www.boomlive.in/boom-reports/zomato-food-delivery-cod-scam-ceo-deepinder-goyal-20831).
- **Blinkit.** Live map with picker status, dispatch and rider GPS, and an ETA that updates live (https://zlash.ai/track/blinkit) **[3rd-party]**.
  - Support is **in-app chat only, with no phone line**. Complaints describe a chatbot giving "vague and inconsistent replies" (https://kanoon360.com/blog/blinkit-customer-care-number-for-complaint/, https://www.consumercomplaints.in/bycompany/blinkit-a616132.html).

### Swiggy / Instamart
- **Enterprise AI agent on Databricks** (Oct 21, 2025). Multi-agent, one agent per ticket type ("disposition"), using RAG and **"structured action-trigger integration" with the CRM** to run refunds and cancellations.
  - Latency target under 500 ms at p99.
  - KPIs are scored hourly: Conversation Quality, Completeness, Factfulness and Resolution Efficiency.
  - Claims "100% of queries fully automated" **[vendor claim; this almost certainly refers to the scoped rollout, not the whole company]**.
  - Source: https://www.databricks.com/blog/redefining-customer-support-swiggys-enterprise-scale-ai-agent-built-databricks
- **Instant, photo-based refunds for missing or damaged items.** These were **exploited with AI-edited images** in Nov 2025: a user prompted "apply more cracks" on a photo of eggs and got a refund.
  - Swiggy responded with ML behavioural models that flag suspicious refund patterns in real time, plus manual checks (https://www.businesstoday.in/amp/latest/trends/story/apply-more-cracks-swiggy-instamart-customer-allegedly-uses-ai-to-secure-refund-for-broken-eggs-503803-2025-11-26, https://www.business-standard.com/industry/news/food-companies-take-note-of-rising-ai-generated-images-for-refund-125120101409_1.html).
- **Delivery OTP scams.** Fraudsters posing as restaurant staff or riders get the customer's OTP so the order is marked complete. Swiggy says it never asks for an OTP by phone (https://thelogicalindian.com/i-feel-foolish-hyderabad-man-loses-swiggy-order-after-sharing-otp-with-fake-pista-house-caller/).
  - **Lesson: an OTP is only as good as the rule that it is spoken in person, at the door, and checked against the rider's GPS.**
- A consumer commission held Swiggy and Instamart liable for short delivery and ordered Rs 2,000 compensation (https://www.bwlegalworld.com/article/chandigarh-commission-holds-swiggy-and-instamart-liable-for-short-delivery-and-service-deficiency-580694).

### Zepto
- **Self-serve in-app help:** pick the order, then "Item missing", "Damaged" or "Delayed". Missing-item reports are accepted **within 24 h** and take 1-2 days to review.
- Zepto **defaults refunds to Zepto Cash (store credit)**. Customers must ask explicitly for a refund to the original payment method.
- Complaints about bots that will not hand over to a human (https://www.zeptocorner.com/2025/06/report-missing-items-zepto-order.html, https://digilawyer.ai/blogs/file-complaint-against-zepto) **[3rd-party]**.
- For premium electronics (iPhone), quick-commerce players reportedly use **OTP handoff, tamper-evident packaging and insured delivery** (https://retailintel.in/signal/quick-commerce-platforms-add-iphone-18-pro-models-to-10-minu-cfb0420c) **[unverified]**.

### Domino's (India)
- The **Pizza Tracker** (order to prep to bake to QC to out-for-delivery) is the original "show the work" tracker (https://dominos.gcs-web.com/news-releases/news-release-details/dominos-launches-revolutionary-customer-tool-pizza-trackertm).
- **"30 minutes or free" is still live in India.** Details:
  - maximum liability **Rs 300**;
  - measured at the "first barrier point" (the gate or first checkpoint), not the door;
  - excludes orders of 4+ pizzas and festival blackout days;
  - riders are not penalised for lateness.

  Source: https://www.dominos.co.in/hot-pizza-30-minutes-delivery-guarantee-at-dominos-get-pizza-hot
- The template: **a pre-committed, capped, automatic remedy, stated before purchase.**

### Uber Eats / DoorDash
- **Uber Eats PIN.** A 4-digit PIN is required for some hand-to-customer orders, **especially for accounts with a history of missing-order reports**. That makes it risk-based, not universal (https://financialpanther.com/uber-eats-pin/; developer docs: https://developer.uber.com/docs/deliveries/guides/pincode).
- **Uber Eats late credit.** The automatic "Latest arrival by" credit (20% as Uber Cash) for Uber One members was **discontinued May 30, 2025** (https://www.19pine.ai/late-delivery-compensation/meal-kit-and-food-delivery/uber-eats) **[3rd-party]**. The 2017 guarantee gave a $4.99 promo (https://www.uber.com/us/en/newsroom/guaranteed-delivery/).
- **Missing or incorrect items.** Self-serve Get Help flow: select the items, get an instant refund or credit, and the merchant is charged (https://help.uber.com/en/merchants-and-restaurants/article/managing-refunds-for-missing-or-incorrect-orders-?nodeId=9aa57e9b-8bbf-4aa7-91d6-96ca77682dd2). Agents see a single view of customer data via Salesforce (https://www.salesforce.com/resources/customer-stories/automating-workflows-uber-eats/).
- **DoorDash.** A drop-off photo is required for contactless delivery, and some customers must give a 4-digit code.
  - After a Dec 2025 case where a driver submitted an **AI-generated delivery photo**, DoorDash describes:
    - live-camera-only capture with signed metadata;
    - an ML forgery score on each photo;
    - GPS and jailbreak anomaly detection;
    - periodic driver selfie checks;
    - flags on customers with repeat claims.

    Sources: https://www.aicerts.ai/news/doordashs-ai-image-delivery-fraud-challenge-and-ethics/ **[3rd-party]**, https://help.doordash.com/en-us/dashers/article/confirming-delivery-drop-off-photos

### Apple Store
- Order status on the "For You" tab of the Apple Store app. **SMS when shipped or ready for pickup**, and a dispatch email with the carrier and estimated date.
- **Apple Wallet Order Tracking** (merchant API) pushes status changes and delivery links into Wallet, with notifications (https://support.apple.com/en-us/105065, https://support.apple.com/guide/business/order-tracking-faq-abcbb713dd73/web).
- The takeaway is **one canonical status, pushed to where the user already is**.

---

## 2. Post-purchase and AI-support vendors

| Vendor | What it does | How the AI acts | Integration | Pricing (public) | Published results |
|---|---|---|---|---|---|
| **Narvar** (US, enterprise) | Branded tracking; proactive notifications; returns. **IRIS** AI engine (Jan 9, 2025) runs on 42B+ interactions/yr. **Narvar Assist** handles delivered-not-received (DNR) claims. | Scores each claimant as **high-trust or high-risk** using account age and history, carrier scans, proof of delivery, device and IP, and payment signals. **High-trust customers get an instant refund or reship.** High-risk claimants must upload photos, or are denied. Auto-adjudicates within the retailer's policy. | Salesforce, Zendesk, Gladly, Kustomer; APIs. | Enterprise, not public. | **WISMO -60% with proactive updates.** Claim payouts -25%, claim-related conversations -80%, +30% of ineligible claims deflected (https://corp.narvar.com/assist, https://corp.narvar.com/press/narvar-introduces-iris, https://corp.narvar.com/solutions/customer-care) **[vendor claim]**. |
| **AfterShip** | Multi-carrier tracking (1,100+ carriers); branded tracking page; email and SMS alerts; **AI EDD** (estimated delivery date) trained on 4.4B shipments, covering at least 80% of deliveries vs under 40% for carrier EDDs; AI status normalisation. | Mostly proactive notifications and EDD; the AI works on the data layer. | Shopify app, API, webhooks. | **Free tier; Essentials $29/mo** (6k shipments/yr, $0.08 per extra); Premium $59/mo; Enterprise custom (https://www.aftership.com/pricing/tracking). | **WISMO -65%** **[vendor claim]** (https://www.aftership.com/tracking). |
| **parcelLab** (EU) | Tracking, notifications, returns, delivery-promise widget. **AI Agents launched at Shoptalk, Mar 24, 2025.** | The "WISMO/R agent" **intercepts customer emails and answers WISMO and WISMR (where is my refund) questions on its own**, and handles order exceptions. | Plugs into retailer systems; no specifics published. | Enterprise. | WISMO **-20%**, email revenue +29%, checkout conversion +5% **[vendor claim]** (https://parcellab.com/press/parcellab-debuts-industry-defining-ai-agents-at-shoptalk-spring-2025/, https://parcellab.com/ai-agents/). |
| **WISMOlabs** (US) | 750+ carriers; branded tracking; email, SMS and **webhooks**; **delay prediction with proactive alerts**. | Rules plus predictive delay alerts. | Shopify, BigCommerce, Gorgias, Klaviyo, Yotpo. | Growth **$250/mo** (2,500 shipments); Pro $730/mo (10k) **[3rd-party]** (https://wismolabs.com/pricing/, https://www.clickpost.ai/en-us/alternatives/wismolabs). | n/a |
| **Route** (US) | Package protection sold at checkout (typically **about 2-2.5% of cart value**, paid by the customer) plus tracking. | **The customer files a claim in seconds, and the AI verifies it and triggers a refund or reship with no ticket.** AI fraud detection. | Shopify app. | Customer-paid premium. | **1.6M claims resolved, 97% CSAT, $20B GMV protected, $10M fraud prevented** **[vendor claim]** (https://www.route.com/protect). |
| **Malomo** | Branded tracking for Shopify; notifications; marketing. **Acquired by Redo** (https://gomalomo.com/). | Rules. | Shopify, Klaviyo. | n/a | WISMO "up to -50%" **[vendor claim]**. |
| **ClickPost** (India) | 600+ carriers, 50M+ shipments/mo; EDD by pincode, carrier and SKU; **AI NDR agent** (NDR = non-delivery report, a failed-delivery record); **"Parth" multilingual AI voice agent** that calls customers about failed deliveries and confirms COD orders. | Buckets NDR reasons with AI; runs WhatsApp, SMS and voice follow-ups on a schedule (for example T+60 and T+120 min); **passes the customer's feedback to the carrier via API** (for example, "no one came"). | Shopify, Magento, WooCommerce, OMS and WMS; carrier APIs. | Enterprise. | **RTO (return-to-origin) -40%, support load -75%, 90% of failed-delivery resolutions automated, WISMO -25%** **[vendor claim]** (https://www.clickpost.ai/ndr-management, https://www.clickpost.ai/). |
| **Shiprocket** (India) | Aggregator plus **Engage 360** (WhatsApp, SMS and email). **WhatsApp NDR prompts** capture the failure reason and offer a reattempt. **Automated IVR calls and SMS check whether a delivery attempt was real.** Oct 2025: new NDR panel with automatic reattempts. **Aug 2026: automatic WhatsApp delay notices when the ETA slips.** | Rules plus AI voice ("Fastrr Voice" for COD confirmation). | Shopify, Woo, API, WhatsApp. | Per-shipment plus add-ons. | NDR: **+30% responses, reattempts triggered in 75% of cases** **[vendor claim]** (https://www.shiprocket.in/blog/product-highlights-from-august-2026/, https://www.shiprocket.in/blog/product-highlights-from-october-2025/, https://www.shiprocket.in/blog/know-how-you-can-prevent-fake-delivery-attempts/). |
| **Gorgias** (helpdesk for Shopify) | AI Agent with **Actions**: track, cancel unshipped orders, edit the address, returns and **refunds**, pause subscriptions (Recharge, Loop). | Reads **live Shopify data** and acts within the rules the merchant configures. | Shopify-native; about 100 integrations. | **Pay per resolution since May 28, 2025: $0.90 per resolution (annual), $1.00 (monthly)**, plus the helpdesk ticket fee **[3rd-party]** (https://www.ringly.io/blog/gorgias-ai-agent-pricing-per-resolution). | Trove Brands: **45% automation**, 31 s to resolve, **first response at BFCM went from 11.5 h to 30 s** (https://www.gorgias.com/customers-legacy/trove-brands) **[vendor claim]**. |
| **Fin** (formerly Intercom; renamed May 2026) | Fin AI Agent; "Procedures" (multi-step, action-taking workflows); runs on any helpdesk. **Salesforce signed an agreement to acquire it for about $3.6B on Jun 15, 2026** (https://www.salesforce.com/news/press-releases/2026/06/15/salesforce-signs-definitive-agreement-to-acquire-fin/). Whether the deal has closed is unclear **[unverified]**. | Procedures call APIs (refunds, order lookup); hands off to a human. | Widget, SDK, API, Zendesk and Salesforce. | **$0.99 per outcome** (resolution, procedure handoff, and similar); guarantees a refund of up to $1M **[3rd-party]** (https://www.getmacha.com/blog/intercom-fin-pricing). | Claims a **76% average resolution rate**. Third-party reading of case studies puts it at **42-50%** **[3rd-party]**. |
| **Sierra** | Enterprise agent platform, chat and voice. | Tracks orders, handles warranty claims, **issues refunds instantly**, and turns returns into exchanges. | Custom; deep API integration. | **Outcome-based**, not public. Estimated at $150k+/yr **[3rd-party]**. | Casper: resolved more than half of inquiries from day one, **70% on product questions**, CSAT up nearly a full point (https://sierra.ai/industries/retail) **[vendor claim]**. |
| **Decagon** | Agent Operating Procedures (AOPs): workflows written in plain language, with integrations and guardrails version-controlled in Git. | Executes an AOP against backend tools. | API, widget, voice. | Enterprise. Valued at $4.5B in Jan 2026 (https://www.businesswire.com/news/home/20260128580542/en/). | **About 80% average deflection**, support cost -65% (https://decagon.ai/product/aop, https://stripe.com/customers/decagon) **[vendor claim]**. |
| **Zendesk AI agents** | AI agents inside Zendesk Suite. | Resolutions verified automatically; actions via integrations. | Zendesk-native. | **$1.50 per automated resolution (committed), $2.00 pay-as-you-go.** Suite plans include 5, 10 or 15 per agent per month **[3rd-party]** (https://www.eesel.ai/blog/zendesk-ai-pricing). | n/a |
| **Yellow.ai** (India) | Agentic AI platform; 135+ languages. | Checks the order in the CRM, **checks refund eligibility**, updates the ticket and notifies the customer. | CRM, helpdesk and ERP connectors; WhatsApp. | Enterprise. | Support volume "up to -40%" **[vendor claim]** (https://yellow.ai/blog/digital-commerce/). |
| **Haptik** (Jio, India) | WhatsApp and voice AI agents; **22 Indian languages**. | Order lookup and status via CRM or ERP APIs; creates tickets; sends payment links. | WhatsApp Business API; CRM and OMS APIs. | **SMB tier from Rs 10,000** (Sept 2025) (https://yourstory.com/2025/09/jios-haptik-rs-10000-whatsapp-ai-agents-small-businesses). | **Up to 80% of repetitive queries resolved automatically**; a logistics client resolves 80% of status queries **[vendor claim]**. |

**Patterns across vendors:**
1. The **biggest drop in WISMO comes from proactive notifications** (claimed at 20-65%), not from chat.
2. **Outcome-based pricing ($0.90-$2 per resolution) is now standard.**
3. **AI that takes actions** (refund, reship, cancel, change address) inside policy limits is what separates these products from FAQ bots.
4. **Trust-scored claims**, where good customers get an instant refund and risky ones need proof (Narvar, Route), is the proven answer to "delivered but not received".
5. India-specific vendors (ClickPost, Shiprocket) centre on **NDR and verifying fake delivery attempts** over WhatsApp and voice, in Indian languages.

---

## 3. Mapping: failure mode → proven fix → who does it

| Smytten / quick-commerce failure | Proven practice that fixes it | Who does it (evidence) |
|---|---|---|
| **Marked delivered, not received (37.6%)**, the root cause at handover | **Delivery OTP spoken at the door**, with rules: never ask by phone; **OTP accepted only when the rider's GPS is within X metres of the drop point** (the geofence part is my recommendation) | Amazon India 6-digit PIN; Flipkart Open Box + OTP; Uber Eats PIN; DoorDash code. Scam cases at Swiggy and Amazon show why the in-person rule matters. |
| Delivered, not received: no evidence | **Photo on delivery**, taken live with signed metadata and an ML forgery check, and shown in the delivery notice | Amazon POD; DoorDash drop-off photo with forgery scoring. |
| Delivered, not received: customer has no recourse | **Self-serve "Package didn't arrive" flow**, with a clear window (7 days in India, a 48 h wait in the US) and a promised remedy (refund or replacement) | Amazon (India "rescue" by the delivery station; US A-to-z); Uber Eats Get Help. |
| Delivered, not received: fraud risk blocks instant refunds | **Trust-scored adjudication**: instant refund or reship for high-trust customers; photo, inspection or denial for high-risk ones | Narvar Assist (IRIS); Route; Uber Eats uses a risk-based PIN; Swiggy's ML refund-fraud models. |
| Fake "attempted" or fake "delivered" status from the courier | **Verify with the customer on the spot** (WhatsApp or IVR: "Did the rider come?"); detect patterns (the same rider logging many "unavailable" results with no call log, late-night attempts, GPS mismatch); **escalate to the carrier via API with evidence** | Shiprocket IVR/SMS checks and WhatsApp NDR; ClickPost Parth voice agent and NDR API feedback. |
| **Support: no reply or ticket closed (39%)** | **An AI agent that can act** (look up the order, refund, reship, cancel) within policy, plus a **guaranteed human handoff** with full context, plus SLA timers tied to the 48 h / 1 month rule | Zomato Nugget (80%+ automated, 70% of refunds automated); Swiggy's Databricks agent; Gorgias Actions; Fin Procedures; Sierra; Decagon. |
| Bots looping, "please wait" | **Detect loops and escalate automatically** (for example, the same intent 2+ times, negative sentiment, or a legal or complaint keyword leads to a human); report bot quality hourly | Swiggy scores Completeness and Resolution Efficiency hourly; Nugget audits 100% of AI chats; Flipkart offers escalation by chat, callback or email. |
| Tickets closed without resolution | **Closing needs proof of an outcome** (a refund reference or new AWB), confirmed by the customer, or it reopens automatically; pricing tied to outcomes lines up the incentives | Gorgias, Fin and Zendesk charge only for verified resolutions. |
| Late or stuck orders | **Predicted EDD plus a proactive delay notice before the promised time**, with a new ETA and options (wait, cancel, refund) | AfterShip AI EDD; WISMOlabs delay prediction; Shiprocket WhatsApp delay alerts (Aug 2026); ClickPost EDD; Narvar (claims up to 60% fewer WISMO contacts). |
| Late (quick-commerce and food) | **Live rider map plus a granular stage tracker** (packing, picked up, arriving) | Blinkit, Swiggy and Zepto live maps; Domino's Pizza Tracker; Amazon "10 stops away" map. |
| Late: no remedy | **A pre-committed, capped, automatic compensation** ("30 min or free", up to Rs 300); credited automatically, not by claim | Domino's India (still live). Zomato Gold (withdrawn 2023, cost) and Uber One (withdrawn May 2025) show it must be priced and capped. |
| **Refund stuck at "initiated"** | **Refund tracker showing the gateway and bank reference (RRN/ARN)**, with each stage (initiated, processed by the gateway, credited by the bank) and an ETA held to the RBI benchmark (T+5 for P2M UPI); auto-escalate if late | RBI TAT circular; parcelLab's WISMR agent answers "where is my refund". Amazon offers a 2-3 h refund to gift-card balance, or 3-5 days to cards **[3rd-party]**. RRN/ARN display is common in Indian apps, but no single citation found **[unverified]**. |
| Refund forced to store credit | **Default to the original payment method**, or offer an instant wallet refund as an explicit choice | Zepto's default to credit is a complaint driver; Amazon lets the customer choose. |
| Customers go to Trustpilot, Voxya or NCH | **Grievance-officer SLA** (acknowledge within 48 h, resolve within 1 month); **NCH convergence (mandatory from Jan 2027)**; monitor public complaint sites and reply | Consumer Protection (E-Commerce) Rules 2020 and the 2026 amendment. Smytten currently does **not reply** on Trustpilot. |
| Missing or damaged item (quick-commerce) | **Instant photo-based refund**, with vision checks for damage and stock or edited images, plus behavioural fraud models | Zomato Nugget vision; Swiggy after the "apply more cracks" incident; Uber Eats charges the merchant. |
| No phone line or human | **A published human channel** (callback within X min) as a backstop | Flipkart scheduled callback; Nykaa toll-free line. Now required: 2026 amendment Rule 4 (customer-care landline and mobile numbers must be shown). |

---

## 4. What a best-in-class "AI WISMO" product must do

### Table stakes (everyone good does these; missing any one of them produces the complaint dataset)

1. **One trustworthy status timeline.** Merge carrier, OMS, payment-gateway and rider-GPS events. Normalise carrier statuses (AfterShip normalises with AI). Show the timeline in the app, on a branded page, on WhatsApp and in Wallet (Apple Wallet Orders).
2. **Proactive notifications at every milestone, and above all before a promise is missed** (delay notice with a new ETA). This is the largest single WISMO deflector, claimed at 20-65%.
3. **An AI agent that answers from live order data**, in the customer's language (Hindi, English and regional languages; Haptik covers 22, Meesho's voice bot started with Hindi and English), on chat, WhatsApp and voice.
4. **The agent can act within policy**: cancel, change address, reattempt, refund, reship. It does not only answer (Gorgias Actions, Fin Procedures, Nugget, Swiggy).
5. **Self-serve "didn't receive it", "missing item" and "damaged" flows**, with clear windows and a promised outcome.
6. **Proof of delivery**: door OTP (spoken in person), and/or a live photo.
7. **Refund tracker** with the stage, bank reference and RBI-benchmarked ETA; the default is the original payment method.
8. **Guaranteed human escalation** with full context; no bot loops; the 48 h acknowledgement and 1-month resolution SLA enforced by the system; a published phone or callback option.
9. **A ticket closes only with an outcome** (refund reference, new tracking number, or the customer's confirmation), and reopens automatically if the promised event does not happen.

### Differentiators (what makes it "best-rated", and what to pitch)

1. **Trust-scored instant resolution** (Narvar IRIS, Route). A per-customer and per-order risk score decides between an instant refund or reship and a request for evidence. Good customers get a remedy in seconds, and fraud is still held back.
2. **Cross-checking delivery evidence in the AI's answer.**
   - For a delivered-not-received (DNR) claim, the agent itself checks the OTP entry, the rider's GPS at the moment "delivered" was logged vs the address geofence, the photo, the call log, and the scan time.
   - Then it gives **a straight answer**: "Your OTP was not entered and the rider was 2.3 km away when this was marked delivered, so we've refunded you." Or: "OTP was entered at your door at 7:42 pm; here's the photo."

   This directly fixes "support never gives a straight answer".
3. **Automatic courier accountability.** Fake-attempt and fake-delivery pattern detection per rider and per courier. Evidence goes to the carrier through its API (like ClickPost and Shiprocket), and those costs are recovered from the carrier.
4. **Predictive EDD and pre-emptive remedies.** Predict a breach before it happens (AfterShip AI EDD, WISMOlabs). Credit a capped apology automatically (Domino's model) without the customer asking. Price it so it survives (Zomato Gold and Uber One show the cost risk).
5. **Detecting fraud in photos and images**: live-capture only, signed metadata, a forgery or AI-edit classifier (DoorDash, Nugget vision, Swiggy after the eggs incident).
6. **Quality control on the AI itself.** Audit 100% of AI conversations (Nugget); score factfulness and completeness hourly (Swiggy); detect loops; pay per verified outcome.
7. **Regulatory automation (India).** Grievance-officer SLA clocks; NCH convergence ingestion (mandatory from Jan 2027); RBI refund TAT alerts. It also watches Trustpilot, Voxya and NCH and closes the loop on each.
8. **Answering from "the system of record", not a script.** Every answer cites the event it rests on (timestamp, scan, reference number). Promises made by the agent become tracked commitments that trigger follow-up automatically.
9. **Adoption without rebuilding the app**: embeddable widget, SDK, WhatsApp number, Shopify app, webhooks; outcome-based pricing (the $0.90-$2 per resolution market norm).

### Weak spots (where even the leaders stumble; avoid them)
- Store-credit-only refunds (Zepto).
- Removing time guarantees without telling customers (Zomato Gold, Uber One).
- OTP social engineering, when the OTP is shared by phone (Swiggy, Amazon).
- Blind trust in photos (Swiggy eggs; the DoorDash AI photo).
- In-app-only support with no human route (Blinkit, Zepto). India's regulator is explicitly targeting this.
- Vendor claims of "100% automated" (Swiggy/Databricks) or "95% resolved" (Meesho) are measured on scoped traffic. Benchmark with care: third-party analysis of Fin puts real resolution at **about 42-50%**, against the 76% claimed.
