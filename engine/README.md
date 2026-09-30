# Cierto engine (`wismo`)

Cierto's order-truth engine (Python; the package keeps its internal name, `wismo`). See `../docs/02-architecture.md`.

| Module | Role |
|---|---|
| `events.py`, `taxonomy.py` | Canonical event model; status taxonomy mapped to ONDC states |
| `store/` | Event log port; Postgres (RLS, append-only) and in-memory adapters |
| `projection.py` | What is actually known about an order: per-source views, conflicts, proof state |
| `commitments.py`, `profiles.py` | Promises and deadlines per vertical (parcel / quick) |
| `detectors.py` | Named rules: exceptions and checks (including `rider_stalled` and `address_mismatch`) |
| `engine.py`, `clock.py`, `runner.py` | Ingest → project → detect → schedule, on a virtual clock |
| `resolver.py` | The AI resolver: trust score, policy-gated remedies, steps, English/Hinglish messages, optional LLM rephrase |
| `cases.py` | The resolution desk: writes decisions to the log, schedules follow-ups, executes and approves remedies |
| `view.py` | The order view: state, tone, `cause` (why, in the shopper's locale), promises, clocks, actions, resolution |
| `ask.py` | Grounded answers to a shopper's question: intent rules, English/Hinglish templates from the view only, staleness, optional guarded Claude rewording |
| `sdk.py`, `webhooks.py` | The SDK server API (keys, sessions, ingestion, config, simulate, remedies) and Standard Webhooks signing |
| `api.py` | FastAPI app ("Cierto API"): demo sessions (incl. `ask`, `case`, webhooks, approve), the SDK API, the `/sdk/cierto.js` bundle (`/sdk/pakka.js` still works), `/healthz` and `/readyz`, the web build |
| `sessions.py`, `shared.py` | Stateless instances: demo sessions and SDK tenants as append-only op logs in a shared store (memory, or Redis with `REDIS_URL`), materialized and replayed on demand; model outputs recorded on the op |
| `waf.py` | App-level WAF: client IP from `X-Forwarded-For`, request hygiene, rate limits, the daily LLM budget, security headers, JSON access logs |
| `web.py` | The prerendered site: canonical URLs without trailing slashes, a real 404, `__SITE_URL__`, precompressed assets, ETags and cache headers |
| `coverage/` | Complaint-to-timeline generator, healthy orders, coverage report |

## Setup

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -e ".[dev]"            # tests: Postgres (pgserver), Redis client, fakeredis
uv pip install --python .venv/Scripts/python.exe -e ".[llm]"      # optional: Claude rewords resolver messages and answers when ANTHROPIC_API_KEY is set
```

Postgres runs embedded via `pgserver` (no Docker). The first start initialises a data directory in `.pgdata/` and takes ~20 s.

## Run

```sh
.venv/Scripts/python.exe -m wismo replay ../scenarios/IC-213360.json             # run a scenario through the engine (in memory)
.venv/Scripts/python.exe -m wismo replay ../scenarios/VX-07.json --postgres       # same, written to the local Postgres log
.venv/Scripts/python.exe -m wismo coverage                                        # replay all complaints + healthy orders; writes docs/reports/phase1-coverage.md
.venv/Scripts/python.exe -m wismo serve --build                                  # API + SDK (/sdk/cierto.js) + web app on :8787; keys at /v1/dev/keys
.venv/Scripts/python.exe -m wismo serve --no-build --host 0.0.0.0 --port 8080    # production mode ($PORT works too); see ../docs/deploy.md
.venv/Scripts/python.exe -m pytest -q                                             # tests (Postgres tests use their own temporary database)
```

Set `WISMO_PGDATA` to put the local database elsewhere. `CIERTO_DEV_SEED` changes the derived test keys; `CIERTO_ENV=live` turns off the dev endpoints; `CIERTO_SDK_DIST` points `/sdk/*` at another build.

Deploying behind a load balancer (Cloud Run, or Caddy + Redis locally), the WAF limits and every environment variable: `../docs/deploy.md` and `.env.example`. The runtime needs no Postgres: install `-e ".[redis]"` for production, `-e ".[postgres]"` for `replay --postgres`.
