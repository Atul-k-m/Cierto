# SDK design research: embeddable customer-facing SDKs, and a proposed AI WISMO SDK

*Research notes, 2026-09-30. Sources are cited inline; "(inferred)" marks my own reasoning rather than a documented fact. Secondary sources (vendor blogs, third-party guides) are flagged where a claim rests on one.*

---

## Part A. What the reference SDKs do

### A1. Summary matrix

| SDK | Install surfaces | Client credential | End-user identity | Theming model | Headless option | Server side |
|---|---|---|---|---|---|---|
| **Intercom Messenger** | Script tag, npm `@intercom/messenger-js-sdk`, Android (Gradle `io.intercom.android:intercom-sdk`), iOS (SPM `intercom-ios-sp`, CocoaPods), RN `@intercom/intercom-react-native`, Flutter `intercom_flutter` (community-maintained plugin) | `app_id` (web); mobile-specific API key + app id | **JWT** signed with the Messenger API secret (`intercom_user_jwt`, HS256, `user_id` required, `exp` recommended); HMAC `user_hash` is legacy | A few settings (`action_color`, `background_color`, `theme_mode`, `alignment`, paddings); most styling in the admin UI | Hide the launcher plus `custom_launcher_selector`; JS API (`show`, `update`, `shutdown`, `trackEvent`) | Fin **Data connectors** (Fin calls your API); JWT required before connectors go live; HITL approvals in Procedures |
| **Zendesk messaging** | Web Widget snippet (key), Android `com.zendesk:zendesk-messaging`, iOS, Unity, RN | Channel key | JWT: header `alg HS256` + `kid`; payload `scope:"user"`, `external_id`, optional `email`, `email_verified`, `name`, `exp`; `zE('messenger','loginUser', cb)` | Admin-configured colours; conversation fields and tags from the API | Sunshine Conversations API | Webhooks; triggers |
| **Freshchat** | Web `fcWidget`, Android, iOS, RN, Flutter | `token` + `host` (a regional host) | JWT (`freshchat_uuid` required); for logged-out users, sign the UUID on your backend and call `fcWidget.authenticate(signedUUID)` | `config` object: `headerProperty` (fonts, colours), `cssNames`, `hideChatButton`, `appLogo` | JS API: `open`, `close`, `user.setProperties`, `track`, events `widget:opened`, `unreadCount:notify` | `restoreId` for cross-device continuity |
| **Stripe Elements / Payment Element** | `js.stripe.com` script, `@stripe/stripe-js`, `@stripe/react-stripe-js`, iOS SPM `stripe-ios-spm`, Android, RN `@stripe/stripe-react-native` | **Publishable key** `pk_test_/pk_live_`; server uses secret `sk_` or restricted `rk_` keys | Server creates the object (PaymentIntent or AccountSession) and hands the client a **client_secret** | **Appearance API**: `theme` + `variables` + `rules` + `labels`/`inputs` + `disableAnimations` | PaymentSheet or Elements vs raw Stripe.js / API; Connect embedded components are **custom elements** | Webhooks (`Stripe-Signature` t/v1), `Idempotency-Key`, CLI `listen`/`trigger`, sandboxes |
| **Razorpay Checkout** | `checkout.js`, Android, iOS, RN `react-native-razorpay`, Flutter `razorpay_flutter` | `key_id` (public) and `key_secret` (server) | Server creates an Order; client opens Checkout with `order_id`; server verifies `HMAC_SHA256(order_id|payment_id, key_secret)` | `theme.color`, `image`, `name`, `prefill` | Custom Checkout SDK | Webhooks with `X-Razorpay-Signature`; `x-razorpay-event-id` for dedupe; out-of-order delivery warned |
| **AfterShip Tracking** | Order-lookup widget (JS snippet), branded tracking page (hosted, custom domain, **iframe embed**), EDD widget, REST API | `as-api-key` (server) | Order number + email lookup, or tracking number | Page editor, merge tags; widget button colours and size | Tracking API for headless storefronts | Webhook `tracking_update` with full checkpoints; `aftership-hmac-sha256`; 14 attempts on a `2^n × 30s` backoff |
| **Narvar** | Hosted tracking pages, Notify, Order and Shipment APIs, helpdesk apps (Zendesk, Gladly, Salesforce, Kustomer) | Client ID and secret (server) | n/a (hosted pages) | Hosted page branding | APIs | Order API (order, items, shipments, customer, billing), Shipment API, Returns API |
| **Gorgias Chat** | Snippet (v3 loads `/bundle-loader/:appKey`), Shopify app | Alphanumeric app key (replaced guessable numeric IDs) | Shopify customer session; Order Management portal uses an email/SMS OTP | Admin UI; `updateTexts`, `setPosition` | `GorgiasChat` JS API (`init()` promise, `open`, `sendMessage`, `captureUserEmail`, `hideOutsideBusinessHours`) | AI Agent Actions (track, cancel, edit address, refund) against Shopify and 3PLs |
| **Sendbird UIKit** | Android Gradle `com.sendbird.sdk:uikit`, iOS SPM/CocoaPods, React, RN, Flutter | `appId` | Session tokens issued by your server | `colorSet`, `stringSet`, BEM CSS, `renderMessage`; light and dark themes | Chat SDK (headless) under UIKit v3's modular components | Platform API and webhooks; region choice including **Mumbai** |
| **Stream Chat** | React, RN, Android, iOS, Flutter | API key (public) | JWT from the server with the API secret, via a **token provider** (refreshed on expiry); dev tokens for prototyping | CSS variables in layers (global, component), `str-chat__theme-dark`, `@layer stream-overrides` | Hooks plus a low-level client; `WithComponents` overrides | Webhooks |
| **Google Maps Mobility (Fleet Engine + Consumer SDK)** | Consumer SDK for Android, iOS and JS; Driver and Navigation SDKs | Maps API key | **Auth token fetcher**: your server mints a JWT scoped to one `tripid`/`trackingid`, lifetime of 1 hour or less, refreshed by the SDK a minute before expiry | Map styling, polyline and marker customisation | Raw Fleet Engine APIs | Fleet Engine as the backend of record for vehicles and tasks |
| **Mapbox** | GL JS (npm `mapbox-gl`), Navigation SDK v3 for Android and iOS | Public `pk.` token (optionally **URL-restricted**); secret `sk.` token with `Downloads:Read` only for SDK download | n/a | Style spec | Everything is an API | Directions, Map Matching |

### A2. Install surfaces: patterns worth copying

- **Offer both a script tag and npm.** Intercom, Stripe and Stripe Connect.js all ship a CDN loader (`<script src=".../v1/connect.js" async>` that calls a global `onLoad`) and an npm wrapper that lazy-loads the same CDN bundle, so the runtime stays evergreen and server-controlled. https://docs.stripe.com/connect/get-started-connect-embedded-components.md?platform=web
- **Web Components as the framework-neutral primitive.** Stripe Connect's `create('payments')` "returns a custom element that Connect.js registers"; React wrappers (`ConnectComponentsProvider`, `ConnectPayments`) are thin shells over it. The same source.
- **Mobile is native, not WebView,** wherever it matters. Stripe says embedded components "can't be used in embedded web views"; use the iOS, Android or RN SDKs. Intercom, Zendesk and Sendbird all ship native UIKits. RN packages are usually **bridges over the native SDKs** (Intercom RN "bridges iOS and Android SDKs"; Razorpay RN "acts as a wrapper around the Razorpay Standard SDK"). https://github.com/intercom/intercom-react-native, https://razorpay.com/docs/payments/payment-gateway/react-native-integration/standard/
- **iOS: SPM first, CocoaPods second.** Stripe uses `stripe-ios-spm`, Intercom `intercom-ios-sp`, and Sendbird `sendbird-uikit-ios-spm`. The pattern is a separate lightweight SPM mirror repo. https://github.com/intercom/intercom-ios-sp, https://sendbird.com/docs/chat/uikit/v3/ios-uikit/essentials/installation
- **Android: initialise in `Application.onCreate()`.** Intercom warns that "initializing anywhere else will result in Intercom not behaving as expected". Ship a `-base` artifact without push (`intercom-sdk-base`) so apps that don't want FCM coupling can opt out. https://developers.intercom.com/installing-intercom/android/installation
- **Flutter is often community-maintained** (`intercom_flutter`); Razorpay and Sendbird ship first-party plugins. https://pub.dev/packages/intercom_flutter, https://pub.dev/packages/razorpay_flutter

### A3. Init and config API shape

**Keys.** Stripe has the canonical taxonomy. The **publishable** key "can identify your account… can't perform sensitive operations… You can include it in front-end code". **Restricted** keys have scoped permissions, and Stripe now recommends them over **secret** keys for new use. Test and live keys are prefixed (`pk_test_`, `rk_live_`). Webhook signing secrets (`whsec_`) are a separate class. New in 2026: **agent-tagged restricted keys** "are automatically subject to approval rules, which require a designated reviewer to approve sensitive actions", covering refunds and payouts. That is a direct precedent for an AI WISMO agent's money actions. https://docs.stripe.com/keys

**Identity verification.** There are three patterns, in increasing strength and flexibility:
1. **HMAC of the user id** (Intercom `user_hash`, now legacy). It is static, never expires, and carries no claims. https://developers.intercom.com/installing-intercom/web/identity-verification
2. **Host-signed JWT** (Intercom `intercom_user_jwt`; Zendesk with `kid` and `scope:"user"`; Freshchat). The host backend signs with a shared secret, the SDK passes the JWT, and the vendor verifies it. Intercom advises a short `exp` ("minimum of 5 minutes" if pages reload often). Intercom Fin data connectors **require** JWT auth before going live. https://support.zendesk.com/hc/en-us/articles/4411666638746, https://www.intercom.com/help/en/articles/10589769-authenticating-users-in-the-messenger-with-json-web-tokens-jwts, https://www.intercom.com/help/en/articles/9916507-fin-data-connector-faqs
3. **Server-created session plus `client_secret`, fetched through a callback** (Stripe AccountSession `fetchClientSecret`; Stream "token provider"; Google Consumer SDK `authTokenFetcher`). The SDK calls the host's endpoint again whenever the credential expires. Stripe: "`fetchClientSecret` should always create a new account session". The session carries **component and feature permissions enforced server side**: "you can enable refund management only for administrators… you must map your site's user role to account session components." Google: tokens are scoped to one `tripid`/`trackingid`, and "the request fails if the timestamp is more than one hour in the future". https://docs.stripe.com/connect/get-started-connect-embedded-components.md?platform=web, https://getstream.io/chat/docs/react/tokens_and_authentication/, https://developers.google.com/maps/documentation/mobility/journey-sharing/on-demand/javascript/setup, https://developers.google.com/maps/documentation/mobility/fleet-engine/essentials/set-up-fleet/jwt

→ **For WISMO, pattern 3 is the right default:** the scope is an order or a customer, the features are per session, it refreshes, and the host needs no crypto code. Pattern 2 is the zero-round-trip alternative.

**Logout and shared devices.** Intercom `shutdown` clears cookies "to prevent conversation history leakage on shared devices". Stripe `logout()` destroys the session but must *not* be called on unmount. Freshchat `user.clear()`. https://developers.intercom.com/installing-intercom/web/installation

**Locale.** Stripe Connect takes `locale` (BCP 47 with fallback, e.g. `fr-be`→`fr-fr`) and includes `en-IN`. Freshchat takes `locale`, Intercom `language_override`, Zendesk admin locale. **None of them lists Hindi or Hinglish** in the lists I saw. That gap is an opportunity. https://docs.stripe.com/connect/get-started-connect-embedded-components.md?platform=web

**Copy overrides.** Sendbird has `stringSet`, Gorgias `updateTexts({})`, Freshchat `config.headerProperty`/`appName`. https://docs.gorgias.com/en-US/customize-the-chat-widget-with-HTML-and-JavaScript-286032

**Runtime update.** Stripe `stripeConnectInstance.update({appearance, locale, displayOptions})` accepts only a subset of options at runtime. Intercom `update`.

**Events out of the widget.** Freshchat has `widget:opened`, `user:created`, `unreadCount:notify`. Stripe components have `setOnLoadError` (typed errors: `api_connection_error`, `authentication_error`, `rate_limit_error`, `render_error`…) and `setOnLoaderStart`, and warn that "logic triggered by a load error handler must be idempotent". https://developers.freshchat.com/web-sdk/

**Custom UI slots.** Intercom and Freshchat support `hide_default_launcher`/`hideChatButton` plus a custom launcher selector. Sendbird has `renderMessage`, Stream `WithComponents`/`ComponentContext`. Stripe does **not** allow slots inside Elements; its only hooks are appearance and events. That is deliberate, for PCI.

### A4. Theming: Stripe Appearance API as the model

Source: https://docs.stripe.com/elements/appearance-api.md?api-integration=paymentintents
- **Three tiers:** `theme` (`stripe`, `night`, `flat`) → `variables` → `rules`. The guidance is to "pick a theme… customise using inputs and labels… set variables… If needed, fine-tune individual components and states using rules."
- **Variables** (commonly used): `fontFamily`, `fontSizeBase` ("at least 16px for input fields on mobile"), `spacingUnit` ("base spacing unit that all other spacing is derived from"), `borderRadius`, `colorPrimary`, `colorBackground`, `colorText`, `colorDanger`, and also `colorSuccess`, `colorWarning`. Derived variables include `accessibleColorOnColorPrimary`, `fontSizeSm/Lg/Xl` scaled in rem, and `buttonColorBackground` (defaults to `colorPrimary`). Colour variables "don't support `rgba()` or `var(--myVariable)`" because Stripe computes derived shades from them.
- **Rules:** CSS-like objects keyed by **public class names only**, with documented states, pseudo-classes and pseudo-elements, for example `.Tab--selected`, `.Input:focus`, `.Input--invalid`, `.Input::placeholder`. "Ancestor-descendant relationships in selectors are unsupported." Each class has a whitelist of supported CSS properties. This keeps the internal DOM private, so Stripe can refactor without breaking merchants.
- **Layout options:** `inputs: 'spaced'|'condensed'`, `labels: 'auto'|'above'|'floating'`, and `disableAnimations`.
- **Connect embedded components** "inherit font family and background colour from the parent container" and take a `fonts` array (`cssSrc` or `{family, src, weight}`). The CSP must allow the font CSS URL. https://docs.stripe.com/connect/get-started-connect-embedded-components.md?platform=web
- **The Stream alternative** is plain CSS custom properties in `@layer stream`/`stream-overrides`: "Prefer CSS variables over selector overrides to keep upgrades painless." https://getstream.io/chat/docs/sdk/react/theming/themingv2/
- **Mobile parity:** Stripe RN passes the same `appearance.variables` (`colorPrimary`) through `loadConnectAndInitialize`, and custom fonts need a `CustomFontSource`. Sendbird uses `UIKitTheme`/`colorSet`. https://docs.stripe.com/connect/get-started-connect-embedded-components.md?platform=react-native

### A5. Server side: webhooks, idempotency, signatures, ordering

**Outbound signing (vendor → host):**
- **Stripe:** `Stripe-Signature: t=<ts>,v1=<hex>`, where the signed payload is `timestamp + "." + raw_body`, HMAC-SHA256 with `whsec_`. Libraries default to a **5-minute tolerance**, and Stripe says "Don't use a tolerance value of 0". Compare in constant time and ignore non-`v1` schemes to prevent downgrade attacks. On secret rotation, both secrets sign for up to 24 hours. There is also an IP allowlist. The raw body must not be re-serialised. https://docs.stripe.com/webhooks
- **Standard Webhooks** (the open spec, used by OpenAI, Anthropic, Twilio, Supabase per the Standard Webhooks and Svix material): headers `webhook-id`, `webhook-timestamp`, `webhook-signature: v1,<base64>` (space-separated for rotation); signed content `msg_id.timestamp.payload`; secret `whsec_<base64>`. https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md
- **AfterShip:** `aftership-hmac-sha256` is a base64 HMAC of the body with no timestamp, so it has no replay protection. The single event type is `tracking_update` with the full tracking object and checkpoints. Enums "are not restrictive and may be extended", so consumers must tolerate unknown values. Delivery is up to 14 attempts on a `2^n×30s` backoff (about 136 hours) and then **discarded**. https://hookdeck.com/webhooks/platforms/guide-to-aftership-webhooks-features-and-best-practices (secondary; the official aftership.com docs returned 403)
- **Razorpay:** `X-Razorpay-Signature` is an HMAC-SHA256 of the raw body. `x-razorpay-event-id` is unique per event and is used to dedupe. Delivery order is not guaranteed. When rotating secrets, "use the old secret… while retrying older requests". https://razorpay.com/docs/webhooks/validate-test/
- **Shiprocket (India 3PL aggregator):** there is **no HMAC**, only an optional static `x-api-key` "security token" header. The payload carries `awb`, `courier_name`, `current_status`, `current_status_id`, `shipment_status_id` and `current_timestamp`, and "should send only code 200 in response". NDR API: `GET /v1/external/ndr/all`. https://apidocs.shiprocket.in/ (via the search summary). **Implication (inferred):** Indian carrier feeds are weakly authenticated. The WISMO ingestion layer must treat them as claims, use unguessable per-connector URLs, and re-fetch from the carrier API before acting on money-moving signals.

**Delivery semantics (all vendors converge):**
- **At-least-once delivery.** Dedupe by event id (Stripe: "logging the event IDs you've processed"; also, two distinct events can describe the same change, so dedupe on `data.object.id + type`).
- **No ordering guarantee.** Stripe: "Don't use `created` to determine event order". Fetch the latest object or carry a version.
- **Return 2xx fast and process on a queue.**
- **Retries:** Stripe retries for up to 3 days in live mode and 3 times over a few hours in a sandbox. Manual resend from the dashboard works for 15 days, from the CLI for 30.
- **Thin vs snapshot events:** Stripe v2 thin events carry only a reference, and you call `fetchRelatedObject()`. That avoids stale-payload bugs.

**Inbound idempotency (host → vendor):** Stripe's `Idempotency-Key` header (≤255 chars, V4 UUID suggested, "avoid using sensitive data"). The key stores "the resulting status code and body of the first request… including 500 errors", compares the parameters and errors on a mismatch, and can be pruned after 24 hours. It applies to all POSTs; GET and DELETE are idempotent by definition. https://docs.stripe.com/api/idempotent_requests

**Order and shipment ingestion shapes:**
- **Narvar Order API:** one order document with `order_info`, `order_items`, `shipments[]` (carrier, tracking number), `customer`, `billing` and promotions; the OMS re-sends it as fulfilment progresses. Auth is client ID and secret. https://docs.celigo.com/hc/en-us/articles/7581451681179-Available-Narvar-APIs, https://docs.oracle.com/cd/F21615_01/oroms/pdf/195/cws_help/master/Narvar_Integration/Narvar_Integration.htm, https://github.com/api-evangelist/narvar
- **AfterShip:** create a tracking from `tracking_number` plus `slug`, which it can auto-detect. It then polls and pushes updates. Normalised tags: `Pending`, `InfoReceived`, `InTransit`, `OutForDelivery`, `AttemptFail`, `Delivered`, `AvailableForPickup`, `Exception`, `Expired`, with sub-tags such as `InTransit_002`.
- **Carrier connectors in India:** **ClickPost** covers 600+ carriers (Blue Dart, Delhivery, DTDC, India Post…) and uses "both tracking webhook and APIs… its API proactively nudges the system at regular intervals when an update is delayed". That hybrid of push plus poll-on-silence is the right model. https://www.clickpost.ai/carrier-integration. **Shiprocket** is an aggregator with a webhook plus a pull API.

**AI agent actions against the host (the closest precedents to WISMO):**
- **Intercom Fin Data connectors:** each connector is "an API call that you configure, and Fin automatically determines when to use it". Read-only connectors such as "Check order status" can be direct-triggered. Tokens are sent as headers. "A Condition step should be added after every Data Connector call to handle errors and empty responses." **Human-in-the-loop approvals** apply to "refund or exception approvals… goodwill gestures". Built-in escalation fires on an explicit request for a human, "strong frustration", or "a repetitive loop". https://www.intercom.com/help/en/articles/9916183-best-practices-when-using-data-connectors-with-fin, https://www.intercom.com/help/en/articles/14468561-human-in-the-loop-approvals-for-fin-procedures, https://www.intercom.com/help/en/articles/12396892-manage-fin-ai-agent-s-escalation-guidance-and-rules (details via the search summary)
- **Gorgias AI Agent:** WISMO is "the most common job": it "pulls the live order and tracking from Shopify (and from 3PLs…)… If it cannot answer with confidence, it hands the ticket to a human". Actions cover cancel, address edit and refunds. https://www.eesel.ai/blog/gorgias-shopify (secondary)
- **Narvar:** IRIS claims "60% less WISMO contacts with proactive delivery updates"; Assist does claims and Shield does returns; integrates with Zendesk, Salesforce, Gladly and Kustomer. https://corp.narvar.com/solutions/customer-care. A Narvar agentic assistant ("NAVI", January 2026) is reported only by a third-party blog (https://alhena.ai/blog/agentic-commerce-narvar-reduce-support-costs/) and is **unverified**.

### A6. Headless vs pre-built

| Vendor | Pre-built | Headless | Middle layer |
|---|---|---|---|
| Stripe | Payment Element, PaymentSheet, Checkout | Stripe.js API | Appearance rules (no slots) |
| Sendbird | UIKit v3 ("rearchitected with more granular, modularized components" after customers asked for flexibility) | Chat SDK | `renderMessage`, `stringSet` https://sendbird.com/blog/introducing-swift-kotlin-typescript-flutter-chat-sdk-uikit |
| Stream | Components | Hooks + low-level client | `WithComponents` overrides; CSS variables |
| Google Mobility | `JourneySharingMapView` | Fleet Engine REST | Marker and polyline customisation |
| AfterShip | Hosted page (iframe) | Tracking API | Merge tags |
| Intercom / Zendesk / Freshchat / Gorgias | Messenger | REST and JS APIs; custom launcher | Very limited styling |

**Lesson (inferred):** the winners ship **three layers**: (1) a drop-in component, (2) the same component with overridable sub-parts or slots, and (3) a typed headless client whose **data model is already display-ready**, so custom UIs don't re-implement business logic. Sendbird's v3 rewrite shows that starting with only layer 1 forces a painful redo.

### A7. Security

- **CSP.** Vendors publish exact directives. Stripe.js needs `connect-src https://api.stripe.com`, `frame-src https://*.js.stripe.com https://js.stripe.com https://hooks.stripe.com` and `script-src https://*.js.stripe.com https://js.stripe.com`. Connect embedded components add `style-src 'sha256-…'` (the hash of an empty style element). Trusted Types need a policy example. Cross-origin isolation is **not supported**. https://docs.stripe.com/security/guide
- **Why iframes:** Stripe's iframes keep card data off the merchant page to reduce PCI scope ("securely collect and transmit payment information directly to Stripe without it passing through your servers"). **WISMO has no equivalent regulatory reason.** The host already owns the order data, so Shadow DOM custom elements are acceptable and cheaper (inferred). The exception is the chat transcript, which may hold PII the host shouldn't log; keep it in the SDK's own network layer, not in host analytics.
- **Guessable identifiers.** Gorgias v3 replaced numeric app IDs with alphanumeric keys to make the loader "more resistant to unauthorized access attempts". https://updates.gorgias.com/publications/security-improvements-chat-installation-snippet-v3
- **Publishable key restrictions.** Mapbox URL-restricted tokens return a 403 from other origins. Stripe applies access policies (IP, ASN, country) to server keys. https://docs.mapbox.com/accounts/guides/tokens/, https://docs.stripe.com/keys
- **Least-privilege tokens per object:** Fleet Engine consumer JWTs scoped to one trip. https://developers.google.com/maps/documentation/mobility/fleet-engine/essentials/set-up-fleet/jwt
- **Data residency.** Intercom offers US, EU and AU `api_base` endpoints, with **no India** option. https://developers.intercom.com/installing-intercom/web/installation. Zendesk offers US, EEA, AU and JP, **not India**. https://support.zendesk.com/hc/en-us/articles/4408838409754. Freshworks offers **India** among US, EU, AU and MEA. https://www.eesel.ai/blog/freshdesk-data-residency (secondary). Sendbird offers **Mumbai**. https://sendbird.com/blog/announcing-8-global-data-centers. India hosting is a real differentiator against the US-first incumbents.
- **India DPDP (Act 2023 + Rules notified 13/14 Nov 2025):**
  - **Phasing:** the Board rules apply from Nov 2025, consent-manager registration from Nov 2026, and **substantive obligations from 14 May 2027** (notice, security, breach reporting, rights).
  - **Security safeguards:** "encryption, masking, obfuscation… access controls". Logs and traffic data are kept **at least one year**.
  - **Breach reporting:** notify affected principals "without delay"; report to the Board **within 72 hours**.
  - **Processors:** processor contracts must require equivalent safeguards.
  - **Rights requests:** answered within 90 days.
  - **Erasure:** large platforms must give 48 hours' notice before auto-erasing inactive users' data.
  - **Cross-border:** transfers are allowed unless a country is restricted by notification.
  - Sources: https://www.scrut.io/post/dpdp-rules, https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf, https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Rules,_2025
  - **For WISMO:** the host (Smytten or Zomato) is the **Data Fiduciary** and WISMO the **Data Processor**. WISMO needs a DPA, masking, an erasure API, a one-year audit log and a breach runbook with a 72-hour path.

### A8. Docs: structure and what makes them good

- **Stripe as the benchmark:**
  - Three-column layout (nav, prose, runnable code).
  - **Test keys auto-injected into samples** for logged-in users.
  - Hover-highlight that links prose to code lines.
  - An API reference generated from OpenAPI "so they cannot drift".
  - Dated version header (`Stripe-Version`).
  - Test mode with fixtures (test cards).
  - CLI `stripe listen --forward-to localhost` and `stripe trigger <event>`.
  - Interactive quickstarts with downloadable samples.
  - Markdoc with custom tags and build-time validation.
  - Agent-readable docs ("Read this page in your terminal… `stripe docs`", `.md` variants of every page, agent skills).
  - Sources: https://www.moesif.com/blog/best-practices/api-product-management/the-stripe-developer-experience-and-docs-teardown/, https://www.mintlify.com/blog/stripe-docs, https://stripe.dev/blog/markdoc, https://docs.stripe.com/webhooks
- **Pages that answer "what can go wrong":** Stripe's webhook page has a status-code troubleshooting table (302 counted as a failure, TLS errors, timeouts) and a "Don't manipulate the raw body" callout. Stripe components log console warnings for common integration mistakes.
- **Razorpay:** the go-live checklist is explicit ("Replace test API keys with Live Mode credentials… Set up webhooks"). The docs warn that skipping signature verification "is the leading cause of fraudulent transactions". https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/integration-steps/
- **Stream:** dev tokens let people prototype before auth is wired. https://getstream.io/chat/docs/react/tokens_and_authentication/
- **A skeleton that works everywhere:** Quickstart (≤5 min, one page, copy-paste) → Guides by use case and platform → Reference (API, SDK, webhooks, errors) → Testing (sandbox, fixtures, CLI) → Go-live checklist → Changelog and upgrade guides.

---

## Part B. Proposed design: the AI WISMO SDK

Design stance, carried from the product brief (`docs/00-product-brief.md`) and the engine (`engine/src/wismo/`): the SDK renders **delivery truth**, not courier status. A "Delivered" scan is a *claim* until proof. The AI agent **proposes** money moves inside host-set policy, **humans approve above the threshold**, and a case can't close while an exception is live. The SDK must make those guarantees hard to break, even by a careless integrator.

### B1. Principles (each traced to Part A)

1. **Server-minted sessions, not client config, carry authority** (Stripe AccountSession, Fleet Engine consumer JWT). The browser can never raise a refund threshold or unlock a feature.
2. **Policies live server side, versioned and simulated.** Client config covers presentation plus a subset of features that the session allows.
3. **Three layers:** a drop-in element, slots and parts, and a headless client with a display-ready **view model** (the engine's `view.py` already produces `state`, `tone`, reasons, proof, clocks and actions).
4. **Appearance follows Stripe's model** (theme → variables → rules over public part names). Parts are exposed as CSS `::part()` and custom properties, so it is native CSS on the web.
5. **Events in are claims with provenance** (`asserted_by`). Ingestion is idempotent and order-tolerant. Weakly authenticated feeds (Shiprocket) are re-verified before money moves.
6. **Webhooks out follow Standard Webhooks.** Carry an `order_version` so consumers can drop stale updates; provide a thin-event option.
7. **India first:** Mumbai region, DPDP processor posture, Hindi (`hi-IN`) and Hinglish (`hi-Latn-IN`), rupee amounts, pincodes, COD, NDR, RTO vocabulary.

### B2. Package list

| Package | Surface | Contents |
|---|---|---|
| `https://js.wismo.dev/v1/wismo.js` | Script tag (CDN, evergreen v1; versioned URLs with SRI for pinning) | Loader; registers `<wismo-tracker>`, `<wismo-assistant>`, `<wismo-launcher>`, `<wismo-order-list>`; global `Wismo` |
| `@wismo/js` | npm (ESM, typed) | `loadWismo()` that lazy-loads the CDN runtime, like `@stripe/stripe-js` |
| `@wismo/react` | npm | `<WismoProvider>`, `<OrderTracker>`, `<Assistant>`, `<Launcher>`, hooks `useOrder`, `useConversation`, `useWismo` |
| `@wismo/headless` | npm (no DOM) | Typed client: sessions, `orders.get/subscribe`, `assistant.*`, `actions.*`; SSE and WebSocket transport; used internally by `wismo.js` and RN |
| `@wismo/react-native` | npm (native views via a bridge; no WebView for the tracker) | `WismoProvider`, `<OrderTracker>`, `<AssistantSheet>`, hooks; wraps the Android and iOS SDKs |
| `dev.wismo:wismo-android` / `wismo-android-core` | Gradle (Maven Central) | Compose + View UI / headless core; `-core` has no FCM dependency (Intercom `-base` pattern) |
| `WismoKit` / `WismoCore` | iOS SPM (`github.com/wismo/wismo-ios-spm`), CocoaPods | SwiftUI + UIKit UI / headless core |
| `wismo_flutter` | pub.dev (first-party) | Platform-channel wrapper over the native SDKs |
| `wismo` (Node), `wismo` (Python), `wismo-java` | Server SDKs | `customerSessions.create`, `events.ingest`, `webhooks.verify`, `remedies.approve`, typed models |
| `@wismo/cli` | npm global / Homebrew | `wismo login`, `wismo listen --forward-to`, `wismo trigger <scenario>`, `wismo replay`, `wismo policies simulate` |
| Connectors (hosted, no host code) | Dashboard toggles | Shopify, WooCommerce, Unicommerce (OMS); Shiprocket, Delhivery, Blue Dart, ClickPost, AfterShip (carriers); Razorpay, Cashfree, Juspay (refund status); Zendesk, Freshdesk, Gorgias (helpdesk handoff); WhatsApp BSP |
| `@wismo/mcp` | MCP server | Read-only order-truth tools for internal AI assistants and ops |

### B3. Keys and credentials

| Prefix | Where | Can do |
|---|---|---|
| `pk_test_…` / `pk_live_…` | Client | Identify tenant and environment; load the runtime; nothing else. **Origin allowlist** (web) and **package or bundle ID allowlist** (mobile), like Mapbox URL restrictions |
| `sk_test_…` / `sk_live_…` | Host server | Everything; discouraged for new integrations |
| `rk_…` | Host server or integration | Scoped: e.g. `events:write` only (for the OMS job), `sessions:create` only (for the BFF), `remedies:approve` (for the support tool). **Agent keys** (`rk_agent_…`) always pass the approval policy, following Stripe's agent-tagged RAKs |
| `cs_…` (client secret) | Client, from the host server | One customer session: scoped to a customer and optionally to specific `order_refs`; 15-minute TTL, refreshed through `fetchClientSecret`; carries enabled `features` |
| `tlk_…` (tracking link token) | SMS, WhatsApp, email links | One order, read plus confirm/dispute; 30-day TTL; no chat history; no PII beyond masked fields |
| `whsec_…` | Host server | Verify outbound webhooks (Standard Webhooks) |

### B4. Server: creating a customer session (host backend)

```http
POST https://api.wismo.dev/v1/customer_sessions
Authorization: Bearer rk_live_sessions_…
Idempotency-Key: 5f0c…            # optional
Wismo-Version: 2026-09-30

{
  "customer_ref": "cust_88213",               // host's stable id; no email or phone needed
  "order_refs": ["SMY-2025-771203"],          // optional: restrict to these orders
  "locale": "hi-Latn-IN",
  "features": {
    "tracker":   { "enabled": true },
    "assistant": { "enabled": true, "handoff": true, "attachments": true },
    "self_serve_actions": ["confirm_receipt", "dispute_delivery", "update_phone", "request_reattempt"],
    "remedy_requests": true                   // customer can ask; policy decides
  },
  "customer_context": {                       // optional, minimised; masked server-side
    "tier": "gold", "phone_last4": "4471", "pincode": "560034"
  }
}
→ 200 { "client_secret": "cs_live_…", "expires_at": "2026-09-30T10:15:00Z" }
```

**Alternative (zero round trip):** the host signs its own JWT with `whsec`-style tenant secret `jst_…`. The header is `{alg:"HS256", kid:"jst_2026a"}` and the claims are `{sub:"cust_88213", tid:"smytten", scope:"customer", orders:[…], exp:+≤60min}` (Zendesk and Intercom pattern). Features then fall back to the tenant defaults.

**Guests:** `<wismo-tracker lookup>` does order number + phone and then OTP (Gorgias order portal pattern), or uses a `tlk_` link.

### B5. Client init snippets

**Web, script tag (Smytten web order-detail page):**
```html
<script src="https://js.wismo.dev/v1/wismo.js" async></script>
<wismo-tracker order-ref="SMY-2025-771203"></wismo-tracker>
<wismo-launcher></wismo-launcher>
<script>
  window.Wismo = window.Wismo || {};
  Wismo.onLoad = () => {
    Wismo.init({
      publishableKey: "pk_live_smytten_…",
      fetchClientSecret: async () =>
        (await fetch("/api/wismo/session", { method: "POST", credentials: "include" })).json()
          .then(r => r.client_secret),
      locale: "hi-Latn-IN",                       // Hinglish; "hi-IN" Devanagari; "en-IN"
      appearance: {
        theme: "light",                            // light | dark | system
        variables: { colorPrimary: "#E4007C", fontFamily: "Inter, sans-serif", borderRadius: "12px", spacingUnit: "4px" },
        rules: { ".Banner--attention": { borderLeft: "4px solid var(--colorWarning)" } }
      },
      strings: { "tracker.headline.delivery_claimed": "Courier ne delivered bola hai — kya aapko mila?" },
      onEvent: (e) => analytics.track(`wismo.${e.type}`, e.data)   // no PII in e.data
    });
  };
</script>
```

**React:**
```tsx
import { loadWismo } from "@wismo/js";
import { WismoProvider, OrderTracker, Launcher } from "@wismo/react";
const wismo = loadWismo({ publishableKey: "pk_live_…", fetchClientSecret, locale: "en-IN", appearance });

<WismoProvider wismo={wismo}>
  <OrderTracker orderRef={id} slots={{ footer: <ReorderButton/> }} onLoadError={report} />
  <Launcher position="bottom-right" />
</WismoProvider>
```

**Android (Kotlin):**
```kotlin
// build.gradle.kts
dependencies { implementation("dev.wismo:wismo-android:1.+") }   // or wismo-android-core for headless

// Application.onCreate()
Wismo.initialize(
  context = this,
  publishableKey = "pk_live_smytten_…",
  clientSecretProvider = { backend.createWismoSession() },   // suspend fun: String
  config = WismoConfig(
    locale = Locale.forLanguageTag("hi-Latn-IN"),
    appearance = Appearance(colors = Colors(primary = 0xFFE4007C), shapes = Shapes(cornerRadiusDp = 12f)),
  )
)
// Compose
OrderTracker(orderRef = "SMY-2025-771203", modifier = Modifier.fillMaxWidth())
// Anywhere
Wismo.assistant.present(activity, orderRef = "SMY-2025-771203")
// On logout
Wismo.logout()   // clears session and cached transcript (shared-device safety)
```

**React Native:**
```tsx
import { WismoProvider, OrderTracker, useAssistant } from "@wismo/react-native";

export default function App() {
  return (
    <WismoProvider
      publishableKey="pk_live_zomato_…"
      fetchClientSecret={() => api.post("/wismo/session").then(r => r.data.client_secret)}
      locale="hi-Latn-IN"
      appearance={{ variables: { colorPrimary: "#E23744", borderRadius: 16 } }}>
      <Nav/>
    </WismoProvider>
  );
}
function LiveOrderScreen({ orderRef }) {
  const assistant = useAssistant();
  return (<>
    <HostMap orderRef={orderRef} />                                  {/* host keeps its own map */}
    <OrderTracker orderRef={orderRef} variant="compact" parts={{ map: false }} />
    <Button title="Help" onPress={() => assistant.open({ orderRef })} />
  </>);
}
```

### B6. Config schema

Two scopes. **Client config** is presentation only and safe to ship in the app. **Tenant config** (policies, channels, escalation) is set through the dashboard or API, versioned, and never readable or writable from the client.

**Client config (TypeScript):**
```ts
interface WismoClientConfig {
  publishableKey: string;
  fetchClientSecret: () => Promise<string>;
  locale?: "en-IN" | "hi-IN" | "hi-Latn-IN" | "ta-IN" | "te-IN" | "bn-IN" | "mr-IN" | string; // BCP 47; fallback chain hi-Latn-IN → en-IN
  appearance?: {
    theme?: "light" | "dark" | "system";
    variables?: {
      colorPrimary?: string; colorBackground?: string; colorText?: string; colorTextMuted?: string;
      colorSuccess?: string; colorWarning?: string; colorDanger?: string;   // mapped to tones resolved/attention/urgent
      fontFamily?: string; fontSizeBase?: string; spacingUnit?: string; borderRadius?: string;
      density?: "comfortable" | "compact";
    };
    rules?: Record<PublicSelector, CSSProps>;   // whitelisted parts and states only, e.g.
    // ".Headline", ".Banner--calm|--check|--attention|--urgent|--resolved", ".Timeline", ".Step--done|--current|--claimed",
    // ".ProofBadge--verified|--claimed|--disputed", ".Clock", ".ActionButton--primary", ".Bubble--agent|--customer", ".HandoffCard"
    fonts?: Array<{ cssSrc: string } | { family: string; src: string; weight?: string }>;
    disableAnimations?: boolean;
  };
  strings?: Record<StringKey, string>;          // ICU MessageFormat; per-locale via { "hi-Latn-IN": {...} }
  display?: { showCarrierRawStatus?: boolean; showCaseIds?: boolean; currency?: "INR" };
  onEvent?: (e: WismoEvent) => void;            // opened, action_taken, handoff_requested, load_error…
}
```

**Tenant config (YAML via `PUT /v1/config`, versioned, with `POST /v1/config/simulate`):**
```yaml
version: 2026-09-30.3
vertical: ecommerce            # ecommerce | food_delivery | quick_commerce  (selects detector profile + clocks)
region: ap-south-1             # data residency; ap-south-2 (Hyderabad) as DR (inferred choice)

channels:
  in_app:    { tracker: true, assistant: true }
  hosted_page: { domain: track.smytten.com }            # CNAME, like AfterShip custom domains
  whatsapp:  { enabled: true, bsp: gupshup, templates: { delivery_check: tmpl_101, delay_notice: tmpl_102 } }
  sms:       { enabled: true, dlt_entity_id: "…" }      # India DLT registration required for SMS
  push:      { via: host_webhook }                       # host sends push; WISMO emits notify.requested
  email:     { enabled: false }

proactive:
  delivery_check_after_claim: 30m      # "Courier says delivered — did you get it?"
  delay_notice_on: [eta_slipping, tracking_stalled_48h, ofd_overdue_24h]
  quiet_hours: "22:00-08:00 Asia/Kolkata"

policies:
  remedies:
    refund:
      auto_approve:                                   # agent may execute without a human
        max_amount_inr: 499
        when_all:
          - exception in [delivery_disputed_no_proof, lost_in_transit, refund_overdue]
          - customer.remedies_90d < 2
          - order.payment_mode != "COD"               # COD has no instrument to refund; use wallet/UPI flow
      require_approval_above_inr: 499                 # → remedy.proposed webhook + console queue
      hard_cap_inr: 10000                             # agent can never propose above this
      method_preference: [original_instrument, wallet_credit]
    reship:     { auto_approve: false, max_order_value_inr: 2000 }
    goodwill_credit: { auto_approve: true, max_inr: 100, max_per_customer_90d: 1 }
    reattempt:  { auto_approve: true }                # carrier NDR action, no money
  claims:
    missing_item_requires_photo: true
    report_window: 48h                                # after delivery claim
  never:
    - close_case_while_exception_live
    - ask_customer_for_order_id_when_session_scoped
    - promise_date_without_carrier_or_model_eta

escalation:
  - when: customer.requested_human            then: handoff.now            # always one tap
  - when: conversation.repeat_intent >= 2     then: handoff.now            # the "10 bar issue raised" loop
  - when: sentiment <= -0.6                   then: handoff.now
  - when: remedy.amount_inr > 499             then: approval.queue
  - when: exception.age > 24h and case.holder == none   then: page.ops
  - when: incident.detected                   then: [page.ops, banner.affected_orders]
  handoff_target: { type: helpdesk, connector: freshdesk, group: "wismo-escalations" }
  business_hours: "Mon-Sun 09:00-21:00 Asia/Kolkata"

clocks:                                          # regulatory + promise clocks (see product brief)
  support_ack: 48h                               # Consumer Protection (E-Commerce) Rules grievance ack
  resolution: 30d
  refund_bank_reference: 5 working_days          # RBI TAT-style reversal expectation

assistant:
  model_tier: standard
  languages: [en-IN, hi-IN, hi-Latn-IN]
  tone: "warm, brief, no blame on customer, never 'delivered correctly from our end'"
  tools_enabled: [get_order_truth, explain_evidence, request_reattempt, update_phone, open_claim, propose_remedy, handoff]
  pii: { redact_in_logs: true, retain_transcripts_days: 180 }

copy:
  "hi-Latn-IN":
    tracker.headline.delayed: "Thoda late ho gaya hai — naya estimate {eta, date, ::d MMM}"
    tracker.headline.delivery_claimed: "Courier ne delivered mark kiya hai. Mila kya?"
```

**Food-delivery profile differences (Zomato- or Swish-like; the numbers are illustrative):**
- `vertical: food_delivery`, and all clocks are in minutes: `ofd_overdue: 15m past promised`, `rider_stationary: 8m`, `delivery_check_after_claim: 3m`.
- Refunds: `auto_approve.max_amount_inr: 300`, applied when `exception in [not_delivered_rider_far_from_drop, missing_item_with_photo, spilled_with_photo]` **and** `customer.remedies_30d < 3`.
- Proof sources: delivery OTP, rider GPS at drop, photo.
- Escalation: `handoff.sla: 60s` (a hot-food context).

### B7. Server ingestion API (host → WISMO)

Base URL `https://api.wismo.dev/v1`, region-pinned (`api.in.wismo.dev`). Auth is `Authorization: Bearer rk_…`. Versioning uses `Wismo-Version: YYYY-MM-DD`. Every POST accepts an `Idempotency-Key` (Stripe semantics: the first result is stored for 24 hours and a parameter mismatch returns 409).

**1. Canonical events (primary; matches the engine's `Event` model in `engine/src/wismo/events.py`):**
```http
POST /v1/events            # batch ≤ 100
{ "events": [{
  "event_id": "shiprocket:AWB123:2026-09-29T18:02:11Z:7",   // dedupe key; reuse with different payload → 409 conflict
  "type": "shipment.status",            // order.placed|order.confirmed|order.cancelled|shipment.status|eta.promised|
                                        // payment.captured|payment.failed|refund.status|customer.contacted|
                                        // customer.receipt_confirmed|customer.receipt_disputed
  "order_ref": "SMY-2025-771203", "shipment_ref": "AWB123",
  "status": "delivered", "substatus": "delivered.delivered",   // two-level taxonomy; ONDC-mappable
  "occurred_at": "2026-09-29T18:02:11+05:30",
  "asserted_by": "carrier",             // merchant|carrier|rider|payment|customer
  "source_adapter": "shiprocket",
  "raw": { "code": "7", "message": "DELIVERED", "carrier": "Delhivery" },   // always keep the source's words
  "proof": { "otp_verified": null, "photo_url": null, "geo_verified": null, "call_logged": false },
  "location": { "pincode": "560034", "city": "Bengaluru" }
}]}
→ 202 { "accepted": 1, "duplicates": 0, "rejected": [] }   # per-event results; partial success allowed
```
Rules:
- Out-of-order events are fine, because the projector orders by `occurred_at` and tolerates gaps.
- Unknown `raw.code` values are accepted and mapped to `exception.unknown`, which raises an alert on the mapping itself (the AfterShip "enums may be extended" lesson).
- `asserted_by` is **required**, because truth is provenance-weighted.

**2. Convenience resource endpoints** (Narvar-style, for teams that think in documents rather than events). The server diffs each one into canonical events:
- `PUT /v1/orders/{order_ref}` upserts an order snapshot: items, amounts, payment mode, the promised ETA shown at checkout, and customer_ref.
- `PUT /v1/orders/{order_ref}/shipments/{shipment_ref}` upserts a shipment: carrier, AWB, items.
- `POST /v1/refunds` records a refund state (`initiated`, `processed`, `credited` + `bank_reference`/ARN/RRN).
- `POST /v1/rider_locations` (food) carries a stream of `{order_ref, lat, lng, ts}` at ≤1 per 5 s. Coordinates are kept for 24 hours only, then reduced to derived facts (DPDP minimisation).

**3. Hosted connectors** (no host code): `POST /v1/connectors` with `{type: "shiprocket", credentials: {...}}` returns a unique inbound URL `https://in.wismo.dev/c/{connector_id}/{random_128bit}`.
- Where the provider signs (Razorpay `X-Razorpay-Signature`, AfterShip `aftership-hmac-sha256`, Shopify HMAC), the signature is verified.
- Where it doesn't (Shiprocket `x-api-key`), the event is treated as a **low-trust claim**. Before any money-moving decision the engine **re-fetches** the tracking API, and it rate-limits and alerts on anomalies.
- **Poll-on-silence** follows ClickPost's pattern: if there is no update within a profile-specific window, WISMO polls the carrier.

**4. Customer-side facts** arrive through the SDK itself (`confirm_receipt`, `dispute_delivery` with photo). They are signed by the session and stored with `asserted_by: customer`.

**5. Read APIs:**
- `GET /v1/orders/{ref}/truth` returns the view model (B9).
- `GET /v1/cases?state=open`.
- `GET /v1/orders/{ref}/events` returns the audit log.
- `GET /v1/incidents`.

### B8. Webhooks out (WISMO → host) and the approval loop

**Format:** Standard Webhooks. Headers are `webhook-id`, `webhook-timestamp` and `webhook-signature: v1,<base64>`, with a `whsec_` secret. The receiver checks a 5-minute tolerance, and during rotation both secrets sign for up to 24 hours. Delivery is at least once, retried with exponential backoff for 3 days (live) or 3 times over a few hours (test). Events can be resent from the dashboard (15 days) or the CLI (30 days). Endpoints can be disabled after repeated failures, with an email alert. The IP egress list is published.

**Payload:**
```json
{ "id": "evt_01J…", "type": "exception.opened", "api_version": "2026-09-30", "created": "2026-09-30T09:12:44Z",
  "livemode": true, "tenant": "smytten",
  "data": { "object": { "order_ref": "SMY-2025-771203", "order_version": 42, "exception": "delivery_claimed_unverified",
            "reasons": ["delivered_before_eta", "no_ofd_scan", "phone_mismatch"], "case_id": "WSM-7F3K" },
            "previous_attributes": { "truth_state": "out_for_delivery" } } }
```
`order_version` is monotonic per order, so consumers drop stale deliveries (Stripe: "don't use `created` to determine order"). A thin option sends `{id, type, related_object: {order_ref, url}}` only.

**Event types:**

| Type | Why the host cares |
|---|---|
| `order.truth_changed` | Mirror the derived state into the host's own order screen and CRM |
| `exception.opened` / `exception.resolved` | Ops dashboards and alerts |
| `case.opened` / `case.updated` / `case.closed` | Mirror into the helpdesk; visible IDs |
| `remedy.proposed` | **Money needs host approval**: the host approves or rejects through `POST /v1/remedies/{id}/approve` (with `rk_…remedies:approve`) or in the WISMO console |
| `remedy.approved` / `remedy.executed` / `remedy.failed` | For the host's finance ledger |
| `notify.requested` | The host sends its own push or in-app notification with WISMO's copy |
| `conversation.handoff_requested` | Includes the summary, evidence and transcript link, so the helpdesk agent never re-asks |
| `customer.receipt_disputed` | Carrier claim workflow |
| `incident.detected` | Courier × pincode × day spike (the December 2025 cluster lesson) |

**Remedy execution options (host picks per remedy type):**
- **(a) Host executes** (recommended for refunds). WISMO emits `remedy.approved` with an `idempotency_key`. The host calls its own Razorpay or Juspay refund, then reports back with `POST /v1/events` `refund.status`.
- **(b) WISMO executes through a connector** using a host-provided **restricted, agent-tagged** payment key. It is capped by `hard_cap_inr`, and every execution carries the remedy id as the idempotency key for the payment gateway.

**Action endpoints** (Intercom data-connector pattern, reversed):
- The host may register `actions: [{name: "reattempt_delivery", url: "https://smytten.com/wismo/actions/reattempt", method: POST}]`.
- WISMO signs the requests (the same Standard Webhooks scheme) and sends `Idempotency-Key`.
- The host returns `{status: "ok" | "rejected", message}`.
- The agent treats a failure as a condition and never retries silently.

### B9. Headless mode

**Web / RN (`@wismo/headless`):**
```ts
const wismo = createWismo({ publishableKey, fetchClientSecret, locale: "hi-Latn-IN" });

const order = await wismo.orders.get("SMY-2025-771203");      // display-ready view model
const unsub = wismo.orders.subscribe("SMY-2025-771203", (o) => render(o));   // SSE; resumes with Last-Event-ID

await wismo.orders.confirmReceipt(ref);
await wismo.orders.disputeDelivery(ref, { reason: "not_received", photo: file });

const convo = await wismo.assistant.start({ orderRef: ref });  // agent already has order context
convo.on("message", m => …);            // { role, text, parts: [ {type:"evidence"}, {type:"action", id, label} ] }
convo.on("action_proposed", a => …);    // render your own confirm UI; then convo.confirm(a.id)
convo.on("handoff", h => …);            // { case_id, eta_seconds, channel }
await convo.send("abhi tak nahi aaya");
await convo.requestHuman();              // always available
```

**View model** (from the engine's `view.py`; stable and versioned; every string is already localised):
```jsonc
{
  "order_ref": "SMY-2025-771203", "version": 42,
  "state": "delivery_claimed",          // on_the_way|out_for_delivery|preparing|rider_assigned|delayed|attempt_failed|
                                        // delivery_claimed|delivery_disputed|delivered|cancelled|returning|
                                        // refund_not_started|refund_on_its_way|refund_overdue|refunded|payment_issue
  "tone": "check",                      // calm|check|attention|urgent|resolved → maps to appearance tones
  "headline": "Courier ne delivered mark kiya hai. Mila kya?",
  "reasons": [{ "code": "delivered_before_eta", "text": "…" }],
  "proof": { "state": "claimed", "otp": "not_used", "photo": "none", "geo": "unknown" },
  "promise": { "eta": "2026-09-30", "revisions": 1, "source": "carrier" },
  "clocks": [{ "kind": "report_window", "ends_at": "…", "label": "Report within 48h" }],
  "case": { "id": "WSM-7F3K", "holder": "wismo_agent", "ack_by": "…" },
  "timeline": [{ "at": "…", "text": "…", "asserted_by": "carrier", "raw": "DELIVERED", "kind": "claim" }],
  "actions": [{ "id": "confirm_receipt", "label": "Haan, mil gaya", "primary": true },
              { "id": "dispute_delivery", "label": "Nahi mila" }],
  "carrier": { "name": "Delhivery", "awb": "AWB123", "raw_status": "DELIVERED" }
}
```

**Slots and parts (layer 2):**
- **Web:** `<wismo-tracker>` exposes `::part(headline|banner|timeline|step|proof|actions|footer)` and named `<slot name="footer">` / `<slot name="empty">`.
- **React:** `slots={{ footer, empty, actionButton: (a) => … }}`.
- **Android:** composable lambdas.
- **iOS:** `@ViewBuilder` closures.

The tracker's `parts.map=false` lets a food app keep its own map (Zomato already has one) while WISMO supplies truth, headline and actions.

**Mobile headless:** `WismoCore.orders.observe(ref): Flow<OrderView>` (Android) and `AsyncStream<OrderView>` (iOS).

### B10. Live maps (food and quick commerce)

- **Default is none.** Food apps already run a map (Google or Mapbox) and a rider pipeline. WISMO consumes rider pings (`/v1/rider_locations`) to derive facts: rider stationary, rider far from the drop at the "delivered" claim, ETA drift. It does **not** redraw the map.
- **Optional `<wismo-live-map>`** for hosts with no map. It uses Mapbox GL JS with a WISMO-owned **URL-restricted public token**, or it takes a host `mapProvider` adapter. Location reaches the client via a **per-order scoped token**, following Fleet Engine's consumer-token model (≤1 h, one order).
- **Privacy:** the rider's precise location is shown only while the order is out for delivery. It is snapped to a coarse point after delivery and purged after 24 hours (inferred DPDP minimisation).

### B11. Security and compliance

- **CSP to document:**
  - `script-src https://js.wismo.dev`
  - `connect-src https://api.in.wismo.dev wss://rt.in.wismo.dev`
  - `img-src https://*.wismo.dev data:`
  - `frame-src` none (no iframes)
  - `style-src` needs the constructable-stylesheet hash if strict (inferred)
  - Give a Trusted Types policy example, following Stripe.
- **Isolation.** Shadow DOM custom elements, not iframes. The host already owns the order data, and there is no PCI-like reason to hide it. Chat attachments upload directly to WISMO storage with pre-signed URLs.
- **Session scope.** Enforce `order_refs`, features and TTL server side. Every API call from the client is re-authorised against the session, and IDs in URLs are never trusted alone.
- **PII minimisation:**
  - The client view model carries a masked phone (`••••4471`), a pincode and city, never the full address.
  - The agent sees the minimum fields per tool.
  - Transcripts are redacted in logs.
  - No tenant data is used for model training.
  - The LLM provider is configured for India or in-region processing where available, with a documented list of sub-processors (inferred).
- **Prompt injection.** Customer text, carrier remarks and photo captions are **data**, never instructions. Tool calls are authorised by the policy engine (deterministic), not by the model's say-so. Money tools require a policy decision id.
- **DPDP posture:**
  - WISMO is the processor and the host the fiduciary; sign a DPA.
  - Default region `ap-south-1`.
  - `DELETE /v1/customers/{ref}` does erasure (cascades to transcripts and events, keeping only anonymised aggregates), and `GET /v1/customers/{ref}/export` supports access requests.
  - Audit logs are kept ≥1 year.
  - The breach runbook targets host notification well inside the 72-hour Board window.
  - Consent: WhatsApp and SMS proactive messages need the host's opt-in flag per customer (`customer_context.channels_opt_in`).
- **Key hygiene.** Use restricted keys by default, with an access policy (IP or ASN) on live server keys and rotation with a 7-day overlap. `pk_` keys carry an origin and package allowlist.
- **Abuse.**
  - Rate-limit dispute and remedy requests per customer.
  - Detect remedy velocity across a household, device or pincode.
  - Never auto-refund COD orders to a new instrument.

### B12. Docs structure

1. **Quickstart: "See a disputed delivery resolved in 5 minutes."**
   - Sign up; test keys are auto-injected into snippets.
   - `npx @wismo/cli init` scaffolds `/api/wismo/session`.
   - Paste `<wismo-tracker order-ref="ord_test_delivered_unverified">`.
   - Run `wismo trigger scenario smytten-marked-delivered`.
   - Watch the tracker flip from "Delivered ✓" to "Courier says delivered. Did you get it?", tap "Nahi mila", and watch the agent open a case and propose a refund that lands in the approval queue.
   - The fixtures come from the real complaint shapes (`scenarios/demo/*.json`), so the quickstart *is* the product pitch.
2. **Guides by platform:** web, React, Android, iOS, RN, Flutter; each is one page with the same five steps (install, session endpoint, init, place component, test).
3. **Guides by vertical:** e-commerce parcels (Smytten-like), food delivery (Zomato-like), quick commerce (Swish-like).
4. **Guides by job:**
   - Ingest events from your OMS.
   - Connect Shiprocket / Delhivery / ClickPost.
   - Wire refunds (Razorpay).
   - Hand off to Freshdesk / Zendesk.
   - Configure policies safely (`simulate`).
   - Hindi and Hinglish copy.
   - Theming.
   - Headless.
5. **Reference:**
   - REST API (OpenAPI-generated, with `.md` twins and `llms.txt` for agents).
   - SDK references (TypeDoc, Dokka, DocC).
   - Event and webhook catalogue with sample payloads.
   - Error codes, each with a doc link in the error body.
   - Appearance parts and variables table.
   - String keys table.
6. **Testing:**
   - Test mode with a scenario library (named after failure modes: `marked_delivered_no_otp`, `ofd_stuck_48h`, `refund_initiated_no_arn`, `phone_mismatch_ndr`, `rider_far_at_drop`).
   - A virtual clock (`wismo replay --speed 1000x`).
   - `wismo listen --forward-to localhost:3000/webhooks`.
   - Dev sessions (`cs_dev_…`, like Stream dev tokens).
7. **Going live checklist:** live keys, origin allowlist, webhook signature verified, idempotency on ingestion, policy approved and simulated, handoff target tested, DPA signed, CSP updated, logout wired.
8. **Changelog and upgrades:** dated versions (`Wismo-Version`), with deprecation windows.

**What makes it good (applied):**
- Runnable samples with your own keys.
- A failure-first narrative (the demo *is* a broken delivery).
- Every page answers "what can go wrong" (a troubleshooting table like Stripe's webhook table).
- Console warnings in the SDK for common mistakes: missing `fetchClientSecret`, a `pk_test` key on a production origin, a customer session without `order_refs` on an order page.

### B13. Integration guide outlines

#### Smytten-like (India D2C e-commerce sample boxes; web + Android + iOS; courier parcels)

| Step | What | Time (est.) |
|---|---|---|
| 0 | Create a test account; install the CLI; run the quickstart scenario | 10 min |
| 1 | **Session endpoint** in the Smytten BFF: `POST /api/wismo/session` → `wismo.customerSessions.create({customer_ref, order_refs?, locale})` using `rk_…sessions` | 1 h |
| 2 | **Order feed:** at checkout, `order.placed` + `eta.promised` (the promise shown to the shopper matters); on cancel, `order.cancelled`; via the OMS job with `rk_…events` + `Idempotency-Key` | 0.5–1 d |
| 3 | **Carrier feed:** enable the Shiprocket connector (paste the credentials) or the Delhivery / ClickPost connectors; poll-on-silence on by default | 1 h |
| 4 | **Payments and refunds:** Razorpay connector for refund status (ARN/RRN) *or* send `refund.status` from the finance service | 2–4 h |
| 5 | **Place components:** web order-detail page `<wismo-tracker>`; account page `<wismo-order-list>`; global `<wismo-launcher>`; Android `OrderTracker()` in `OrderDetailFragment`; iOS `OrderTrackerView` | 0.5 d per platform |
| 6 | **Appearance + copy:** Smytten pink `colorPrimary`, `borderRadius 12px`; set `hi-Latn-IN` for Hinglish users (detect from the app language plus chat input) | 1 h |
| 7 | **Policies:** start at `auto_approve.max_amount_inr: 0` (the agent proposes, humans approve); run `simulate` against the last 90 days of disputes; raise to ₹299–499 once precision is known | 1 d (ops) |
| 8 | **Handoff:** Freshdesk connector (Smytten's helpdesk is unknown; pick at integration time) with the evidence summary; **remove "delivered correctly from our end" macros** | 2 h |
| 9 | **Proactive:** WhatsApp delivery-check template after a delivery claim; SMS DLT template | 1 d (template approval) |
| 10 | **Go-live:** checklist; start with a 10% rollout by `customer_ref` hash; watch the `delivery_disputed` rate and remedy precision | — |

Smytten specifics:
- Sample-box orders have low item values, so auto-refund thresholds can be modest.
- Credits-based pricing means `wallet_credit` is a natural remedy.
- **Phone on the parcel ≠ account phone** is a known failure, so the `update_phone` self-serve action with a carrier re-attempt is high-value.

#### Zomato-like (food delivery; minutes clock; in-house riders; native apps)

| Step | What |
|---|---|
| 1 | **Session endpoint** (same as above). Session TTL 15 min; `order_refs` = the active order only |
| 2 | **Order and kitchen events:** `order.placed` with the promised ETA shown at checkout; `pending.preparing` → `packed.packed`; `pending.searching_agent` / `pending.agent_assigned` |
| 3 | **Rider pipeline:** stream `POST /v1/rider_locations` from the dispatch system (not the phone) at ≤5 s; `in_transit.picked_up`; `delivered` with `proof.otp_verified`, `geo_verified` |
| 4 | **Placement:** keep the host's live-order map; add `OrderTracker variant="compact" parts={{map:false}}` under it; the **Help** button → `assistant.open({orderRef})`, so the agent opens already knowing the order, ETA drift and rider state |
| 5 | **Headless option:** Zomato-scale apps will likely use `WismoCore.orders.observe()` and render in their own design system. WISMO supplies `state`, `headline`, `actions` and the conversation stream only |
| 6 | **Policies (food profile):** minute clocks; auto partial refund for `missing_item_with_photo` ≤ ₹150 and full refund for `not_delivered_rider_far_from_drop` ≤ ₹300 with a customer velocity cap; everything else goes to a human within 60 s |
| 7 | **Incident detection:** kitchen × zone × 30-min window (restaurant delays) and rider-fleet × zone (rain surge) → `incident.detected` → a proactive banner on affected orders ("Baarish ki wajah se 10 min late") |
| 8 | **Handoff:** the in-house support tool through `conversation.handoff_requested` + the action endpoints (`issue_refund`, `call_rider`) |
| 9 | **Load and latency:** SSE through the region edge; target < 5 s event-to-screen (the architecture NFR) |

---

## Part C. Open questions and risks

1. **Hinglish locale code.** `hi-Latn-IN` is valid BCP 47 (Hindi in Latin script), but OS locale pickers never emit it. The SDK must infer it from chat input and offer a toggle, not rely on the device locale (inferred).
2. **Food apps won't embed a vendor UI.** Assume headless-first for Zomato and Swiggy scale, and UI-first for D2C brands. Design the view model as the primary contract.
3. **Carrier feed trust.** Indian 3PL webhooks are weakly signed. Money decisions must wait on re-verification or on customer and host proof, and that adds latency to auto-refunds.
4. **Approval UX ownership.** If remedies need host approval, who staffs the queue at 2 a.m.? Default to a **time-boxed auto-approve fallback** only under a low cap, and make it explicit in policy.
5. **LLM data residency.** Confirm which model providers offer India-region processing before promising "data never leaves India". Until then, state "stored in India; processed by named sub-processors".
6. **The regulatory clocks** cited (48 h ack, 30 d resolution, RBI TAT) come from the product brief. Re-verify the exact rule text before putting them in customer-facing copy.
