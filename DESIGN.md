---
name: Intelligent WISMO (working name)
description: Delivery truth for Indian D2C and quick commerce. The platform's own world is an iridescent cloud edge; the shopper widget wears each host's tokens.
colors:
  cloud-field: "#fbfcfd"
  slate-ink: "#2e3440"
  slate-ink-deep: "#1f242d"
  slate-soft: "#545e6d"
  hairline: "rgb(46 52 64 / .12)"
  paper-white: "#ffffff"
  proof-mint: "#2aa27a"
  proof-rose: "#d9577d"
  proof-violet: "#6f58e0"
  focus-violet: "#5b47c9"
typography:
  display:
    fontFamily: "'Source Sans 3', system-ui, sans-serif"
    fontSize: "clamp(30px, 2.6vw, 40px)"
    fontWeight: 300
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "tnum"
  headline:
    fontFamily: "'Source Sans 3', system-ui, sans-serif"
    fontSize: "clamp(26px, 2.2vw, 34px)"
    fontWeight: 300
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  lede:
    fontFamily: "'Source Sans 3', system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 300
    lineHeight: 1.45
  title:
    fontFamily: "'Source Sans 3', system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.25
  body:
    fontFamily: "'Source Sans 3', system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "'Source Sans 3', system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    fontFeature: "tnum"
  code:
    fontFamily: "ui-monospace, 'SF Mono', Consolas, monospace"
    fontSize: "0.92em"
rounded:
  focus: "6px"
  control: "12px"
  screen: "38px"
  device: "47px"
  edge: "54px"
  pill: "999px"
spacing:
  hair-gap: "4px"
  caption: "10px"
  row: "14px"
  stack: "18px"
  section: "22px"
  gutter: "48px"
components:
  button-trigger:
    backgroundColor: "{colors.slate-ink}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
    height: "56px"
  button-trigger-hover:
    backgroundColor: "{colors.slate-ink-deep}"
  beat-step:
    textColor: "{colors.slate-ink}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
    height: "56px"
  beat-step-reached:
    textColor: "{colors.slate-soft}"
  beat-step-current:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.slate-ink}"
  button-next:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.slate-ink}"
    rounded: "{rounded.pill}"
    padding: "0 20px"
    height: "48px"
  text-button:
    textColor: "{colors.slate-soft}"
    typography: "{typography.label}"
    padding: "6px 0"
  device-frame:
    backgroundColor: "{colors.paper-white}"
    rounded: "{rounded.device}"
    padding: "9px"
---

# Design System: Intelligent WISMO

This file records the **platform world**: the demo launcher as shipped, and the rules every future platform surface inherits (hosted tracking page, support console, ops dashboard). The `<wismo-order>` shopper widget is documented separately under Components as a token contract; it has no palette of its own. The Smytten, Zomato and Swish host replicas are third-party look-alikes kept as theme files and examples. They are never this project's identity.

## Overview

**Creative North Star: "The Iridescent Cloud Edge"**

A quiet observatory. The field is cloud-white, the type is slate and light, margins are wide, and nothing is filled. The one exception is the single primary control. Colour appears in one place only: a thin spectral edge around the thing being observed, and the edge's state is the delivery's proof. With no proof there is no colour. When the courier claims delivery, the colour starts forming. A confirmation makes it vivid and still, and a dispute breaks it apart.

The world is meant to be looked through, not at. Chrome recedes to hairlines so the observed content (the phones in the launcher, and later an order, a case or a lane) does the talking. Density is low in the stage and moderate in the side feed, which reads as a plain-text log and not as a card grid. The owner rejected the category default of a dashboard made of cards and metric tiles.

Motion follows the same restraint. Each state change gets one authored arrival on an exponential ease-out. The forming shimmer is the only loop. Hovers change colour or border, never position.

**Key Characteristics:**
- Cloud-white field, slate ink, a single light humanist sans (Source Sans 3 at 300/400/600).
- Chromatic colour exists only as the proof edge (mint, rose, violet) and the focus ring.
- Four edge states (absent, forming, vivid, dispersed), always paired with words.
- Hairline dividers, no card fills, one filled control per view.
- Times and counts set in tabular figures.

## Colors

The palette is achromatic slate on cloud white, with a three-stop spectral band kept for proof.

### Primary
- **Slate Ink** (`slate-ink`): all primary text and the one filled control (the primary trigger). **Slate Ink Deep** (`slate-ink-deep`) is its hover only.

### Tertiary (the proof spectrum)
- **Proof Mint** (`proof-mint`), **Proof Rose** (`proof-rose`), **Proof Violet** (`proof-violet`): the three stops of the proof edge. Each holds about 3:1 or better against the field so the band reads as a non-text graphic. They never colour text, fills or icons.
- **Focus Violet** (`focus-violet`): the keyboard focus ring (1.5px outline, 3px offset). This is the one sanctioned chromatic use outside the edge, and it is there for legibility.

### Neutral
- **Cloud Field** (`cloud-field`): the page field for every platform surface.
- **Paper White** (`paper-white`): the device bezel, the current timeline step and the secondary pill. These are the only raised whites on the field.
- **Slate Soft** (`slate-soft`): secondary text such as the lede, metadata, reached steps, the clock's day and source lines.
- **Hairline** (`hairline`, slate at 12%): every divider and resting border, and the proof edge in its absent state.

### Named Rules
**The Proof-Only Colour Rule.** Mint, rose and violet appear only in the proof edge. Text, fills, icons and charts stay achromatic. The focus ring is the one exception.

**The Words-With-Edge Rule.** Every edge state is also written out in the caption ("Not delivered yet", "Courier says delivered · unproven", "Delivery confirmed", "Customer disputes delivery"). The uncertain states (forming and dispersed) are set in 600 ink. The edge is `aria-hidden`, so the words carry the status.

## Typography

**Display / Body Font:** Source Sans 3 (fallback `system-ui, sans-serif`), self-hosted at 300, 400 and 600.
**Mono:** `ui-monospace, 'SF Mono', Consolas, monospace` at 0.92em, used only for engine rule identifiers.

**Character:** A light humanist sans set large and thin, which gives an observational, unhurried voice. Weight carries hierarchy and colour does not.

### Hierarchy
- **Display** (300, `clamp(30px, 2.6vw, 40px)`, 1, -0.03em, tabular): the virtual clock.
- **Headline** (300, `clamp(26px, 2.2vw, 34px)`, 1.1, -0.02em): the page question, e.g. "Where does the shopper check?".
- **Lede** (300, 16px, 1.45, slate soft, max 72ch): one or two sentences under the headline.
- **Title** (600, 15–16px, 1.25): caption titles, section heads, timeline step labels.
- **Body** (400, 15px, 1.4): feed messages.
- **Label** (400, 13–14px, slate soft, tabular): metadata, times, sources, text buttons.

### Named Rules
**The Light Voice Rule.** Large type is always 300 and emphasis is always 600. The platform never uses 700 or heavier.

**The Tabular Time Rule.** Every clock, timestamp and step time uses `font-variant-numeric: tabular-nums`, in IST and Indian English formatting.

## Layout

The page has a centred maximum width of 1680px with 48px side gutters and 22px vertical rhythm between blocks. The stage is a two-column grid: a fluid main column and a 300px sticky side column, with a 48px column gap. The main column stacks the observed objects over a single horizontal timeline, and the side column holds the plain-text feed.

Observed objects are sized from viewport height (`--phone-w: clamp(250px, calc((100vh - 372px) / 2.164 + 34px), 420px)`), so objects, captions and the timeline all fit in the first viewport. They sit in equal columns, spaced evenly.

Breakpoints:
- **≤1280px:** the side column drops below the stage and feed entries flow into `auto-fill, minmax(260px, 1fr)`.
- **≤860px:** 16px gutters, the header stacks, one object is shown per row (max 360px), and the timeline collapses to a sticky bottom bar. That bar shows only the current step and the next action, with a 94% field wash and an 8px backdrop blur.

## Elevation & Depth

The platform is flat. Depth comes from hairlines and from one real shadow.

### Shadow Vocabulary
- **Device lift** (`box-shadow: 0 1px 2px rgb(46 52 64 / .05), 0 40px 70px -40px rgb(46 52 64 / .35)`): used only on the observed object's frame, to seat a physical object on the field.
- **Proof fringe** (`filter: blur(7px); opacity: .55`): a blurred copy of the forming or vivid band behind the crisp band, which gives the iridescent halo. It is not drawn when the edge is absent or dispersed.

### Named Rules
**The Hairline Rule.** Dividers and resting borders are 1px `hairline`. Feed entries, the timeline and the header are separated by rules, not boxes.

## Shapes

Corners follow the objects they hold. The ring sits concentric around the device: edge 54px, then a 7px gap, the device bezel at 47px with 9px padding, and the screen at 38px. Interactive shapes use gentle 12px corners (timeline steps) or full pills (secondary action). The proof band is 3px wide in the forming, vivid and dispersed states, and 1px in the absent state.

## Components

### Proof Edge (signature)
A ring 7px outside the observed object, drawn as a masked border and re-mounted only when its state changes.
- **Absent:** 1px hairline. No colour.
- **Forming:** a 3px conic sweep (transparent, then mint, rose and violet, then transparent) travelling round the frame once every 3.6s, linear, with the blurred fringe behind it.
- **Vivid:** a 3px still conic band (mint, rose, violet, mint) from 200deg, with the fringe.
- **Dispersed:** a 3px repeating conic of rose and violet segments separated by gaps. No fringe.
- **Arrival:** on each state change the ring scales from .985 and fades up from .5 over .9s on `cubic-bezier(.16, 1, .3, 1)`. Under `prefers-reduced-motion` both the arrival and the travel animations are turned off.

### Buttons
- **Primary trigger:** the one filled control in view. Slate-ink fill, white label (600) over a tabular time at 75% white, 12px corners, 56px minimum height. Hover deepens the fill. Once its moment has been reached it reverts to a plain step.
- **Timeline step:** unfilled, with a transparent 1px border that turns hairline on hover. Reached steps drop to slate soft and 400 weight. The current step gets a white fill and a hairline border, and is marked `aria-current="step"`.
- **Secondary pill:** white, hairline border, 600 weight, 48px minimum height. Hover turns the border to ink, and disabled is shown at 50% opacity.
- **Text button:** unfilled, slate soft, 14px, with a hairline underline at a 4px offset. On hover the text and underline go to ink.
- **Transitions:** background and border colour only, .3s on the house ease.
- **Focus:** a 1.5px focus-violet outline at a 3px offset with 6px rounding, applied globally.

### Feed (side column)
A plain ordered list with no cards. Each entry has a 1px hairline top rule, 14px top padding and an 18px gap between entries. Each entry holds three lines: tabular meta (13px, slate soft), message (15px/1.4, ink) and rule identifier (mono, slate soft), followed by the problem's holder when there is one.

### Captions
A title in 600, then the proof words (slate soft, or 600 ink when uncertain), then the evidence source in 13px 300. Captions always sit directly under the observed object.

### Order Widget (`<wismo-order>`), a separate system
A framework-free Web Component in an open Shadow DOM. **It has no identity.** Every colour, the face and the radii come from host tokens, and the platform palette above never applies inside it.

**Token contract.** A host theme is a DTCG `*.tokens.json` file. Each `$value` is flattened to a `--w-<path>` custom property on `:host`, and a host may also set the same properties on the element from its own CSS. A theme must supply every key below:

| DTCG key | Custom property | Role |
|---|---|---|
| `font.body` | `--w-font-body` | the only face |
| `color.ink` | `--w-color-ink` | text, fact labels |
| `color.muted` | `--w-color-muted` | detail, holder, clock, absent-proof icons |
| `color.surface` | `--w-color-surface` | card and ask-panel fill, secondary button |
| `color.surface-2` | `--w-color-surface-2` | calm badge, reference strip, proof tiles |
| `color.line` | `--w-color-line` | card and secondary button borders |
| `color.action` / `color.action-ink` | `--w-color-action`, `--w-color-action-ink` | primary button fill and label, selection tint |
| `color.action-strong` | `--w-color-action-strong` | primary hover, link text |
| `color.ok` / `color.ok-soft` | `--w-color-ok`, `--w-color-ok-soft` | verified badge, present-proof icons |
| `color.check` / `color.check-soft` | `--w-color-check`, `--w-color-check-soft` | "Not confirmed" and running-late badges, urgent clock, warning facts |
| `color.alert` / `color.alert-soft` | `--w-color-alert`, `--w-color-alert-soft` | open issue and overdue refund badges |
| `color.focus` | `--w-color-focus` | 2px focus outline, 2px offset |
| `radius.surface` | `--w-radius-surface` | card and ask panel |
| `radius.control` | `--w-radius-control` | buttons |

Default: `apps/web/src/widget/themes/neutral.tokens.json`, a brand-free system-font skin used when a host passes no `theme`. Shipped host examples (look-alikes, not identity): `smytten.tokens.json`, `zomato.tokens.json`, `swish.tokens.json`.

**Variants** (set by the `variant` attribute):
- `orders-row`: sits inside the host's order card. Headline 15px, detail 13px, compact buttons. Proof facts appear only while delivery is claimed or disputed.
- `tracking-card`: one card in the host's stack. 16px padding, surface radius, line border, a soft card shadow, headline 17px, and question plus buttons at equal width.
- `after-delivered`: the main content of the host's post-delivery screen. Headline 22px, proof as a row of icon tiles, an ask panel with a 20px question and full-width 52px buttons.

**Fixed across hosts:** badge anatomy (pill, 6px current-colour dot, 12px/600), headline 700 at -0.01em, tabular figures, 1.75-stroke line icons that are `aria-hidden`, and the "settle" arrival (6px rise, .5s house ease) on headline and question only, and only when the state changes.

**Copy rules** (`copy.ts`): plain words with no internal jargon, calm when something is wrong, and never blaming the customer. A courier's delivery is written as a claim ("<courier> says it was delivered"), never as a green tick. Questions are yes/no in the shopper's words ("Did you get your parcel?" or "Did your food arrive?", answered by "Yes, I got it" / "No, I didn't", or the quick-commerce wording). Every open problem names who has to act. Deadlines are written as a date or a countdown. Superseded promises stay visible, struck through. "Talk to a person" is always offered when the engine allows it.

**Accessibility rules:** status is always words first and tone second, and badges always carry text. The headline is `aria-live="polite"`. Each root is `role="group"` with an `aria-label` of brand plus order reference. Icons are `aria-hidden`. Buttons have a 44px minimum height (52px in after-delivered). Reduced motion turns off the settle animation and button transitions. Themes must give AA contrast for ink, muted, and each tone on its soft fill.

## Do's and Don'ts

### Do:
- **Do** keep chromatic colour inside the proof edge. The focus ring is the one exception.
- **Do** pair every edge state with its written status in the caption.
- **Do** allow one filled control per view (slate ink, 12px corners) and keep everything else unfilled or hairline.
- **Do** set large type at 300 and emphasis at 600 in Source Sans 3, with tabular figures for every time.
- **Do** give each state change one arrival on `cubic-bezier(.16, 1, .3, 1)`, and honour `prefers-reduced-motion`.
- **Do** theme the widget only through the `--w-*` contract, so each host gets a new token file and never a fork.

### Don't:
- **Don't** colour text, icons, fills or data with mint, rose or violet.
- **Don't** build platform surfaces as dashboards of cards and metric tiles. Use hairline-separated lists and plain text.
- **Don't** add shadows beyond the device lift, and don't box feed or list entries.
- **Don't** give the widget its own colours, face or radii, or let the platform palette leak into it.
- **Don't** treat a host replica's palette (Smytten, Zomato or Swish) as this project's identity.
