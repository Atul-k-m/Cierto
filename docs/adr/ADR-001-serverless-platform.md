# ADR-001: Serverless platform and local-first runtime

**Status:** Accepted (2026-09-29; local database: embedded Postgres via `pgserver`)
**Date:** 2026-09-29
**Deciders:** Ishrajesh (owner)

## Context

The owner prefers a serverless architecture. The engine has four needs that decide the platform:

1. **Webhooks in.** Order, carrier and payment events arrive in bursts and must be processed in order per order.
2. **Durable timers.** The product is built on clocks: ETA breach, "report within 48 hours", RBI T+5, a 48-hour acknowledgement and a 30-day resolution. Thousands of one-off timers must fire reliably.
3. **Python for the engine and agent.** The research and dataset are in Python; detectors and the Claude agent are simplest there.
4. **An India data story.** A WISMO layer is a data processor under the DPDP Act. The proof of concept uses synthetic data, but the design should show where real customer data would live.

The proof of concept must also **run entirely on a laptop** for interviews and offline demos, with a replay clock that compresses days into seconds.

## Decision

**AWS serverless in `ap-south-1` (Mumbai), behind a ports-and-adapters core that also runs locally.**

The engine is a plain Python package with four ports: `EventStore`, `Scheduler`, `Notifier`, `LLM`. Two adapter sets implement them:

| Port | Local (demo, tests) | Cloud (AWS Mumbai) |
|---|---|---|
| Ingest / API | FastAPI | API Gateway HTTP API → Lambda |
| Per-order ordering | in-process queue | SQS FIFO, `MessageGroupId = order_id` |
| Event store + projections | Postgres (Docker) | Postgres with row-level security (Aurora Serverless v2, scales to zero) |
| Durable timers | in-process scheduler on a **virtual clock** | EventBridge Scheduler one-time schedules → Lambda |
| Internal events | in-process bus | EventBridge bus |
| Live updates to widget | Server-Sent Events | API Gateway WebSocket |
| Evidence photos | local disk | S3 presigned upload |
| Static apps and widget bundle | Vite dev server | S3 + CloudFront |
| IaC | n/a | AWS SAM |

## Options considered

### Option A: AWS serverless, Mumbai (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Medium: more services to wire, mitigated by SAM and the local adapter set |
| Cost | Near zero at demo volume (free tiers); pay per request |
| Scalability | High; SQS FIFO + Lambda handles far beyond POC needs |
| Fit to needs | Timers: EventBridge Scheduler is purpose-built for one-off schedules. Python: first-class. India: Mumbai region |
| Hiring signal | Widely recognised; easy to defend in interviews |

**Pros:** every hard need has a managed primitive; in-India region; mature Python.
**Cons:** most moving parts of the three; cold starts on the agent path; AWS console friction for a solo builder.

### Option B: Cloudflare Workers + Durable Objects

| Dimension | Assessment |
|---|---|
| Complexity | Low: one Durable Object per order holds its log, projection and alarms |
| Cost | Lowest |
| Scalability | High |
| Fit to needs | Timers: DO alarms are an elegant "order actor". Python Workers are less mature than TypeScript; no India data-location guarantee for Durable Objects |
| Hiring signal | Strong with infra-savvy teams |

**Pros:** the actor-per-order model matches the domain beautifully; tiny ops surface.
**Cons:** pushes the engine to TypeScript; weaker DPDP residency story; Postgres RLS would need an external database anyway.

### Option C: Vercel functions + Supabase (Mumbai) + a workflow service (Inngest/QStash)

| Dimension | Assessment |
|---|---|
| Complexity | Low to start |
| Cost | Low; free tiers |
| Fit to needs | Timers via a third-party workflow service; Python functions are secondary on Vercel |
| Hiring signal | Common in product startups |

**Pros:** fastest to a deployed front end; Supabase gives Postgres with RLS in Mumbai.
**Cons:** the core need (durable timers) depends on a third vendor; three vendors for one engine.

## Trade-off analysis

B is the most elegant model and C the fastest start, but A is the only option where **durable timers, per-order ordering, Python and an India region** are all first-party. Because the core is ports-and-adapters, the cloud choice is reversible: moving to B later means writing a new adapter set, not rewriting the engine.

## Consequences

- **Easier:** demoing offline; testing detectors deterministically with a virtual clock; a credible DPDP answer ("processed in Mumbai, RLS per tenant").
- **Harder:** two adapter sets to keep in step, so every port gets a contract test run against both.
- **Revisit:** if the agent's cold-start latency hurts the chat experience, move that one function to provisioned concurrency or a container.

## Action items

1. [x] Owner confirmed A ("go with your picks", 2026-09-29).
2. [ ] Phases 1–3 build the local adapter set only; cloud adapters land in Phase 4.
3. [ ] Contract tests per port, run against both adapter sets from Phase 4.
