---
title: Built by
summary: Cierto is a working proof of concept, built end to end as an engineering and product exercise.
---

Cierto started as a research question: what do Smytten's shoppers actually complain about? I collected 93 distinct public complaints from 2025–26, categorised them, and found that the biggest problem wasn't tracking. It was **a courier's “Delivered” that nobody could prove, and a support loop that couldn't act on it**.

Everything on this site is real and runs locally from one command:

- **An order-truth engine** in Python: an append-only event log with provenance, derived delivery proof, commitments and clocks, and 17 detectors, with 61+ tests.
- **A replay harness** that turns public complaints into timelines and measures what the engine catches and how early, including the miss and the in-sample caveat.
- **An AI resolver** that decides the remedy under the host's policy, deterministically, with the language model limited to explaining the decision.
- **An SDK**: a Web Component with a token-based theme contract, a headless view model, a server events API and signed webhooks.
- **Three host replicas**, Smytten, Zomato and Swish, labelled as concept demos and not affiliated, showing the same engine in three very different order screens.

## What I'd want you to judge

- **Problem sizing from evidence**, before any code (`research/`, `docs/00-product-brief.md`).
- **Decisions written down**, including what was cut and why (`docs/decision-log.md`, `docs/adr/`).
- **Honest measurement**: the coverage report states its own limits.
- **End-to-end ownership**, from research through engine, SDK and API to the product site you're reading.

## What it isn't

- **No real brand data.** It is not integrated with any real brand. Smytten, Zomato and Swish don't expose order data to third parties, and nothing here uses their data.
- **Some numbers are scenarios.** Numbers marked *Scenario* come from demo timelines; numbers marked *Replay* come from the complaint replay.
