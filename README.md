# Cierto: intelligent WISMO (proof of concept)

Cierto is an order-truth engine and SDK that any shopping or delivery app can plug into. It treats a courier's "Delivered" as a **claim** until there is proof, catches late, stuck and falsely-closed orders before the customer has to ask, and shows the truth inside the host app's own screens.

Built from **93 public complaints about Smytten** (2025–26), plus quick-commerce complaints about Swish, Swiggy and Zomato. Every demo scenario cites the complaints it came from.

## Run the demo

One command, one port (Python 3.11 and Node 20+; first run: see engine/README.md for setup):

```sh
cd engine && .venv/Scripts/python.exe -m wismo serve        # add --build after changing the web app
```

Open http://localhost:8787. Press **Courier marks delivered, no OTP** and watch Smytten, Zomato and Swish each admit the delivery is unproven. Answer "No" in one of them and read what the engine noticed in the right-hand feed. The same demo session holds one order for each of six WISMO causes (rider stopped, traffic, batched drop, address pin mismatch, silent courier, unproven delivery), and `POST /v1/demo/sessions/{sid}/orders/{key}/ask` answers "where is my order?" for any of them from the order's own data.

The three host apps are **concept replicas**, labelled as such and not affiliated with the brands: none of them exposes customer order data to third parties (see `docs/02-architecture.md` §8).

## What's here

| Path | What |
|---|---|
| `docs/00-product-brief.md` | Problem from evidence, users, scope and cut list, metrics |
| `docs/01-design-brief.md` | Design direction: host look-alikes + the platform's own "cloud edge" world |
| `docs/02-architecture.md`, `docs/adr/` | System design, interoperability, decisions |
| `docs/03-roadmap.md` | Phases and iterations |
| `docs/decision-log.md` | What was decided, cut and learned in each iteration |
| `docs/reports/phase1-coverage.md` | The engine replayed against every complaint: coverage, lead time, false alarms |
| `engine/` | Python engine (package `wismo`): event log, projection, commitments, detectors, resolver, grounded answers, API |
| `packages/cierto-js/` | The browser SDK, `@cierto/js`: `Cierto.init`, the `<cierto-order>` element, a headless client and a React wrapper |
| `docs/sdk/` | SDK docs: quickstart, integration guides, API, configuration and webhook references |
| `apps/web/` | The widget source (`<cierto-order>`, with `<wismo-order>` and `<pakka-order>` as aliases), three host replicas, the site |
| `research/`, `data/` | Complaint dataset and its JSON export |
| `scenarios/` | Complaint-derived timelines replayed by the engine |
| `Dockerfile`, `deploy/`, `docs/deploy.md` | One image; Cloud Run service and deploy script; Caddy + Redis + three replicas for a local load-balanced run |
