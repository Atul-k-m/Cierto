# Site structure research: how best-in-class B2B / developer products build their sites

*Research date: 2026-09-30. Purpose: structure the marketing + docs site for the AI WISMO product (working name "Intelligent WISMO"). Sources are live pages fetched on this date; URLs are cited inline. AfterShip returned HTTP 403 to the fetcher, so its notes come from search-result snippets only. Resend and Clerk now serve agent-oriented markdown to non-browser clients, so their homepage layouts were only partly visible (that fact is itself a finding, see Part C.6).*

---

## Part A. What the 13 sites do

### A.1 Homepage section order, site by site

| Site | Hero promise / CTA pair | Order of sections after the hero |
|---|---|---|
| **Stripe** ([stripe.com](https://stripe.com)) | "Financial infrastructure to grow your revenue" / Request an invite (+ Contact sales in nav) | Logo carousel → "Flexible solutions for every business model" (6 product families) → scale metrics (135+ currencies, US$1.9tn volume 2025, 99.999% uptime, 200M+ subscriptions) → Enterprise (Hertz, URBN, Instacart, Le Monde cards, each with 1–2 numbers) → Startups (Lovable, Linear, Decagon…) → Platforms (3 "Read the guide" cards + testimonials) → Developer infrastructure (500M+ API requests/day; 3 integration paths: no-code / pre-integrated / build your own) → "What's happening" news carousel → Stripe Press → Final CTA "Ready to get started?" (Contact sales / Pricing details / Integration options) |
| **Intercom** ([intercom.com](https://www.intercom.com/)) | "A complete system for human and AI customer service" / Start free trial + View demo ("14 day free trial. No credit card required.") | "Two products, one experience" → 30,000+ brands → Helpdesk features → Fin section with the number ("averaging 76% resolution across 12,000+ customers") → "Together" section → 3 customer quotes with numbers (Anthropic: "560,000 resolutions a month… 79% resolution rate") → integrations wall → **pricing on the homepage** ("$29 per seat/month + $0.99 per outcome") → final CTA. Every section repeats the same CTA pair. |
| **Fin** ([fin.ai](https://fin.ai/)) | "Perfect customer experiences made possible with Fin" / View demo + Start free trial | A numbered long-form list, "22 reasons to hire Fin" (01–22): performance, models, channels, control, **testing/simulation**, trust (SOC2, HIPAA, ISO 27001/27701/42001, AIUC-1, data residency), deployment, research, outcome pricing → closing CTA. Numbers are dense: 76% avg resolution, "1% monthly improvement", 2M weekly resolutions, 99.8% SLA, "226 product updates in 2025". |
| **Narvar** ([corp.narvar.com](https://corp.narvar.com/)) | "The future of agentic post-purchase starts here" / Book a demo | **Three problem sections first**, each a cost statistic block ("Returns: the $1 trillion retail threat"; "Predictability is profitability"; "Delivery anxiety is a profit killer", 120M+ packages stolen) → logos → platform (IRIS, "74B+ interactions, 2B packages") → module cards, each headline = a number ("Boost conversion up to 5%…", "Earn up to 15x ROI…") → AI engine → teams → testimonials with metrics → G2 badges → CTA "Power every moment after the buy". |
| **parcelLab** ([parcellab.com](https://parcellab.com/)) | "The post-purchase platform built for retailers." / Take a tour + Book a demo | Logos → journey tabs (Retain/Engage/Convert/Insights/AI Agents) → outcome grid ("Cut WISMO & WISMR: 20% fewer WISMO calls") → case carousel with one number each (Conrad "6,427 man hours saved", Wyze "20% decrease in WISMO") → role cards → news/report → G2 awards → **maturity self-assessment** CTA → footer CTA. |
| **parcelLab WISMO/R Agent** ([parcellab.com/wismo-agent](https://parcellab.com/wismo-agent/)) | "Customers don't want status updates. They want resolution." / Book a pilot | 4 commercial pillars → **pilot story with raw numbers** (2-week UK pilot: 411 emails, 81% resolution, 6:1 ROI) → how it works (delay intelligence, live tool calls, brand-tone guardrails) → **two deployment paths** (A: standalone; B: plug into existing Zendesk/Gorgias/Salesforce bot via endpoint or MCP server) → FAQ (escalation, traffic splits, data handling, pilot scope). The closest direct competitor positioning. |
| **AfterShip** ([aftership.com](https://www.aftership.com/), via search) | "Make every post-purchase moment count" | Outcome numbers up front ("95% delivery date accuracy, 50% revenue recovery through exchanges, 65% fewer WISMO tickets"), 2,000+ carriers, AI EDD across 101 carriers; free tools (e.g. [order lookup widget](https://www.aftership.com/tools/order-lookup-widget)) and a [WISMO glossary page](https://www.aftership.com/glossary/wismo) used as SEO entry points. |
| **Gorgias** ([gorgias.com](https://www.gorgias.com/)) | "Conversations that drive revenue, not just resolutions." / Discover pricing + Book a demo | "40% of Shopify brands" + logos (each with "Read case study") → feature cards → single ROI callout (bareMinerals 8.83× ROI + quote) → "AI Agent + Helpdesk, built as one" (contrast with "bolt-on" competitors) → AI Agent features ("Automate 60% of support", "Knows when to escalate") → inbox features → customer stories with 3 numbers → stats banner ($500M+, 17,000+ brands, 4.2× ROI) → **"50% in 50 days" timeline** (Today / Day 7 / Day 21 / Day 50) → "Backed by the best" (OpenAI partner, Shopify-invested). |
| **Sierra** ([sierra.ai](https://sierra.ai/)) | "Better outcomes. Built on Sierra." / Learn more | Logos (30+) → value props → exec quotes with headshots → product modules (Ghostwriter, Insights, Horizon) shown as **real UI: trace timelines, supervisor actions, intent classification** → trust wall (SOC 2, ISO 27001, ISO 42001, HIPAA, GDPR, EU AI Act, FedRAMP, PCI DSS) → CTA. Very little copy; the UI and the logos carry it. |
| **Decagon** ([decagon.ai](https://decagon.ai/)) | "The AI concierge for every customer" / Get a demo (hero also promotes its conference) | Logos → customer stories with metric per brand (Chime 70% resolution, Duolingo 80% deflection, ClassPass 95% cost reduction) → "Decagon difference" (Agent Operating Procedures written in natural language) → Build/Optimize/Scale with UI → omnichannel tabs (Voice/Chat/Email) → "Instant ROI" metric grid → resources. Hero shows agent actions as past-tense sentences ("I've applied your membership perks. Extending your rental…"). |
| **Razorpay** ([razorpay.com](https://razorpay.com/)) | "India's All-in-One Finance Platform" / Sign up, Pricing, **API Reference** in hero | Products grouped by job (Accept payments / Payouts / Banking / Payroll / Credit) → innovations → industry table (E-commerce, Education, BFSI, SaaS) → **For Developers with a cURL snippet** → no-code products → FAQs → free calculators. Trust: PCI DSS, "RBI-authorised Payment Aggregator". Names Indian customers (Swiggy, Zomato, Zepto). |
| **Linear** ([linear.app](https://linear.app/)) | "The product development system for teams and agents" | Every section is **real product UI with real-looking data** (issue IDs ENG-2298, a HomeScreen code diff, "8 sec", backlog counts 71/3/53) → planning timeline → AI agents doing tasks → review/ship → **dated changelog on the homepage** (Sep 24 → Aug 19, 2026) → 3 named-engineer quotes → "Built for the future. Available today." |
| **Vercel** ([vercel.com](https://vercel.com/)) | "Agentic Infrastructure" / Deploy now + Talk to sales | Each use-case section leads with **one customer + one number** ("Notion powers millions of agent conversations daily", "Zapier serves 100M+ monthly visits", "Mintlify powers docs for 20,000+ companies") → "Recently shipped" → CTA "Built by you, or your agents". |
| **Resend** ([resend.com](https://resend.com/)) | "Email for developers" | Code-first: a 6-line `resend.emails.send({from,to,subject,html})` snippet is the product demo; SDK tabs per language; testimonials from developers ([search result](https://www.producthunt.com/products/resend)). |
| **Clerk** ([clerk.com](https://clerk.com/)) | "More than authentication…" / Start building for free | Logos → **Components** (drop-in `<SignIn />`, `<UserButton />`, with a [theme editor](https://clerk.com/components/theme-editor)) → Authentication → Multi-tenancy → Billing → Platform → **Frameworks** (Next.js, React, Expo, Astro…) → integrations → 8 CEO/CTO testimonials → CTA with pricing teaser ("Free for your first 50,000 monthly retained users"). |

**Common skeleton (what 10+ of 13 share):**
1. Hero: one-line promise + a paired CTA (self-serve action + human action: *Start free / Book demo*, *Deploy / Talk to sales*).
2. Logos immediately under the hero (Stripe, parcelLab, Gorgias, Sierra, Decagon, Clerk, Narvar).
3. Problem or outcome framing, usually as numbers (Narvar, parcelLab, AfterShip, Gorgias).
4. Product surfaces, each shown as real UI (Linear, Sierra, Decagon) or cards linking to product pages.
5. Developer / integration section with a snippet or "3 ways to integrate" (Stripe, Razorpay, Clerk, Resend, parcelLab paths A/B).
6. Customer proof with one metric per customer (everyone).
7. Trust / compliance badges (Fin, Sierra, Razorpay; Decagon links a Trust Center).
8. Pricing teaser (Intercom, Clerk, Gorgias "Discover pricing" as the primary CTA).
9. Freshness signal: changelog, "recently shipped", news carousel (Linear, Vercel, Stripe, Fin's "226 updates").
10. Final CTA that repeats the hero pair.

### A.2 Information architecture (top nav)

| Site | Top nav | Notable sub-structure |
|---|---|---|
| Stripe | Products · Solutions · Developers · Resources · Pricing · Sign in · Contact sales | Footer: 25+ product links, 16+ solutions by industry/use case |
| Narvar | Products · Solutions · Customers · Resources · Company · Sign in · Request a demo | Solutions split **By value / By stage (pre-purchase, delivery, post-delivery) / By function / Platforms & integrations**; Customers split **by industry** (Apparel, Beauty & Skincare, Food & Beverage…); announcement bar ("Are you ready for Peak? Take the assessment") |
| parcelLab | Platform · AI Agents · Solutions · Customers · Resources · Company | Solutions **by role** and **by journey**; Resources grouped Learning (blog, guides, research, compare, glossary) / Events (live demo, webinars) / Help (developer resources, **status page**, carriers, partners) |
| Decagon | Product · Industries · Customers · Resources · Company · Sign in · Get a demo | Product grouped Channels / Build / Optimize / Scale; Resources: blog, "Decagon University", videos, glossary, guides; Company includes Trust Center |
| Sierra | Product · Industries · Customers · Company · Sign in · Learn more | Footer Product has a dedicated "Trust" page |
| Linear | Product · Resources · Customers · Pricing · Now · Contact · **Docs** · Open app · Log in · Sign up | "Now" = blog + changelog + launches in one feed |
| Razorpay | Payments · Banking · Payroll · Resources · **Developers** · Pricing | Hero puts "API Reference" next to "Sign up" |
| Intercom/Fin | Product · Solutions · Customers · Resources · Pricing · View demo · Start free trial | Demo is a top-level destination ([fin.ai/view-demos](https://fin.ai/view-demos)) |

**Pattern:** 5–6 items maximum. Products → Solutions (by industry *and* by role/stage) → Customers → Developers/Docs → Resources → Pricing, with a two-button right side (sign in / primary CTA). Dev-first companies (Linear, Razorpay, Stripe, Clerk) put **Docs** in the top bar, not buried in Resources.

### A.3 Page templates

#### Case studies

| Site | Structure |
|---|---|
| Stripe, [Instacart](https://stripe.com/customers/instacart) | Headline → 3 scale metrics (600K+ shoppers, 1,800 retailers, 98%+ households) → sidebar facts (**Products used**, location, stage) → 2 narrative sections named by *what they built* → quotes from a named lead → CTAs top/middle/bottom → 2 related stories |
| Decagon, [Rippling](https://decagon.ai/case-studies/rippling) | Breadcrumb → "How Rippling supports many user types with Decagon" → sidebar (32% deflection increase, 12+ product lines, 400,000 users, industry, **channels used**) → lead quote (VP Support) → **Overview / The Problem / The Solution / The Result** (problem lists 4 gaps; solution maps 1:1 to them) → 2 more quotes → Get a demo → 3 related |
| Fin, [Kalshi](https://fin.ai/customers/kalshi) | "How a Super Bowl support crisis led Kalshi to rebuild their stack on Fin" → 3 metric callouts (80k+ monthly resolutions, 80% automation, ~2M projected) → "At a glance" box → **story arc headings**: "A scaling problem with no easy answer" → "Touchdown in ten days" → "The turning point" → "A new AI-first support system" → "Room to breathe" → "What's next" → embedded charts → results summary (23 hours → minutes) → 3 related |
| Gorgias, [Pit Viper](https://www.gorgias.com/customers/pit-viper) | Headline = the result (4.9 CSAT, faster FRT) → 3 metrics (<3h FRT, 4.9/5, 41% one-touch) → facts (industry, **previous helpdesk**, size, products, **integrations: Shopify, ShipBob**) → Challenge / Solution / Results. Challenge is literally WISMO: agents tab-switching between Shopify and ShipBob |
| Linear, [OpenAI](https://linear.app/customers/openai) | "Why OpenAI chose Linear and scaled to 3,000 users" → facts (industry, location, founded, size, switched Nov 2023, previous state) → essay-style headings ("Complexity as the status quo", "Simplicity scales", "It's a feeling") → 4 pull quotes → previous/next story |
| Indexes | [Linear](https://linear.app/customers): industry filter tabs, card = logo + one-line + tags + "Read story". [Intercom](https://www.intercom.com/customers): Industry + Topic filters, card = logo + headline + 1–2 metrics. [Decagon](https://decagon.ai/case-studies): every card has a number |

**Template consensus:** headline states the outcome or the turning point, not "Company X uses Product Y"; 3 metric callouts above the fold; a facts sidebar that includes *products used, integrations, previous tool, time to launch*; challenge → solution → results where the solution answers each challenge point; named quotes; related stories filtered by industry.

#### Blogs

- [Stripe blog](https://stripe.com/blog): 4 categories (Product, Industry, Corporate, Engineering), bylines with job titles, dates, subscribe block.
- [Linear "Now"](https://linear.app/blog): one feed with filters: Changelog / Product launches / From the team / From the community / Press. Engineering posts titled as a specific problem ("AI coding has made CI a bottleneck, so we reworked ours to keep up", Sep 21 2026). Separate "Method" section for philosophy.
- parcelLab / Decagon / Narvar: blog sits under Resources beside guides, research reports, **glossary** and webinars; long-tail SEO pages such as [Decagon's WISMO glossary](https://decagon.ai/glossary/what-is-wismo-where-is-my-order), [AfterShip's](https://www.aftership.com/glossary/wismo), [Gorgias "reduce WISMO requests"](https://www.gorgias.com/blog/automate-wismo-requests).

#### Docs

- [Stripe docs](https://docs.stripe.com/): home = "Start here" (agent skills + CLI quickstart) → use-case entry points ("Accept payments online", "Sell subscriptions") → "Browse by product". Quickstarts ([Checkout quickstart](https://docs.stripe.com/checkout/quickstart)) are a **two-pane builder**: steps on the left, a full runnable file tree on the right, language/framework switchers (Node, Ruby, Python, PHP, Go, .NET, Java, Next.js), a **Download** button, **test data table** (4242… succeeds, 4000…3155 needs 3DS, 4000…9995 declines), "Congratulations!" then next steps. Every page says "Read this page in your terminal: `stripe docs`".
- [Resend Node quickstart](https://resend.com/docs/send-with-nodejs): Prerequisites (API key, verified domain) → 3 steps (Install with npm/yarn/pnpm/bun tabs → set `RESEND_API_KEY` → send) → 9 example repos. Test inbox address `delivered@resend.dev` makes the first call succeed without setup. Docs index at `/docs/llms.txt`.
- [Clerk Next.js quickstart](https://clerk.com/docs/quickstarts/nextjs): written for coding agents: one CLI command (`npx clerk init`) that works **without an account**, a checklist the agent confirms, 7 numbered steps, a "Critical rules" box, then "test sign-up" and next features.
- [Razorpay docs](https://razorpay.com/docs/): per product **Build → Go Live → Grow** cards; "Ask AI"; **copyable prompts to paste into Claude/Cursor** ("Integrate Razorpay using AI"); Developer Tools menu (API reference, webhooks, SDKs, CLI, **MCP**, error codes); Postman collection.

**Docs consensus (2026):** quickstart ≤ 5 minutes with one working call; a sandbox or test fixtures that return realistic states; guides by use case; API reference generated from OpenAPI; and an agent path (llms.txt, MCP server, CLI, copyable prompts).

#### Interactive demos

- **Stripe** [checkout.stripe.dev](https://checkout.stripe.dev/): a live, working component you can operate, with "Change demo" switches and "Start building" linking to docs.
- **Fin** [fin.ai/view-demos](https://fin.ai/view-demos): **not form-gated**; "Pick your industry, ask Fin anything" (Software, Financial Services, Ecommerce & Retail, Healthcare); an 8-chapter guided tour (analyse → train → guide → complex tasks → test → deploy → integrate); video as an alternative. The trial has a Messenger preview where you type your own questions.
- **parcelLab**: "Take a tour" is the primary hero CTA, with a "Live demo" listed under Resources.
- **Clerk**: live components + [theme editor](https://clerk.com/components/theme-editor), so the demo *is* the product.
- **Linear / Sierra / Decagon**: no playground, but product-UI screenshots carry realistic data and traces.

---

## Part B. What separates persuasive pages from generic "AI slop"

Specific techniques seen above, and the failure each one avoids:

1. **Real product UI with real-shaped data, not abstract gradients.** Linear shows issue IDs, a diff and "8 sec"; Sierra shows a trace with intent classification and supervisor steps. Slop shows a glowing orb and "AI-powered insights".
2. **One number per claim, attributed to a named customer.** "Wyze: 20% decrease in WISMO" (parcelLab), "Anthropic: 560,000 resolutions/month at 79%" (Intercom), "OrthoFeet: 56% automation in <2 months" (Gorgias). Slop says "reduce tickets dramatically".
3. **Numbers that include a denominator and a timeframe.** parcelLab's pilot: *411 emails, 2 weeks, 81%*. Fin: *76% average across 12,000+ customers*. The context makes them believable.
4. **The mechanism is named.** Decagon's "Agent Operating Procedures", Fin's "Procedures" and simulation testing, Narvar's IRIS, parcelLab's "live tool integration rather than guessing". Buyers of AI want to know *how it avoids being wrong*.
5. **Guardrails are marketed as features.** "Knows when to escalate to your team" (Gorgias), brand-tone control and policy injection (parcelLab), testing suites and regression tests (Fin). For AI support, *what it won't do* persuades more than what it will.
6. **A time-to-value path with dates.** Gorgias "50% in 50 days: Today / Day 7 / Day 21 / Day 50"; Kalshi "Touchdown in ten days"; Stripe/Le Monde "<3 months implementation".
7. **Code in the first scroll for developer buyers.** Resend's 6-line send, Razorpay's cURL on the homepage, Clerk's `<SignIn />`. The snippet shows the size of the integration.
8. **A demo you can use without a form.** Fin's industry picker, Stripe's live checkout, Clerk's theme editor.
9. **Transparent pricing on the homepage.** Intercom "$0.99 per outcome"; Clerk "free for first 50,000 MRU". Outcome-based pricing fits AI resolution products.
10. **Visible freshness.** Dated changelog (Linear), "226 product updates in 2025" (Fin), "Recently shipped" (Vercel).
11. **Integration paths that respect existing stacks.** parcelLab's Path A (standalone) vs Path B (plug into your existing bot via endpoint or MCP); Stripe's no-code / pre-integrated / build-your-own. This removes the "rip and replace" objection.
12. **Problem framing through the buyer's P&L.** Narvar gives three problem sections, each with a cost ("$25–$35+ per delivery issue"); Gorgias's WISMO cost maths ("150 WISMO requests per 1,000 orders ≈ $1,860/month"). Slop describes the problem only as "customer frustration".
13. **Contrast with the status quo.** Gorgias "Most brands bolt third-party AI onto a generic helpdesk"; parcelLab "Customers don't want status updates. They want resolution."

**Anti-patterns to avoid:** stacked vague superlatives ("the #1 platform", "leading the next frontier"; even Narvar leans on these); logo walls with no numbers; a dozen near-identical module cards (Narvar has 7); hero copy that could describe any AI company ("Better outcomes"). Sierra gets away with it only because of its enterprise logos, which a new product does not have.

---

## Part C. Recommendations for the AI WISMO site

### C.0 Constraints carried over from PRODUCT.md (they shape everything)

- **No fabricated proof.** No real customers, testimonials, partnerships, deflection rates or order volumes for Smytten/Swish/Zomato. The site's proof must be *the product's own evidence*: 93 sourced public complaints and the Phase-1 replay (see `docs/reports/phase1-coverage.md`: 79 of 80 detectable complaints surfaced before the public post, median lead time 4.3 days, 0 false alarms on 400 healthy orders, **with the stated in-sample caveat**).
- **Brand replicas are concept demos**: a persistent "Concept demo · not affiliated with <brand>" label, styled wordmarks, no copied logos. Case studies must be labelled **"Concept study: illustrative, not a customer"** in the header, the card and the page metadata. Use "Smytten-like / Zomato-like / Swish-like" in page titles where the page could be mistaken for a real engagement.
- Positioning to keep: **delivery truth** (a "Delivered" scan is a claim until proven), **tell before they ask**, **visible statutory clocks** (48-hour acknowledgement and 30-day resolution under the E-Commerce Rules 2020; RBI T+5), **one engineer, days not months**.
- Honest-numbers voice is a competitive edge: every vendor above shows numbers without method. Publish the method.

### C.1 Recommended sitemap

```
/                                   Home
/product                            Platform overview (the order-truth engine)
  /product/shopper-widget           <wismo-order> in-app widget (tell before they ask)
  /product/support-console          Agent console + AI support agent (sees evidence, proposes, human approves)
  /product/ops                      Ops anomaly view (courier / hub / lane)
  /product/delivery-truth           How "claimed" vs "verified" delivery works (the mechanism page)
  /product/clocks                   Statutory clocks & escalations (48 h / 30 d / RBI T+5)
  /product/channels                 In-app, hosted tracking page, WhatsApp, MCP tool for your own bot
/solutions
  /solutions/d2c-parcel             D2C & subscription boxes (days-long clock)        ← Smytten-like
  /solutions/food-delivery          Restaurant food delivery (minutes to an hour)      ← Zomato-like
  /solutions/quick-commerce         10-minute delivery (minutes)                       ← Swish-like
  /solutions/support-teams          By role: CX / support leads
  /solutions/ops-logistics          By role: ops & logistics
  /solutions/engineering            By role: the integrating engineer
/demo                               Demo hub: pick an app, pick a failure, watch it resolve
  /demo/d2c                         Smytten-like concept app with the SDK embedded
  /demo/food                        Zomato-like concept app
  /demo/quick-commerce              Swish-like concept app
  /demo/console                     Same scenario from the support agent's side
/case-studies                       Concept studies index (all labelled illustrative)
  /case-studies/d2c-trial-boxes     "Delivered, but nothing arrived": a Smytten-like concept study
  /case-studies/food-delivery       "Delivered, no food": a Zomato-like concept study
  /case-studies/quick-commerce      "10 minutes, 40 minutes, refund pending": a Swish-like concept study
/evidence                           The complaint corpus + replay method + coverage report (the proof page)
/developers                         Developer landing (3 integration tiers, snippet, sandbox)
/docs                               Docs (see C.5)
/blog                               Blog (see C.4)
  /blog/category/field-notes        Complaint analysis, failure patterns
  /blog/category/engineering        How the engine works
  /blog/category/product            Launches & decisions
  /blog/category/changelog          Dated changelog (also /changelog)
/changelog
/glossary                           WISMO, NDR, RTO, OFD, POD, AWB, RRN/ARN… (SEO entry points)
/pricing                            Outcome-based teaser; "design partner" programme for the POC
/security                           Data handling, PII minimisation, DPDP Act 2023 posture, WCAG 2.1 AA
/about                              Builder story (engineer + product owner), decision log link
/contact  (Book a walkthrough)
```

**Top nav (6 + 2):** Product · Solutions · Demo · Developers · Customers→*Case studies* · Resources (Blog, Evidence, Glossary, Changelog) | **Docs** · **Try the demo** (primary) / Book a walkthrough (secondary).
Rationale: Demo gets top-level placement (Fin), Docs sits in the bar (Linear, Razorpay), and Evidence replaces the logo wall a new product cannot have.

### C.2 Homepage outline, section by section

| # | Section | Content | Borrowed from |
|---|---|---|---|
| 0 | **Announcement bar** | "New: we replayed 93 public order complaints through the engine. Read the method →" | Narvar's assessment bar, Linear changelog |
| 1 | **Hero** | Promise: *"End WISMO hell. Tell customers what really happened to their order before they ask."* Sub: "An order-truth SDK for commerce and delivery apps. Treats 'Delivered' as a claim until it's proven, catches late and stuck orders early, and gives support the evidence to fix them. One engineer, a few days." CTAs: **Try the live demo** (primary) · **Read the quickstart** (secondary). Visual: a **real, running `<wismo-order>` widget** in a phone frame cycling through a scenario ("Courier marked this delivered at 14:02 with no OTP. Did you get it? [Yes] [No]"), not an illustration. | Linear/Sierra real UI; Stripe live demo; Resend code-first |
| 2 | **Honest-proof strip** (replaces the logo wall) | Four numbers with method links: "93 sourced public complaints · 79 of 80 surfaced before the customer posted (in-sample replay) · median 4.3 days earlier · 0 false alarms on 400 healthy orders". Under it: "Concept demos, not customers. See the method →/evidence". | parcelLab pilot numbers with denominators |
| 3 | **WISMO hell (problem)** | Title: *"Your tracker says Delivered. Your customer says it never came. Your bot agrees with the tracker."* A three-column **before / after** of the same order: courier status ("Delivered ✓") · what support's bot says ("Our records show delivered") · what actually happened (no OTP, no photo, phone on parcel ≠ account phone). Cost block with **sourced** industry figures only: WISMO is 25–40% of e-commerce inbound, rising to 50–60% at peak ([ShippyPro](https://www.shippypro.com/blog/en/how-to-reduce-wismo-tickets-in-ecommerce-the-complete-guide)), $4–12 per contact ([ReadyCloud](https://www.readycloud.com/info/what-is-wismo-why-where-is-my-order-questions-cost-retailers-more-than-most-teams-expect)), 3–5 agent minutes each ([WISMO Labs](https://wismolabs.com/what-is-wismo/)). Then our own corpus: "38% of 2025–26 complaints: *marked delivered, nothing arrived*. 36 of the 40 who contacted support say support failed." Include 2–3 verbatim complaint fragments with source links (including the Hinglish one). | Narvar problem-with-cost sections; Gorgias cost maths |
| 4 | **How the AI resolves it** | A 4-step horizontal flow on one real order timeline: **1. Ingest**: carrier, OMS and payment events into one timeline (ONDC/Beckn states, raw codes kept). **2. Derive truth**: "Delivered" becomes *claimed* or *verified* with confidence. **3. Tell first**: exception rules fire (ETA slipped twice, OFD > 24 h, refund > 7 working days with no RRN) and the shopper hears it first, with a reason and a next step. **4. Resolve**: the AI agent has order context and tools (re-attempt, fix phone, open claim); it **proposes** refunds and a human approves; it never closes a ticket in an exception state. Each step shows the actual widget, console or event JSON. | Decagon AOPs / Fin Procedures: name the mechanism |
| 5 | **Guardrails ("what it won't do")** | Six short cards: never shows an unproven "Delivered" as a green tick · never blames the customer · never closes while in exception · a human is always one tap away · refunds are proposals, humans approve · every issue gets a visible ID and clock. | Gorgias "knows when to escalate"; parcelLab guardrails |
| 6 | **Product surfaces** | Tabbed: Shopper widget · Support console · Ops view · WhatsApp · Hosted page · MCP tool for your existing bot. Each tab = a real screenshot or live embed + one sentence + a link. | parcelLab journey tabs; Decagon channel tabs |
| 7 | **Built for your clock** | Three cards, one per vertical, each showing the **same engine on a different clock**: D2C parcel (days), food delivery (minutes to an hour), quick commerce (minutes). Each card: the concept app in its own skin + "Open live demo" + "Read the concept study". Label: "Concept demos · not affiliated with the brands shown". | Stripe business-model sections; Vercel "customer + number" |
| 8 | **SDK integration** | Heading: *"Drop it in this week."* Left: 3 integration tiers (hosted page: zero code · `<wismo-order>` web component themed by a token file · headless API/SDK + webhooks + MCP). Right: tabbed code (HTML / React / REST / MCP), ~8 lines, e.g. `<script src=".../wismo.js"></script><wismo-order order-id="…" theme="./brand.tokens.json"></wismo-order>` and a `POST /v1/events` for carrier scans. Under it: "Keeps your OMS and helpdesk. Adapters for Shiprocket/Delhivery-style carrier events, Zendesk/Freshdesk handoff." CTA: Quickstart (5 min) · Sandbox keys. | Stripe 3 paths; Resend snippet; Clerk components; parcelLab Path A/B |
| 9 | **Visible clocks** (differentiator) | A live countdown card: "Issue #W-2231 · acknowledged in 2 h (limit 48 h) · resolution due in 27 d (limit 30 d)". Explains E-Commerce Rules 2020 and RBI T+5, plus a ready-to-file escalation on breach. "No vendor we found exposes these to the customer." | Unique to us; framed like Fin's trust list |
| 10 | **Concept case studies** | 3 cards with an "Illustrative" badge, each with a replay-derived number, not a fabricated one (e.g. "35 'marked delivered' complaints: all 35 flagged in replay"). Link to /case-studies. | Decagon/Intercom metric cards |
| 11 | **Evidence & method** | "How we measure": replay diagram, in-sample caveat, the 13 item problems that need the customer's report, the one miss (IC-207446) named. Link to /evidence and the coverage report. | parcelLab pilot FAQ; our honesty principle |
| 12 | **Security & compliance** | PII minimisation (order ID + event stream; phone numbers hashed for mismatch checks), DPDP Act 2023 posture, data residency (India region), WCAG 2.1 AA, audit log of every AI action and approval. **Only claim what is true**: no SOC 2 badge until one exists; write "roadmap" instead. | Sierra/Fin trust walls, adapted honestly |
| 13 | **Pricing teaser** | "Pay per resolved order issue, not per seat. Free sandbox. Design-partner pricing for the first platforms." | Intercom $0.99/outcome; Clerk free tier |
| 14 | **Latest** | 3 blog/changelog items with dates. | Linear changelog; Stripe "What's happening" |
| 15 | **Final CTA** | "Stop answering 'where is my order'. Start telling." · Try the live demo · Read the quickstart · Book a 20-minute walkthrough. | Stripe/Intercom repeated pair |

### C.3 Case-study template (concept study)

```
[Badge, pinned in the header: CONCEPT STUDY: illustrative. Not a customer. Not affiliated with <Brand>.]
Breadcrumb: Case studies › Quick commerce

H1: outcome or turning-point headline
    e.g. "When 'Delivered' isn't: catching a false delivery in a 10-minute app before the customer calls"
Sub: one sentence on the platform archetype ("A Swish-like 10-minute food delivery app in Bangalore")

Metric callouts (3), each with a source tag:
  [Replay] 35 of 35 'marked delivered' complaints flagged | [Replay] median 4.3 d earlier | [Scenario] 0 → 1 tap to a human
  (tags: Replay = engine run over public complaints; Scenario = scripted demo; never "Customer reported")

Facts sidebar:
  Archetype · Clock (minutes / days) · Order sources simulated (carrier, OMS, payments)
  Surfaces used (widget, console, WhatsApp, ops) · Integration tier (web component / API)
  Complaints this study is built on (IDs, linked) · Time to integrate (our build log, honest)

1. The situation: the archetype's delivery model and why its WISMO is different (the clock)
2. What customers actually said: 3 verbatim complaint fragments with permalinks and dates
3. Where today's stack fails: courier status → tracker → bot, each repeating the same wrong fact
4. What the SDK does: steps that answer each failure in §3 one-to-one (Decagon pattern),
   with real screenshots of the concept app + event timeline JSON excerpt
5. Results in the replay: table of scenario → rule that fired → minutes/days before complaint
   + "What this doesn't prove" box (in-sample, synthesized timelines)
6. Try it yourself: embedded demo launcher preset to this scenario
7. What's next: what a real pilot would measure (deflection, reopen rate, time-to-truth)

CTA pair: Open this scenario in the demo · Read the quickstart
Related: the other two concept studies
```

### C.4 Blog-post template and blog organisation

**Categories (4 + changelog):** *Field notes* (complaint analysis, e.g. "Why 'marked delivered' went from 6% to 38% of complaints"), *Engineering* (event model, detectors, the replay harness), *Product* (decisions, cut list, ADR-backed posts), *Guides* (WISMO playbooks, SEO long tail: "What is NDR", "RBI T+5 explained"), *Changelog* (dated). Titles state a specific problem or finding, like Linear's.

```
Category · Date · Reading time
H1: specific claim or question ("A courier's 'Delivered' is a claim, not a fact")
Byline (name, role) · Updated date if revised

TL;DR box: 3 bullets, the finding, the evidence, what to do
Body:
  - Open with one real complaint (verbatim, linked)
  - The pattern (chart from data/complaints.json; the denominator is always shown)
  - The mechanism (diagram / event JSON / rule pseudo-code)
  - Limits and what we don't know (mandatory section)
  - What we built / what you can do today
Inline CTA (once, mid-post): "See this scenario in the live demo →"
Footer: related posts · "Built from" (sources list with URLs) · subscribe · link to docs page
```

### C.5 Docs structure and quickstart template

**Docs IA:**
```
Get started      Overview · Quickstart (5 min) · Concepts (order timeline, claimed vs verified,
                 exceptions, clocks) · Sandbox & test scenarios
Integrate        Hosted tracking page · Web component <wismo-order> · Theming with tokens ·
                 Headless API/SDK · Sending carrier/OMS/payment events · Webhooks
Support & AI     Agent tools · Human approval flow · Helpdesk handoff (Zendesk/Freshdesk) ·
                 MCP server for your existing bot · Guardrails reference
Ops              Anomaly view · Alert rules
Clocks & compliance  E-Commerce Rules 2020 clocks · RBI T+5 · Escalation packets · Accessibility
Reference        REST API (OpenAPI-generated) · Event schema · Status taxonomy & raw-code mapping ·
                 Detector/rule catalogue · Error codes · Changelog
For AI agents    llms.txt · MCP · copyable integration prompts (Razorpay pattern)
```

**Quickstart template (Stripe two-pane + Resend brevity + Clerk agent path):**
```
H1: Show order truth in your app in 5 minutes
Intro line: what you'll have at the end (a widget that flags an unproven delivery)
Choose your stack: [HTML] [React] [React Native] [REST only]     ← switcher changes all code
Prerequisites: a sandbox key (no card, no sales call); Node 20+ (for SDK path)

Left pane: steps                                  Right pane: full file tree + Download
1. Install         npm i @wismo/sdk   (npm/pnpm/yarn/bun tabs)
2. Set your key    WISMO_KEY=sk_test_…
3. Send one event  POST /v1/orders/{id}/events  {type:"delivered", proof:null}
4. Drop in the widget  <wismo-order order-id="ord_test_unproven">
5. See it work     "You should see: 'Marked delivered at 14:02 with no proof. Did you get it?'"

Test scenarios table (like Stripe's test cards):
  ord_test_verified       → delivered with OTP   → green, verified
  ord_test_unproven       → delivered, no proof  → asks the shopper
  ord_test_stuck_ofd      → OFD for 26 h         → exception + new ETA
  ord_test_refund_ageing  → refund 8 working days, no RRN → refund exception + T+5 clock
  ord_test_qc_late        → quick commerce, 10 min promise, 25 min elapsed → minute-clock exception

"Using a coding agent?" box: one copyable prompt + MCP install line
Next steps: theme it · connect your carrier · hand off to your helpdesk · go live checklist
```

### C.6 Demo page template

Model: Fin's ungated industry picker + Stripe's operable demo + Clerk's theme editor. No form. This page is the most persuasive asset the POC has.

```
H1: See the SDK inside three apps. Break an order and watch what happens.
Persistent label: Concept demos · not affiliated with Smytten, Zomato or Swish · data is simulated

Step 1: Pick an app (3 phone frames, each in its own skin):  D2C box · Food delivery · 10-min delivery
Step 2: Pick a failure (chips, each citing its source complaint ID):
        Courier marks delivered, no OTP · Stuck out for delivery · ETA slipped twice ·
        Refund "initiated", no bank ref · Paid, no order · Wrong phone on parcel
Step 3: Play the clock: ▶ play / step / 10× speed; a scrubber shows the event timeline

Layout (desktop): [Phone: host app + widget] [Engine feed: events, derived state, rules fired]
                  [Support console: same order, evidence, proposed action awaiting approval]
Mobile: the phone frame fills the screen; feed and console become tabs

Interactions: answer "Did you get it?" as the shopper; approve/reject the refund as the agent;
              toggle theme tokens to see one widget take on three brands (Clerk theme-editor idea);
              "Show me the code" drawer reveals the exact events + component markup behind the view
Footer strip: "This scenario is built from complaint IC-XXXXX (link)" · Read the concept study ·
              Quickstart · Book a walkthrough
```

### C.7 Two cross-cutting recommendations

1. **Serve agents too.** Stripe (`stripe docs` in the terminal), Resend (`/docs/llms.txt`), Clerk (agent-oriented quickstart with an approval checklist) and Razorpay (copyable prompts, MCP) all make docs readable by coding agents as of 2026; fetching resend.com and clerk.com here returned agent-oriented markdown instead of the visual page. Ship `/llms.txt`, markdown twins of the docs pages, and an MCP server from day one; it also demonstrates engineering judgement to the hiring-manager audience.
2. **Evidence is the proof, instead of logos.** Every competitor sells with logos plus unexplained percentages. With no customers, the credible move is the reverse: sourced complaints, a published replay method, named misses and caveats. The /evidence page and the "Replay / Scenario" source tags on every number can do the job that social proof does for established vendors.

---

## Sources

- Stripe: https://stripe.com · https://stripe.com/customers/instacart · https://stripe.com/blog · https://docs.stripe.com/ · https://docs.stripe.com/checkout/quickstart · https://checkout.stripe.dev/
- Intercom / Fin: https://www.intercom.com/ · https://fin.ai/ · https://fin.ai/view-demos · https://www.intercom.com/customers · https://fin.ai/customers/kalshi · https://fin.ai/pricing
- Narvar: https://corp.narvar.com/
- AfterShip (403 to fetcher; via search): https://www.aftership.com/ · https://www.aftership.com/tracking · https://www.aftership.com/glossary/wismo · https://www.aftership.com/tools/order-lookup-widget
- parcelLab: https://parcellab.com/ · https://parcellab.com/wismo-agent/
- Gorgias: https://www.gorgias.com/ · https://www.gorgias.com/customers/pit-viper · https://www.gorgias.com/blog/automate-wismo-requests
- Sierra: https://sierra.ai/
- Decagon: https://decagon.ai/ · https://decagon.ai/case-studies · https://decagon.ai/case-studies/rippling · https://decagon.ai/glossary/what-is-wismo-where-is-my-order
- Razorpay: https://razorpay.com/ · https://razorpay.com/docs/
- Linear: https://linear.app/ · https://linear.app/customers · https://linear.app/customers/openai · https://linear.app/blog
- Vercel: https://vercel.com/
- Resend: https://resend.com/ · https://resend.com/docs/send-with-nodejs · https://resend.com/docs/introduction
- Clerk: https://clerk.com/ · https://clerk.com/docs/quickstarts/nextjs · https://clerk.com/components
- WISMO cost benchmarks: https://www.shippypro.com/blog/en/how-to-reduce-wismo-tickets-in-ecommerce-the-complete-guide · https://www.readycloud.com/info/what-is-wismo-why-where-is-my-order-questions-cost-retailers-more-than-most-teams-expect · https://wismolabs.com/what-is-wismo/ · https://www.salesforce.com/commerce/wismo/
- Internal: D:\Wismo\PRODUCT.md · D:\Wismo\docs\00-product-brief.md · D:\Wismo\docs\reports\phase1-coverage.md
