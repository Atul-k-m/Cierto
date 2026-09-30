# Pakka product site: visual references

Captured 2026-09-30 with Playwright (Chromium, 1440x900 viewport, DPR 1). Files ending in `-full.png` are full-page captures of the five strongest pages. Section files are 1440x900 crops taken from those full-page captures at the named section. Dribbble and Behance files are the original shot images.

Pinned world: cloud-white field, slate ink, light humanist sans. Colour appears only as a thin mint/rose/violet spectral edge. Most references below are light and restrained. Where a reference is dark (Linear, Resend, Stripe code band), only the structure is being borrowed.

Other folders: `_also-captured/` holds site heroes that were checked and rejected (reasons at the end). `grids/`, `shots/` and `sky/` in this folder were written by a different, concurrent process and are not indexed here.

## Quick map: Pakka page → references

| Pakka page / section | Primary refs |
|---|---|
| Home hero with live widget | R02 Attio, R05 ElevenLabs, R08 Vapi, R10 Inkeep, R11 Lorikeet, R01 Stripe, R09 Mintlify |
| "WISMO hell" problem | R03 Plain (problem turn), R15 WISMOlabs, R18 ClickPost, R06 Fin |
| How the AI resolves an order | R10 Inkeep, R06 Fin (procedure), R21 Harbor, R17 parcelLab, R04 Knock |
| SDK / code integration | R01 Stripe (3 paths), R29 Resend, R05 ElevenLabs, R04 Knock, R10 Inkeep toggle, R14 Clerk, R03 Plain (time-to-value) |
| Proof / metrics | R02 Attio, R01 Stripe band, R06 Fin chart |
| Case studies | R22 Plain×Resend, R23 Stripe×Instacart, R24 Sierra, R25 Linear |
| Blog | R26 Vercel, R27 Linear Now |
| Interactive demos | R16 AfterShip store generator, R08 Vapi, R05 ElevenLabs, R28 Stripe quickstart |
| Docs | R28 Stripe docs, R09 Mintlify |
| Visual-world push | R30 Fastino, R09 Mintlify, R19 Trackora, R20 Alotra, R11 Lorikeet |

---

## A. Heroes built around a live product

**R01 · Stripe home** ★ full page
- Files: `stripe-home-hero.png`, `stripe-home-product-bento.png`, `stripe-home-metrics-band.png`, `stripe-home-integration-code.png`, `stripe-home-full.png`
- Source: https://stripe.com/in (payments platform homepage)
- Borrow:
  - The hero headline is one long sentence in two ink tones (deep clause, then a slate continuation). The only colour is a ribbon that bleeds off the right edge, which is the closest big-brand version of a "spectral edge".
  - In the bento, each tile holds a real UI fragment (a phone checkout or a form) cropped by the card, with a colour wash fading at one edge.
  - The integration band splits into three paths (No-code / Pre-integrated platforms / Build your own), with the terminal as the third column.
  - The metrics band has four numerals in a hairline table.
- Informs: the home hero type treatment, the SDK section (three paths: drop-in widget / platform plugin / SDK) and the proof band.

**R02 · Attio home**
- Files: `attio-home-hero.png`, `attio-home-scale-metrics.png`
- Source: https://attio.com (AI CRM)
- Borrow:
  - The headline is centred, with a real app window rising from the bottom edge. Inside the window an AI answer streams into the actual app chrome, so the hero product is live rather than a static screenshot.
  - In the scale section, stat pairs have a hairline left rule, and the only colour is a single thin blue growth curve over a hatched field.
- Informs: how the hero widget is staged (a Pakka reply streaming inside host-app chrome) and the proof metrics.

**R03 · Plain home** ★ full page
- Files: `plain-home-hero.png`, `plain-home-problem-turn.png`, `plain-home-time-to-value.png`, `plain-home-full.png`
- Source: https://www.plain.com (AI support infrastructure for B2B)
- Borrow:
  - The problem is stated as one typographic sentence with the chaos inlined as icons: "Tools add [12 app icons, 999+ badge] distance." A quiet "But what if it was different?" then hands over to the solution.
  - The time-to-value section reads "29 mins and 59 secs", laid out as 5 / 15 / 29-minute checklist columns.
- Informs: the WISMO hell section (inline courier SMS, IVR, WhatsApp and email icons with a 999+ badge) and the SDK "live in an afternoon" block.

**R04 · Knock home** ★ full page
- Files: `knock-home-hero.png`, `knock-home-cli-code.png`, `knock-home-full.png`
- Source: https://knock.app (messaging infrastructure, devtool)
- Borrow:
  - The hero sits on a light dotted-grid field. A tabbed product panel shows a workflow graph on the left and the agent's chat on the right.
  - In the CLI section, a terminal overlaps an AI-IDE window. CI/CD is drawn as a vertical commit timeline of mono pills.
- Informs: How the AI resolves (the decision graph beside the conversation) and the SDK section.

**R05 · ElevenLabs home** ★ full page
- Files: `elevenlabs-home-hero.png`, `elevenlabs-home-api-code-light.png`, `elevenlabs-home-full.png`
- Source: https://elevenlabs.io (voice AI platform)
- Borrow:
  - A tab switcher for the product lines (Creative / Agents / API) sits in a soft grey tray above a playable carousel, so the product can be used in the first viewport.
  - The API section is laid out in light mode: copy on the left and a white code card on the right in each hairline grid cell.
- Informs: hero widget tabs (D2C / Food delivery / Quick-commerce) and a light-mode code section.

**R06 · Intercom Fin home** ★ full page
- Files: `fin-home-hero.png`, `fin-home-proof-chart.png`, `fin-home-procedure-ui.png`, `fin-home-full.png`
- Source: https://fin.ai (AI customer agent)
- Borrow:
  - The whole homepage is a numbered editorial ledger, "22 reasons" (01–22). Each item has a heading, a paragraph and one staged UI, which gives a very even section rhythm.
  - The proof chart shows three bar charts where only Fin's bar is coloured and competitors are grey.
  - The procedure section puts the policy document next to the chat it produces.
- Informs: How the AI resolves (show the rule beside the reply), the proof section and overall section rhythm.

**R07 · Linear home**
- File: `linear-home-hero.png`
- Source: https://linear.app
- Borrow: the canonical "full app window as hero", with an AI agent panel docked bottom-right over the app. Dark here; invert it to cloud-white.
- Informs: staging Pakka as a sheet or panel that overlays the host app's order screen.

**R08 · Vapi home**
- File: `vapi-home-hero-live-call-demo.png`
- Source: https://vapi.ai (voice agents for developers)
- Borrow: the hero holds a real control, a scenario dropdown ("Appointment Scheduling") plus a "Start call" button. One pick and one action lead straight into the product.
- Informs: the hero widget (pick an order state, then ask "where is my order?") and the demo page.

**R09 · Mintlify home**
- File: `mintlify-home-hero.png`
- Source: https://mintlify.com (docs platform)
- Borrow: bundles of fine iridescent hairlines sweep behind a docs UI on a white field. This is the nearest live site to "colour only as a thin spectral edge". There is also a small live "agent traffic" ticker pill above the headline.
- Informs: the hero background treatment and the docs landing.

**R10 · Inkeep home**
- Files: `inkeep-home-hero.png`, `inkeep-home-ticket-resolve-card.png`, `inkeep-home-code-visual-toggle.png`
- Source: https://inkeep.com (AI agents for CX)
- Borrow:
  - A pale-sky panel holds a support-ticket card whose status checklist ticks in mono caps: ALL CONTENT LOADED, ALL SYSTEMS OK, WEB SEARCH, RESOLVED.
  - A "No-code builder ⟷ 2-way sync ⟷ TypeScript SDK" toggle shows the visual builder and the code side by side.
- Informs: How the AI resolves (a checklist of the signals Pakka read: order DB, courier scan, EDD, policy) and an SDK section that speaks to both CX and engineering.

**R11 · Lorikeet home**
- File: `lorikeet-home-hero.png`
- Source: https://www.lorikeetcx.ai (AI support concierge)
- Borrow: behind a light field and serif headline, a spectral glow (magenta to yellow vertical bars) rises along the top edge of the product frame. Recoloured to mint/rose/violet, this is the "iridescent edge" almost exactly.
- Informs: the edge treatment on the hero widget frame.

**R12 · Granola home**
- File: `granola-home-hero.png`
- Source: https://www.granola.ai (AI notepad)
- Borrow: an asymmetric hero with the headline left and a product window bleeding off the right edge over textured panels. There is one quiet CTA.
- Informs: an alternate, left-weighted home hero.

**R13 · Sierra home**
- File: `sierra-home-hero.png`
- Source: https://sierra.ai (AI customer agents)
- Borrow: translucent chat bubbles are overlaid on full-bleed film of a real customer, which stages the conversation in the customer's world.
- Informs: case-study and brand moments, e.g. an Indian customer waiting on a food order with Pakka bubbles overlaid. Too heavy for a cloud-white hero.

**R14 · Clerk home**
- File: `clerk-home-hero-copy-command.png`
- Source: https://clerk.com (auth SDK)
- Borrow: a single copyable command pill under the hero ("Add Clerk auth to my app: clerk.com/SKILL.md").
- Informs: a secondary hero CTA or the SDK section, e.g. a copy pill with the install line or agent prompt (package name TBD).

## B. Order tracking, logistics and WISMO

**R15 · WISMOlabs** (direct category competitor)
- Files: `wismolabs-home-hero.png`, `wismolabs-home-problem-section.png`, `wismolabs-home-comparison-table.png`
- Source: https://wismolabs.com
- Borrow:
  - The hero diagram reads "same carrier event, different journey context": a journey timeline runs across the top, with rows of context leading to decision chips.
  - The problem section is titled "A carrier event is not a customer answer." It features the customer's real question as a pull quote ("Where is my order – and what happens next?") beside four failure modes.
  - A two-column table compares "event-to-message" with a "context response".
- Informs: the content structure of WISMO hell and the comparison block. Differentiate visually, since theirs is warm beige and yellow.

**R16 · AfterShip**
- Files: `aftership-home-hero.png`, `aftership-tracking-store-demo.png`
- Sources: https://www.aftership.com and https://www.aftership.com/tracking
- Borrow:
  - On the home page, a Tracking/Returns tab switcher sits over a branded tracking page, with a lock-screen notification floating off the frame corner.
  - The tracking page offers "Customize your store mockup with one click": enter a store URL, press Generate, and get a personalised demo.
- Informs: the interactive demo page ("enter your app name or brand colour, see Pakka in your skin") and the notification detail on the hero.

**R17 · parcelLab: Reduce WISMO**
- File: `parcellab-reduce-wismo-hero.png`
- Source: https://parcellab.com/reduce-wismo-wismr/
- Borrow: a thin connector line runs from the chat bubble to the order record card (#12345). It makes "the AI looked up the order" legible without any explanation.
- Informs: How the AI resolves (connect the reply to its data source).

**R18 · ClickPost** (Indian logistics intelligence, a local reference buyers know)
- File: `clickpost-home-hero.png`
- Source: https://www.clickpost.ai
- Borrow: on a light particle-cloud field, before→after chips drift ("Manual label generation → Automated, all carriers", "No EDD on site").
- Informs: an ambient hero option and the WISMO hell → resolved transition. It fits the cloud-white field naturally.

**R19 · Dribbble: Trackora, AI order-tracking SaaS**
- File: `dribbble-trackora-ai-order-tracking-saas.jpg`
- Source: https://dribbble.com/shots/27404671-Trackora-AI-Powered-Order-Tracking-SaaS
- Borrow: a crisp white dashboard floats over a soft sky/cloud photograph, with an AI insight card ("High risk of delay") as a distinct component.
- Informs: the hero field option and a "risk of delay" card for the widget.

## C. AI support concepts (galleries)

**R20 · Dribbble: Alotra, AI support landing**
- Files: `dribbble-alotra-ai-support-cloud-landing-1.jpg`, `dribbble-alotra-ai-support-cloud-landing-2.jpg`
- Source: https://dribbble.com/shots/27383650-Alotra-AI-Customer-Support-Landing-Page
- Borrow:
  - The hero puts a frosted glass frame on a cloud-sky gradient, with a condensed serif headline and a browser window below.
  - The second image shows a calm section rhythm: 4 step cards, a stats row and a chat module.
- Informs: pushing the cloud world. Avoid its stock-landscape imagery, which reads as a template.

**R21 · Behance: Harbor, human-in-the-loop AI support**
- File: `behance-harbor-ai-support-agent-site.png` (long case board)
- Source: https://www.behance.net/gallery/255621209/AI-Customer-Support-Agent-Control-App-SaaS-Website
- Borrow:
  - The framing is "Action over chat". A decision card ("Review refund $124 · Policy match 94% · Deny / Approve & Send") is the unit of work.
  - A giant pale-grey wordmark sits behind the phone, and an iOS notification serves as the entry point.
- Informs: How the AI resolves plus the escalation/handoff state, and phone staging on a cloud-grey field.

## D. Case studies

**R22 · Plain × Resend case study**
- File: `plain-case-study-resend.png`
- Source: https://www.plain.com/customers/resend
- Borrow: the header holds three big numerals with mono caps labels (33% AUTOMATED RESOLUTION RATE / 50 HOURS SAVED PER WEEK / ZERO NEGATIVE SENTIMENT), followed by a pull quote at display size.
- Informs: the case study header template (swap the dark band for cloud-white with a spectral underline).

**R23 · Stripe × Instacart case study and customers index**
- Files: `stripe-case-study-instacart.png`, `stripe-customers-index.png`
- Sources: https://stripe.com/in/customers/instacart and https://stripe.com/customers
- Borrow:
  - The case study has a title plus a right sidebar card (logo, products used, region, segment), and metrics as a left-ruled stat stack beside the body copy. Its delivery-business subject is a close analogue.
  - The index uses offset, stacked photo cards.
- Informs: the case study detail layout and the customers index.

**R24 · Sierra: Chime case study and customers grid**
- Files: `sierra-case-study-chime.png`, `sierra-customers-metric-grid.png`
- Sources: https://sierra.ai/customers/chime and https://sierra.ai/customers
- Borrow: a single metric overlaid on the image ("70%+ Resolution rate"). In the index grid, some tiles carry one metric ("+33 points NPS") and the rest are pure logo or photo.
- Informs: customers index tiles that lead with the metric.

**R25 · Linear customers**
- File: `linear-customers-index.png`
- Source: https://linear.app/customers
- Borrow: a 3-column tile grid with filter tabs by segment. Each tile's title is an outcome sentence rather than a company name.
- Informs: filtering case studies by vertical (D2C beauty / Food delivery / Quick-commerce).

## E. Blog

**R26 · Vercel blog**
- File: `vercel-blog-index.png`
- Source: https://vercel.com/blog
- Borrow: type-only cards (no thumbnails) with a date and category label, a large headline and author avatars, all on a hairline grid. It is the cheapest layout to keep looking good and matches the restraint.
- Informs: the blog index.

**R27 · Linear Now**
- File: `linear-now-index.png`
- Source: https://linear.app/now
- Borrow: one index mixes Changelog, Product launches, From the team and Customer stories under filter tabs. Cards use generative monochrome art.
- Informs: a blog that also carries SDK changelog entries.

## F. Docs, code and demos

**R28 · Stripe docs: quickstart builder**
- File: `stripe-docs-quickstart-builder.png`
- Source: https://docs.stripe.com/payments/quickstart
- Borrow: frontend and backend language chips sit at the top. Step prose runs on the left, and a sticky code panel with file tabs on the right highlights the lines for the current step. There is a "Download example" button.
- Informs: the docs integration guide and a deeper SDK page.

**R29 · Resend: "Integrate this morning"**
- File: `resend-home-code-tabs.png`
- Source: https://resend.com
- Borrow: a row of platform icons (Node, Ruby, Python, …) with framework sub-tabs sits over one code block. The copy frames integration in hours.
- Informs: the SDK section's platform tabs (React Native / Android / iOS / Flutter / Web). Structure only; render it in light mode.

## G. Visual-world push

**R30 · Godly (now recent.design): Fastino Labs identity**
- File: `godly-fastino-labs-iridescent-identity.png`
- Source: https://recent.design/i/0lj68ni-fastino-labs-brand-identity (Godly redirects to recent.design)
- Borrow: a pastel impressionist cloud landscape with a clear oval "lens" carrying a star mark. The headline behind the lens is blurred. The lens is a strong metaphor for "bringing one order into focus".
- Informs: brand moments (hero option D4, blog art, 404). Keep it editorial, not part of the UI chrome.

---

## Sources searched but not kept

- **Pinterest:** search results sit behind a login modal. Only the blurred grid behind the modal was visible, so it was skipped.
- **Mobbin (web):** redirects to a login/landing page, so nothing was captured.
- **Awwwards (SaaS category), Land-book (SaaS feed), Lapa Ninja (SaaS/AI), SaaSFrame:** reviewed. The feeds were dominated by Framer/Webflow templates and purple-gradient AI SaaS, so they were rejected. Lapa's AI category led to Restate and Greptile, which were checked and not kept.
- **Dribbble AI-support shots** (Mios.AI, HueChat, Aerthery, Agentic CS, API Platform, API Landing) and **Behance** (Zendesk redesign, B2B AI SaaS, CS Agent Website): rejected as generic gradient templates.
- **`_also-captured/`** holds site heroes that were captured and rejected:
  - Vercel: an abstract triangle with no product.
  - Resend: a dark 3D cube.
  - Decagon: an illustrated lilac photo.
  - Narvar: dark navy, a robot mascot and rainbow gradient text, which is the anti-pattern.
  - Gorgias: a busy street photo with chat overlay.
  - Raycast: dark red.
  - parcelLab home: a saturated blue animation card.
  - Dribbble Tranzit: a generic app shot.

---

## Homepage directions

All four keep a cloud-white field, slate ink and a light humanist sans. Colour appears only as a 1–2px mint/rose/violet spectral edge. Each direction assigns that edge a different job.

### D1 · Live Ticket (product frame as hero)
- **Grounded in:** R02 Attio, R10 Inkeep, R08 Vapi, R11 Lorikeet, R05 ElevenLabs, R14 Clerk
- **First viewport:**
  - A centred two-line headline (~64px, slate ink) with a one-line subline.
  - Two CTAs: "Book a demo" and a copy pill with the SDK install line (R14).
  - A wide cloud-white frame rises from the fold, with a hairline border and a spectral glow along its top edge (R11). Inside it:
    - Left: the customer's chat inside a host-app skin.
    - Right: "What Pakka checked", a mono-caps checklist that ticks down (ORDER FOUND · COURIER SCAN 2H AGO · EDD 3 OCT · POLICY: NO ACTION) (R10).
  - Scenario chips above the frame: Delayed / Out for delivery / RTO risk / Food: rider stuck (R08).
- **Section order:**
  1. Hero widget
  2. Indian D2C/food logo row
  3. WISMO hell, as a Plain-style inline-chaos sentence (R03)
  4. How it resolves, as three steps each shown with the policy next to the reply (R06)
  5. SDK: Stripe three paths plus Resend platform tabs (R01/R29)
  6. Proof: Attio stat pairs plus one curve (R02)
  7. Case studies, with the Plain metric header (R22)
  8. Docs/blog teaser
  9. CTA
- **Signature interaction:**
  - Picking a scenario chip types the customer's question, ticks the checklist line by line, then streams Pakka's answer.
  - While Pakka "thinks", the spectral edge travels around the frame border. It settles to mint on resolve and rose on escalation to a human.

### D2 · The Order Line (journey timeline as the page spine)
- **Grounded in:** R15 WISMOlabs, R17 parcelLab, R04 Knock, R18 ClickPost, R01 Stripe, R28 Stripe docs, R23 Stripe×Instacart
- **First viewport:**
  - A split layout. The left 5 columns hold a Stripe-style two-tone headline (dark clause, then a slate continuation) and CTAs.
  - The right 7 columns hold a horizontal order line (Placed → Packed → Shipped → Out for delivery → Delivered). The line is a 1px spectral gradient hairline and is the only colour on the page.
  - Customer question chips hang above the nodes ("No update for 2 days?"). Thin connectors run from each question down to Pakka's answer card below the line (R17).
- **Section order:**
  1. Timeline hero
  2. "A tracking status is not an answer" (R15 structure with Pakka's own numbers)
  3. A pinned-scroll walk down the line, where each stage becomes a section showing what Pakka does there
  4. Same event, different context: a D2C prepaid / COD / food-delivery toggle (R15)
  5. SDK as a docs-style split, with steps left and sticky code right (R28)
  6. Stripe hairline metrics band
  7. Case studies in the Instacart layout
  8. Vercel type-card blog
- **Signature interaction:** dragging the "you are here" node along the line re-asks the question at that stage. Pakka's answer card morphs in place, and ClickPost-style before→after chips flip from "customer asks" to "Pakka told them first".

### D3 · The Ledger (numbered editorial chapters with a sticky phone)
- **Grounded in:** R06 Fin, R03 Plain, R21 Harbor, R26 Vercel, R22 Plain×Resend, R12 Granola
- **First viewport:**
  - A left-aligned editorial headline (~88px, light weight, tight tracking) over a short dek.
  - The right margin holds a numbered chapter index (01 WISMO hell · 02 How Pakka resolves · 03 One SDK · 04 Proof · 05 Stories) that doubles as in-page nav.
  - A phone at ~60% scale sits low in the right margin, showing a D2C listing app with the Pakka sheet open.
- **Section order:**
  - Five to seven numbered chapters, each with a number, heading, paragraph and exactly one staged artifact (R06): inbox flood, decision card (R21), code block, metric chart with a single accent bar (R06), case quote (R22).
  - Hairline rules between chapters, generous whitespace.
  - It ends with a Vercel-style type-only blog row and a docs link.
  - Colour appears only as the spectral underline under the active chapter number.
- **Signature interaction:** the phone stays sticky and changes state per chapter as you scroll:
  - 01: a flood of "where is my order??" notifications.
  - 02: Pakka answering, with a Harbor-style "policy match" chip.
  - 03: the code overlay.
  - 04: the numbers.

  This fits a CX lead reading top to bottom.

### D4 · Cloud Lens (visual-world push)
- **Grounded in:** R30 Fastino, R09 Mintlify, R19 Trackora, R20 Alotra, R18 ClickPost, R13 Sierra
- **First viewport:**
  - A full-bleed, very pale cloud field (painted or generative particle cloud at low contrast).
  - Blurred WISMO messages drift behind it ("where is my order??", "still not delivered", "call me back").
  - A small headline sits above a centred glass oval "lens" with a mint→rose→violet rim (R30). Inside the lens, one order card is perfectly sharp: status, ETA, and Pakka's one-line answer.
- **Section order:**
  1. Lens hero
  2. WISMO hell: the drifting messages multiply into a wall with a 999+ count (R03)
  3. Resolution: the lens passes over messages and each one resolves into an answer card
  4. SDK as light code cards on a hairline grid (R05)
  5. Proof: a single curve (R02)
  6. Case studies as metric-on-image tiles (R24)
  7. Blog
- **Signature interaction:**
  - The lens follows the pointer or scroll. Whatever question sits under it snaps into focus as Pakka's answer.
  - On touch and with reduced-motion, it falls back to a static lens cycling three questions.
  - Keep blurred text decorative (`aria-hidden`) and the real content outside the effect.
