---
version: 1
slug: "apps-web-src-site"
primary_target: "apps/web/src/site"
related_targets: ["apps/web/src/widget","apps/web/src/hosts"]
---

# Cierto product site

Scope: the product site for Cierto (renamed from Pakka on 2026-09-30), an AI WISMO SDK that answers every "where is my order?" from live order, courier and rider data and fixes what's wrong inside the host's policy.

Pages, consolidated:
- Home
- Demos
- Case studies (index plus one page each for Smytten, Swish and Zomato, with charts and insights from the review mining)
- Docs

"Built by" is linked from the footer only. There are no nav links to pages that don't exist. Mode: **Persuade** for the home page; Demos is Operate; Docs and Case studies are Read.

Audience: a CX or engineering lead at an Indian D2C, food or quick-commerce company. The site should feel like serious infrastructure with calm precision, carried by rich transitions and motion (the user's words).

Proof available:
- review-mining data in `docs/research/wismo-*.md`
- the root-cause research in `research/notes/`
- the replay of 93 Smytten complaints
- the live engine and SDK

Never invent customers, deflection figures or testimonials.

Quality references, for the bar only and never to copy: the Hermes Agent site (consistency, nav, committed colour) and the City of Mist cards (motion drama). The rejected worlds were sky photos, cloud imagery, kraft/waybill, hazard stripes and anything kiddish.

## Direction contract

THESIS: "Where is my order? Answered." The page proves Cierto by answering real WISMO questions in front of the visitor. It refuses the category's gradient-hero-plus-dashboard-screenshot, and it refuses decorative weather.

OWN-WORLD:
- Ground: calm paper #f3f4f2.
- Ink: #0b0f17.
- Accent: one electric ultramarine, #3a2bff.
- Structure: a visible 12-column hairline grid.
- Type: condensed display (Archivo at 62% width, weight 650); Inter Tight for UI and body; JetBrains Mono for uppercase labels and data.
- Corners: square. Surfaces are white panels with a single deep shadow.
- The only effect: a drifting ordered-dither mist in the accent colour, which stands in for the "cloud effect".
- Charts are drawn in ink and accent only.

STORY:
1. WISMO is 20–40% of support, and shoppers suffer six causes: stuck rider, traffic, batched orders, bad addresses, silent couriers, and "delivered" without the parcel. Cierto answers each one with sources and a promise.
2. It acts inside your policy.
3. It integrates in a few lines.
4. The case studies show the data.

FIRST VIEWPORT:
- Nav: logo, Product, Demos, Case studies, Docs, with "Try it live" on the right.
- Left: a mono index line, then "Where is my order? Answered." at about 118px with the last word in accent, a sub, and two square CTAs.
- Right: a dithered-mist field (live canvas) holding a white answer card. The card shows the shopper's question, Cierto's grounded answer, a route strip, a promised / now-expected / latest-by row, and a sources line.
- Under the card: six cause tabs that cycle automatically and can be clicked.

FORM: a user-steered concept rendered as `.impeccable/mocks/decision/concept-answer.png`. It replaced roll e1e55334 (Calibrated) after the user steered toward "serious + calm, with rich motion, not kiddish".

Signature interaction: the answer card morphs between causes. The question types in, the answer streams, the route and ETA figures tween, and the mist drifts.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
