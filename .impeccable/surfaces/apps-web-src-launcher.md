---
version: 1
slug: "apps-web-src-launcher"
primary_target: "apps/web/src/launcher"
related_targets: ["apps/web/src/hosts","apps/web/src/widget"]
---

# Surface brief — demo launcher, host replicas and shopper widget

**Scope:** `apps/web` — the demo launcher (platform world), three host replicas (Smytten My Orders, Zomato tracking, Swish after-delivered) and the `<wismo-order>` widget inside them. Visitor mode: **Operate** (the shopper checks an order; the evaluator drives the demo).

**Audience and job:** a shopper checking one worried-about order on a phone; a hiring manager who must see within a minute that this upgrades screens real apps already have. Proof: every scenario cites a real complaint; host looks follow the real apps' store screenshots in `.impeccable/refs/`.

**Constraints:** host replicas copy each brand's visual identity with a persistent "Concept demo · not affiliated with <brand>" label and text wordmarks (no copied logo files); local or private demos only. WCAG 2.1 AA. Widget is a framework-free Web Component themed by tokens. Anti-goals from the owner: bolted-on look, chatbot-first, alarmist, legal jargon.

**Unresolved:** product name; urgent-medicine scenario (deferred).

## Direction contract

THESIS: The launcher is a quiet observatory around three real-looking phones; the only colour in the platform is a spectral hairline whose state is the delivery's proof. It refuses the category default of a dashboard of cards and metrics around a single tracking page.

OWN-WORLD: Platform: cloud-white field (#fbfcfd), slate ink (#2e3440), a light humanist sans (Source Sans 3), wide margins, no fills; colour lives only as a 1–2 px mint/rose/violet edge that is absent, forming, vivid or dispersed. Hosts: each brand's own palette, type and pill buttons (Smytten navy/blue/mint, Zomato red/green, Swish greens/yellow); the widget wears the host's tokens and never shows its own identity.

STORY: The evaluator sees three ordinary order screens, presses one trigger, watches all three admit that "delivered" is only the courier's claim, answers "No, I didn't get it" in one of them, and reads in the side feed what the engine noticed and who holds the problem.

FIRST VIEWPORT: Top line at left: "Where does the shopper check?" in light slate; the virtual clock at right. Three phones side by side, equal size, filling the width, each ringed by its proof edge. Under them a single horizontal beat track (Order placed · On the way · Courier marks delivered · …) with the primary action "Courier marks delivered, no OTP" as the one filled control. The engine feed sits as a narrow right-hand column in plain text.

FORM: Surface structures chosen in the shape round (`docs/01-design-brief.md`): the round-2 grounded list positions 7 (My Orders, told truthfully), 2 (one smart card in the tracking screen) and 4 (the screen after "Delivered") all adopted as demos by the owner, inside the iridescent-cloud-edge platform world the owner pinned. Seed key cefc1f0a (re-roll 1).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

Signature interaction: the proof edge. When the courier claims delivery the edge around that phone begins *forming* (a slow spectral shimmer travelling round the frame); a customer confirmation makes it *vivid* and still; a dispute makes it *disperse* (the band breaks into separated segments). Motion grammar: one authored moment per state change, exponential ease-out, nothing else animates.
