# Deploying Cierto

One container serves everything on one port: the API (`/v1/*`), the demo API (`/v1/demo/*`), the browser SDK (`/sdk/*`) and the prerendered site (`/`). It runs on Cloud Run behind Google's front end, or locally behind Caddy, as N identical, stateless replicas. Shared state (session op logs, rate-limit counters, the LLM budget) lives in Redis (Upstash in production).

## Architecture

```
            browsers · crawlers · host servers (SDK)
                            │ HTTPS
    ┌───────────────────────▼────────────────────────┐
    │ Cloud Run front end (Google Front End)          │  TLS, HTTP/2, autoscaling 0..4,
    │ no session affinity                             │  appends the client IP to X-Forwarded-For
    └──────┬──────────────────┬──────────────────┬────┘
           │                  │                  │        (locally: Caddy :8080, round robin → app1..3)
    ┌──────▼───────┐   ┌──────▼───────┐   ┌──────▼───────┐
    │ instance     │   │ instance     │   │ instance     │  1 vCPU · 512 MiB · 80 concurrent requests
    │ uvicorn      │   │   …          │   │   …          │
    │ Firewall     │   └──────────────┘   └──────────────┘
    │ gzip · CORS  │
    │ FastAPI      │── LRU of materialized sessions (sid, version)
    │ web dist     │
    └──┬────────┬──┘
       │        │
┌──────▼─────┐ ┌▼────────────────────┐
│ Redis      │ │ Gemini API          │
│ op logs    │ │ ≤ LLM_DAILY_BUDGET  │
│ counters   │ │ calls per UTC day   │
│ LLM budget │ └─────────────────────┘
└────────────┘
```

Inside an instance, a request passes: uvicorn (proxy headers) → **Firewall** (`waf.py`: methods, sizes, scanners, body cap, rate limits; security headers and one JSON access-log line on the way out) → gzip for API/SDK → CORS for `/v1/*` (not `/v1/demo/*`) and `/sdk/*` → routes → the web build (`web.py`).

## Why op-log sessions instead of sticky sessions

A demo session is a live engine on a virtual clock (~0.4 MB of objects, closures and timer heaps). It used to live in one process's memory, so a load balancer would have needed affinity. Affinity is the wrong foundation here: Cloud Run's is best-effort, scale-to-zero discards every instance when idle, a deploy or scale-in drops all sessions on the instances that go away, and a hot session pins load to one instance.

Instead each session is an **append-only log of ops** (`create`, `advance`, `act`, `approve`; for SDK tenants also `session`, `events`, `order`, `config`, `advance`), stored in Redis as a hash (`1`, `2`, …). State is the fold of the log:

- **Any instance can serve any request.** Each keeps an LRU (`SESSION_CACHE_SIZE`) of materialized sessions with the version they reflect; on each request it asks Redis for the log length (one `HLEN`) and replays only the ops it lacks. A cold instance replays the whole log: creating the demo takes ~9 ms, a full story ~20 ms.
- **Writes are compare-and-set.** A write plans an op against the current state (validation errors return before anything changes), applies it, then `HSETNX`es field `version+1`. If another instance got there first, the local copy is dropped, rebuilt from the log and the op planned again. No Lua or WATCH, so it runs on any Redis-compatible service.
- **Replay is exact by construction.** Only the virtual clock moves time in a demo; SDK ops carry the wall time they ran at and the clock ticks to it before the op applies. Ids come from `sha256(sid:counter)` (webhook and event ids match on every instance; remedy and case ids were already content-derived). Model outputs are recorded into the op that asked for them, so a replay reads the rewording back: no second call, no different wording. Webhook sends wait for the commit, and a shared `SET NX` makes exactly one instance send each.
- **Bounded.** Sessions expire after `SESSION_TTL_SECONDS` idle (2 h); at most `SESSION_MAX_LIVE` live demo sessions (least recently used evicted); an unknown or expired id is a 404 (`session not found; start a new one`), as before.
- Tests (`tests/test_stateless.py`) run the same op sequence through three independent app instances sharing one store, against memory and Redis, and require identical JSON (webhook ids included), a replay without model calls, and a lost-race rebuild.

The shared SDK test tenants follow the same model with one log per tenant. Clock-driven follow-ups (a refund firing at its deadline) run on whichever instance ticks first and use the templates, not the model, so every instance computes the same thing. `POST /v1/dev/reset`, or `SDK_LOG_MAX_OPS` writes, start the tenant on a fresh log that carries its config and customer sessions over.

Trade-off: replicas must run the same code for replays to agree. A rolling deploy briefly runs two revisions; a session that spans it follows the newer engine's logic from then on. Sessions are short-lived demos, so this is accepted rather than versioned.

**Without `REDIS_URL`** every instance keeps its own logs and counters: correct only for one instance. `deploy.sh` sets max-instances to 1 in that case.

## Load balancing

| | Cloud Run | Local (`deploy/compose.yaml`) |
|---|---|---|
| Balancer | Google front end, per-request, no affinity | Caddy `lb_policy round_robin` over `app1..3` |
| Health | startup probe + liveness probe on `/healthz` | active `health_uri /healthz` every 5 s; passive: 2 failures (errors, 5xx, >5 s) → out for 30 s |
| Retries | client-side | `lb_try_duration 5s`, `lb_retries 2` (dial errors always; other failures for GET only) |
| Client IP | `TRUSTED_PROXY_HOPS=1` | `TRUSTED_PROXY_HOPS=1` (Caddy replaces untrusted XFF with the peer) |
| Drain | SIGTERM → uvicorn finishes in-flight requests (`GRACEFUL_SHUTDOWN_SECONDS=8`, Cloud Run allows 10) | same |

`/healthz` is liveness (touches nothing). `/readyz` is readiness: the web build is present and the session store answers (`{"status":"ready","web":true,"store":{"kind":"redis","ok":true},"instance":"…"}`, 503 otherwise). Every response carries `X-Served-By` (hostname, or `SERVED_BY`) so round-robin is visible. Uvicorn's keep-alive (75 s) outlives Caddy's upstream keep-alive (30 s), so the balancer never reuses a connection the app is closing.

## WAF (app level)

Cloud Armor is paid, so the first line of defence is middleware (`engine/src/wismo/waf.py`). Counters are fixed windows in Redis, shared by all instances (in memory without Redis).

**Client IP.** `X-Forwarded-For` is a list each hop appends to: `<whatever the client sent>, <client>, <proxy>…`. The left-most entry is chosen by the client, so it is spoofable and useless for limits (uvicorn's own `forwarded_allow_ips="*"` handling uses it, which is why the WAF doesn't read `scope["client"]` behind a proxy). The WAF takes the entry `TRUSTED_PROXY_HOPS` from the right: 1 on Cloud Run or behind Caddy, 2 behind a Google external Application Load Balancer, 0 with nothing in front (the socket peer; uvicorn then ignores proxy headers entirely).

| Layer | Rule | Default | Env | Response |
|---|---|---|---|---|
| Methods | GET HEAD POST PUT OPTIONS only; site routes GET/HEAD | | | 405 + `Allow` |
| URI / headers | path > 2 KB or query > 4 KB; headers > 16 KB | | | 414 / 431 |
| Scanners | `/wp-`, `.php`, `.asp(x)`, `.jsp`, `/.env`, `/.git`, `phpmyadmin`, `/cgi-bin`, `/xmlrpc`, `/actuator`, `.sql`, `.bak`, … | | | bare 404, app never runs |
| Body | size cap, also for chunked bodies (counted as read) | 64 KB; 1 MB for `/v1/events` | `MAX_BODY_BYTES`, `MAX_EVENTS_BODY_BYTES` | 413 |
| Rate: everything | per IP (static files under `/assets/`, `/site/`, `/og/`, `/sdk/` and icons are exempt) | 300/min | `RATE_LIMIT_GENERAL` | 429 + `Retry-After` |
| Rate: ask (LLM-backed) | `POST /v1/demo/sessions/*/orders/*/ask`, `/v1/orders/*/ask`, per IP | 20/min and 200/day | `RATE_LIMIT_ASK` | 429 |
| Rate: demo sessions | `POST /v1/demo/sessions`, per IP | 20 per 10 min | `RATE_LIMIT_DEMO_CREATE` | 429 |
| Rate: SDK writes | POST/PUT `/v1/*` (not demo), per IP and per API key | 60/min · 600/min | `RATE_LIMIT_SDK_WRITE`, `RATE_LIMIT_SDK_KEY` | 429 |
| User agent | API writes with no User-Agent at all | | | 403 |
| Crawlers | never blocked: Googlebot, Bingbot, GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-User, PerplexityBot, Google-Extended… (the site wants AEO) | | | |

Rates are `count/window` lists: `20/m,200/d`, `20/10m`. `WAF_RATE_LIMITS=off` disables them (the test suite). Limits fail open if Redis is unreachable; the LLM budget fails closed.

**Headers on every response:** `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()`, `Cross-Origin-Opener-Policy: same-origin`, `X-Served-By`; `Strict-Transport-Security: max-age=63072000; includeSubDomains` only when the external scheme is https. HTML also gets the CSP (`waf.CSP`, one constant): `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'; object-src 'none'`, plus `upgrade-insecure-requests` over https. The site must therefore ship no inline executable scripts (JSON-LD data blocks are fine) and no third-party origins. CORS is open (`*`, no credentials) on `/v1/*` and `/sdk/*` for publishable keys, and absent on `/v1/demo/*` and the site. Uvicorn's `Server` header is off.

**Access logs** (`LOG_FORMAT=json`): one line per request with `severity` and `httpRequest` (method, path without query string, status, size, latency, remote IP, user agent) that Cloud Logging indexes; `waf` names the rule that blocked it; probes are not logged; bodies, query strings and keys never are.

## LLM budget

Every Gemini/Anthropic call goes through `resolver._llm_call`, which first spends one unit of `LLM_DAILY_BUDGET` (1500 calls per UTC day, across all instances) and of the caller's `LLM_IP_DAILY` (100). When either is spent, or Redis can't be read, the call raises and the caller falls back to its deterministic template: `ask` still answers (`"rephrased": false`), resolutions are still made, never an error. Replays read recorded outputs and never spend. With the ask limit (20/min, 200/day per IP) in front, one abusive IP costs at most 100 calls a day and the whole service at most the budget.

## Caching and compression

| Path | Cache-Control | Compression |
|---|---|---|
| `/assets/*` (content-hashed) | `public, max-age=31536000, immutable` | the build's `.br` / `.gz` siblings when accepted (`Content-Encoding`, `Vary: Accept-Encoding`); else gzip here |
| HTML, `robots.txt`, `sitemap.xml`, `llms*.txt`, `docs/*.md`, `site.webmanifest`, json | `no-cache` + ETag (304 on `If-None-Match`, one ETag per encoding) | gzip here, cached per (path, origin, encoding) |
| `/site/photo/*`, `/og/*`, root icons | `public, max-age=604800` | none (already compressed) |
| `/sdk/*` | `public, max-age=300`, CORS `*` | gzip (API middleware, ≥ 1 KB) |
| `/v1/*` JSON | as set per route | gzip ≥ 1 KB |

Text files may contain `__SITE_URL__`; it becomes `SITE_URL`, or the request's external origin (scheme from `X-Forwarded-Proto` via uvicorn, host from `X-Forwarded-Host` behind a trusted proxy, else `Host`). Set `SITE_URL` in production so canonical URLs never depend on a request header.

**Site routes** (the contract with the web build): `/` → `index.html`; `/demos` → `demos/index.html` (every prerendered `<route>/index.html`), no redirect; `/demos/` → 301 `/demos` with the query kept (also `/demos/index.html` and `/index.html`); files as they are; anything else → `404.html` with status 404 (a build without `404.html` gets `index.html`, still as a 404); `/v1/*` and `/sdk/*` misses stay JSON 404s.

## Cost at free tier

| Item | Free allowance | This service |
|---|---|---|
| Cloud Run (request-based billing, per billing account per month) | 2M requests, 180,000 vCPU-s, 360,000 GiB-s | 1 vCPU / 0.5 GiB, billed only while serving (100 ms granularity): ~1.8M light requests a month, or ~750 viewer-hours of the Demos page polling every 1.5 s. Scale to zero when idle. Needs a billing account. |
| Upstash Redis (free plan; check current limits) | 256 MB, ~500K commands/month | a caught-up poll is 1 `HLEN` + 2 for the rate limit; static files cost none; an `ask` ~11. The Demos page polling at 1.5 s is ~120 commands/min per viewer, so ~70 viewer-hours a month free; pay-as-you-go beyond that is cents per viewer-hour. Polling less often stretches it. |
| Artifact Registry | 0.5 GB storage | one ~200 MB image; delete old tags |
| Cloud Build, Secret Manager | free build minutes; 6 secret versions, 10K accesses | a few deploys a month; 2 secrets read at instance start |
| Gemini | per Google's pricing | bounded by `LLM_DAILY_BUDGET` |
| Cloud Armor | not free (see below) | not used; the WAF is in the app |

## Run it

Local development (unchanged): `cd engine && .venv/Scripts/python.exe -m wismo serve` (add `--build` after changing the site). Production mode on one machine: `python -m wismo serve --no-build --host 0.0.0.0 --port 8080` with `LOG_FORMAT=json`.

### Three replicas behind Caddy, with Redis (needs Docker)

```sh
cp deploy/.env.example deploy/.env                  # optional: GEMINI_API_KEY (gitignored)
docker compose -f deploy/compose.yaml up --build    # http://localhost:8080
for i in 1 2 3 4 5 6; do curl -s -o /dev/null -D - http://localhost:8080/healthz | grep -i x-served-by; done
docker compose -f deploy/compose.yaml stop app2     # failover: requests keep succeeding on app1 and app3
curl -s http://localhost:8080/readyz
```

### Free, no card: Vercel + Upstash

Vercel's Hobby plan and Upstash's free Redis both sign up with GitHub and need no payment card. Vercel's FastAPI preset runs `app.py` (the same app) as one function on Fluid compute: it scales out on its own and Vercel's edge routes and load-balances between instances, so shared state in Redis is required. Immutable assets carry `CDN-Cache-Control`, so the edge serves them after the first request. `vercel.json` pins the function to Mumbai (`bom1`); create the Redis database in the same region (`ap-south-1`).

```sh
# 1. upstash.com → Create database (Redis, region ap-south-1, free) → copy the rediss:// URL
# 2. from the repo root, with a finished build (engine: python -m wismo serve --build, or npm run build in both packages)
npx vercel@latest login
npx vercel@latest link                                   # create the project; accept the detected FastAPI preset
npx vercel@latest env add GEMINI_API_KEY production      # paste when prompted; never in a file
npx vercel@latest env add REDIS_URL production           # the rediss:// URL (or add Upstash from the Vercel Marketplace, which sets KV_URL)
npx vercel@latest env add GEMINI_MODEL production        # gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite
npx vercel@latest deploy --prod
```

`SITE_URL` defaults to the production domain Vercel assigns (`VERCEL_PROJECT_PRODUCTION_URL`); set it only for a custom domain. The upload includes the finished `apps/web/dist` and `packages/cierto-js/dist`, so `deploy/vercel/build.sh` skips the Node build; a Git-connected project (no dist in the repo) builds both on Vercel. Upstash's free plan counts every command, and one demo viewer costs roughly 100 commands a minute while the demo page polls, so the free allowance covers dozens of demo hours a month, not thousands.

### Cloud Run (needs `gcloud` logged in and a project with billing)

```sh
PROJECT_ID=my-project REGION=asia-south1 SITE_URL=https://cierto.example ./deploy/cloudrun/deploy.sh
# prompts (hidden) for GEMINI_API_KEY and REDIS_URL (Upstash: rediss://default:<token>@<host>.upstash.io:6379),
# or reads them from the environment; secrets go to Secret Manager over stdin.
```

The script enables the APIs, creates the Artifact Registry repo and a runtime service account with access to just the two secrets, builds with Cloud Build (`.gcloudignore` keeps the upload small), renders `deploy/cloudrun/service.yaml` (max 4 instances with Redis, 1 without), deploys with `gcloud run services replace`, allows public access and prints the URL and `/readyz`.

After deploying: `curl -sI $URL/demos | grep -iE 'x-served-by|strict-transport|content-security'`, `curl -s $URL/robots.txt`, and in Cloud Logging filter `jsonPayload.waf:*` to see what the WAF blocked.

## Optional: Cloud Armor

For edge filtering (OWASP rules, adaptive protection, rate-based bans before traffic reaches an instance), put a global external Application Load Balancer in front of Cloud Run with a serverless NEG and attach a Cloud Armor policy. It costs roughly $18/month for the load balancer's forwarding rule plus Cloud Armor Standard ($5/policy, $1/rule per month, $0.75 per million requests). Then set the service's ingress to `internal-and-cloud-load-balancing` and `TRUSTED_PROXY_HOPS=2` (the load balancer adds its own entry to `X-Forwarded-For`).

```sh
gcloud compute network-endpoint-groups create cierto-neg --region=$REGION --network-endpoint-type=serverless --cloud-run-service=cierto
gcloud compute backend-services create cierto-be --global --load-balancing-scheme=EXTERNAL_MANAGED
gcloud compute backend-services add-backend cierto-be --global --network-endpoint-group=cierto-neg --network-endpoint-group-region=$REGION
gcloud compute security-policies create cierto-armor
gcloud compute security-policies rules create 1000 --security-policy=cierto-armor --action=deny-403 \
  --expression="evaluatePreconfiguredWaf('sqli-v33-stable') || evaluatePreconfiguredWaf('xss-v33-stable')"
gcloud compute security-policies rules create 2000 --security-policy=cierto-armor --src-ip-ranges='*' \
  --action=rate-based-ban --rate-limit-threshold-count=600 --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600 --conform-action=allow --exceed-action=deny-429 --enforce-on-key=IP
gcloud compute backend-services update cierto-be --global --security-policy=cierto-armor
# then: URL map, managed certificate, target HTTPS proxy, forwarding rule; point DNS at its IP
gcloud run services update cierto --region=$REGION --ingress=internal-and-cloud-load-balancing \
  --update-env-vars=TRUSTED_PROXY_HOPS=2
```

The app-level WAF stays on: it knows the routes (which endpoints spend model calls) and shares its counters with the LLM budget.

## Configuration

Every variable, with its default, is in `engine/.env.example`. The ones that matter in production: `REDIS_URL`, `SITE_URL`, `GEMINI_API_KEY`, `TRUSTED_PROXY_HOPS`, `LOG_FORMAT=json`, `LLM_DAILY_BUDGET`. The image sets `PORT=8080`, `TRUSTED_PROXY_HOPS=1`, `FORWARDED_ALLOW_IPS=*`, `LOG_FORMAT=json` and `CIERTO_ENV=dev` (the public SDK sandbox and `/v1/dev/*` stay on; `CIERTO_ENV=live` turns them off).
