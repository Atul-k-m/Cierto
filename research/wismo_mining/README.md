# wismo_mining

Measures how often real shopper reviews complain about WISMO ("where is my order": status, ETA, delays,
missing parcels, date changes) and which WISMO pains dominate, per brand. It is rule-based and
deterministic: every label keeps the phrase that triggered it.

```
collect (one module per source) → data/reviews/<brand>/<source>.jsonl + _manifest.json
classify (taxonomy.yaml)         → data/classified/<brand>.jsonl
report / compare                 → docs/research/wismo-<brand>.md, docs/research/wismo-compare.md
```

## Setup and run

```sh
cd research
uv venv .venv --python 3.11
uv pip install --python .venv/Scripts/python.exe -r wismo_mining/requirements.txt

.venv/Scripts/python -m wismo_mining run --brands smytten,swish,zomato   # collect + classify + report + compare
.venv/Scripts/python -m wismo_mining run --brands zomato --skip-collect  # reuse collected data
.venv/Scripts/python -m wismo_mining collect --brands swish --sources app_store
.venv/Scripts/python -m wismo_mining classify --brands all
.venv/Scripts/python -m wismo_mining report --brand zomato
.venv/Scripts/python -m wismo_mining compare --brands smytten,swish,zomato
```

A full collection makes roughly 150 polite requests per brand and takes a few minutes.

## Files

| File | What |
|---|---|
| `brands.yaml` | Brand registry: store ids, complaint-site slugs, per-brand notes, pull sizes, politeness |
| `taxonomy.yaml` | WISMO categories: definition, regex patterns (English + Hinglish), excludes, hypothesis mapping |
| `collectors/` | `google_play`, `app_store` (Apple RSS), `consumercomplaints`, `trustpilot`, `mouthshut`, `reddit`, `manual_research` (`data/complaints.json`) |
| `classify.py` | Normalise text, match patterns, apply span-level excludes, derive the WISMO flag |
| `stats.py`, `report.py` | Samples, Wilson intervals, monthly coverage, co-occurrence, verbatim excerpts, markdown |
| `validate.py`, `validation/` | Seeded samples, hand labels, metrics snapshots, frozen taxonomy versions |

Row shape (every collector): `{id, brand, source, date, rating, text, url, lang}` plus `kind`
(`app_review` | `complaint_site` | `curated`) and optional extras (`pull`, `title`, ...). Reviewer names are
not stored.

## Add a brand (config only)

1. Find the ids: Google Play package (`google_play_scraper.search`), Apple id (`https://itunes.apple.com/search?term=<name>&country=in&entity=software`), and any consumercomplaints.in brand slug.
2. Add a block under `brands:` in `brands.yaml`:

   ```yaml
   blinkit:
     name: Blinkit
     vertical: "10-minute grocery"
     delivery_model: hyperlocal
     sources:
       google_play: {app_id: com.grofers.customerapp}
       app_store: {app_id: 960335206}
       consumercomplaints: null        # null = no page; shown as "not configured" in the report
       trustpilot: {domain: blinkit.com}
       mouthshut: null
       reddit: {query: blinkit}
     notes:
       - "Anything a reader must know about this brand's data."
   ```

3. `python -m wismo_mining run --brands blinkit` (and add it to `compare`).

## Add a category (config only)

Add a block to `categories:` in `taxonomy.yaml` with `id`, `label`, `group` (`wismo_core` |
`cross_cutting` | `adjacent`), `wismo` (true only if it alone makes a review WISMO), `definition`, `patterns`,
optional `exclude` and `suppressed_by`. Macros such as `{RIDER}`, `{ORDER}`, `{NEG}` and `{HINEG}` come from
`vocab`. Text is lower-cased with apostrophes removed (`didn't` → `didnt`), so write patterns that way. To
make it a hypothesis on the scorecard, add it under `hypotheses:`. Then re-run `classify` and `report`.

## Add a source

Write `collectors/<name>.py` exposing `collect(brand, cfg, http) -> (rows, detail)` (build rows with
`store.make_row`, raise `http.Blocked` when refused), register it in `collectors/__init__.py`, give it a `kind`
in `store.KINDS`, and add `sources.<name>` entries in `brands.yaml`.

## Validation workflow

```sh
python -m wismo_mining sample --brands zomato --n 60 --tag A            # 75% predicted-WISMO, 25% rest
#   read validation/sample_A_zomato.jsonl, write validation/labels_A_zomato.jsonl:
#   {"id": "...", "wismo": true, "categories": ["eta_slip_late", ...], "note": "..."}
python -m wismo_mining validate --brands zomato --tag A --save v1
#   fix patterns once, freeze a copy as validation/taxonomy_v2.yaml, then draw a fresh holdout:
python -m wismo_mining sample --brands zomato --n 40 --tag B --neg-pool low
python -m wismo_mining validate --brands zomato --tag B --save v2
python -m wismo_mining validate --brands zomato --tag A --taxonomy wismo_mining/validation/taxonomy_v1.yaml --save v1
```

Reports read `metrics_v1_A_*`, `metrics_v2_A_*` and `metrics_v2_B_*`. Samples exclude rows used by
earlier samples. Any pattern change after the holdout needs a new holdout before the numbers are quoted.
`validation/taxonomy_v1.yaml` and `taxonomy_v2.yaml` are the exact versions that were scored.

Known v2 misses from the holdout (candidates for v3, with a new holdout): tracker complaints phrased as
"shows wrong delivery time" or "time shown is not correct"; generic "poor customer support"; "shown as
delivered" without a nearby negation; ETA false hits from "taking too much charges", "took forever to
refund" and waits for support; "rain" used as a fee.

## Politeness and skips

Honest user agent, 2.5 s between web requests and 1.5 s between store-API pages. robots.txt is fetched with
that user agent and honoured. No logins, no bot-protection workarounds. As of 2026-09-30: Trustpilot (robots
`Disallow: /` for all agents, HTTP 403), MouthShut (robots disallows ClaudeBot), Reddit (robots `Disallow: /`,
API needs OAuth) are recorded as skipped in `_manifest.json` and in every report.

## Optional LLM pass

Not implemented. The classifier does not depend on an API key. A second-opinion pass (for example Claude
labelling the same validation samples) would slot in next to `validate.py`.
