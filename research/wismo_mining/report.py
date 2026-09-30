"""Markdown reports: docs/research/wismo-<brand>.md and docs/research/wismo-compare.md.

All numbers are computed from data/classified + data/reviews at generation time; nothing
is typed in by hand. Quotes are verbatim excerpts (long digit runs and emails masked).
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date

from .classify import Classifier
from .config import DOCS, VALIDATION, load_brands
from .stats import BrandData, pct, today, wilson

GROUP_NAME = {"wismo_core": "WISMO", "cross_cutting": "cross-cutting", "adjacent": "adjacent", "derived": "derived"}
SUPPORT_CATS = ("support_unreachable_loop", "vague_support_answer")
MANUAL_MAP = {  # research.py categories -> taxonomy ids that should fire
    "Delivery delay": {"eta_slip_late", "order_not_delivered"},   # research.py: 'ordered X, still undelivered Y'
    "Order not received": {"order_not_delivered", "delivered_not_received"},
    "Marked delivered but not received": {"delivered_not_received"},
    "Tracking/status issue": {"tracking_stale_wrong"},
    "Courier/delivery attempt issue": {"order_not_delivered", "address_location", "rider_behaviour", "rider_stuck"},
    "Lost/returned shipment": {"order_not_delivered"},
    "Missing item": {"partial_missing_item"},
    "Partial shipment": {"partial_missing_item", "multiple_batched_orders"},
    "Cancellation": {"cancelled_by_platform"},
    "Refund delay": {"refund_stuck"},
    "Refund not received": {"refund_stuck"},
    "Incorrect/partial refund": {"refund_stuck"},
    "Customer-support accessibility": {"support_unreachable_loop"},
    "Customer-support resolution failure": {"support_unreachable_loop", "vague_support_answer"},
}
MANUAL_WISMO = {"Delivery delay", "Order not received", "Marked delivered but not received",
                 "Tracking/status issue", "Courier/delivery attempt issue", "Lost/returned shipment"}


def table(header: list[str], rows: list[list], align: str | None = None) -> str:
    align = align or ("l" + "r" * (len(header) - 1))
    sep = ["---:" if a == "r" else ":---" for a in align]
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def load_metrics(brand: str) -> dict:
    out = {}
    for p in sorted(VALIDATION.glob(f"metrics_*_{brand}.json")):
        name = p.stem[len("metrics_"):-len(f"_{brand}")]        # e.g. v1_A
        out[name] = json.loads(p.read_text(encoding="utf-8"))
    return out


def _pr(pred: int, correct: int, gold: int) -> str:
    p = f"P {100 * correct / pred:.0f}% ({correct}/{pred})" if pred else "P –"
    r = f"R {100 * correct / gold:.0f}% ({correct}/{gold})" if gold else "R –"
    return f"{p} · {r}"


def best_precision(metrics: dict, cat: str) -> str:
    """Holdout precision/recall (v2 on fresh sample B); falls back to the tuned sample A, flagged."""
    for key, suffix in (("v2_B", ""), ("v2_A", " (tuned sample)")):
        m = metrics.get(key)
        v = m and m["categories"].get(cat)
        if v and (v["predicted"] or v["gold"]):
            return _pr(v["predicted"], v["correct"], v["gold"]) + suffix
    return "–"


def hyp_check(metrics: dict, cats: list[str]) -> str:
    m = metrics.get("v2_B")
    if not m:
        return "–"
    pred = sum(m["categories"].get(c, {}).get("predicted", 0) for c in cats)
    corr = sum(m["categories"].get(c, {}).get("correct", 0) for c in cats)
    gold = sum(m["categories"].get(c, {}).get("gold", 0) for c in cats)
    return _pr(pred, corr, gold) if (pred or gold) else "–"


def hyp_share(bd: BrandData, rows: list, hyp: dict) -> int:
    cats = set(hyp["categories"])
    return sum(bool(cats & set(r["categories"])) for r in rows)


def verdict(share: float) -> str:
    if share >= 0.15:
        return "strong"
    if share >= 0.05:
        return "moderate"
    if share >= 0.02:
        return "weak"
    return "rare"


# --------------------------------------------------------------------- brand report

def write_brand_report(brand: str) -> str:
    clf = Classifier()
    bd = BrandData(brand, clf)
    cfg = bd.cfg
    metrics = load_metrics(brand)
    unb, low, comp, cur, app_all = bd.unbiased, bd.low, bd.complaint, bd.curated, bd.app_all
    w_unb, w_low, w_comp = bd.wismo(unb), bd.wismo(low), bd.wismo(comp)
    core_rank = bd.ranked_categories(w_unb + w_low + w_comp)
    L = []
    L.append(f"# WISMO complaint mining: {cfg['name']}\n")
    L.append(f"_{cfg['vertical']} · delivery model: {cfg['delivery_model']} · generated {today()} by "
             f"`python -m wismo_mining report --brand {brand}` · taxonomy v{clf.version}_\n")
    L.append("WISMO = any shopper complaint about order status, location, ETA, delay, a missing parcel or a "
             "date change. Numbers come from a deterministic keyword/regex classifier "
             "(`research/wismo_mining/taxonomy.yaml`); every label stores the phrase that triggered it. "
             "Categories are multi-label, so shares do not add up to 100%.\n")

    # headline
    k, n = len(w_unb), len(unb)
    kl, nl = len(w_low), len(low)
    L.append("## Headline\n")
    head_rank = bd.ranked_categories(w_unb)
    top3 = ", ".join(f"{bd.label[c].lower()} ({pct(bd.count(w_unb, c), len(w_unb))})" for c in head_rank[:3])
    lo, hi = wilson(k, n)
    L.append(f"- **{pct(k, n)}** of app-store reviews (all ratings, n={n:,}) are WISMO-related "
             f"(95% CI {100 * lo:.1f}–{100 * hi:.1f}%).")
    L.append(f"- Among **1–2★** app reviews (n={nl:,}) the share is **{pct(kl, nl)}**.")
    if comp:
        L.append(f"- Among complaint-board posts (n={len(comp)}) it is **{pct(len(w_comp), len(comp))}**.")
    L.append(f"- Largest WISMO issues among WISMO reviews: {top3}.")
    sup = sum(any(c in r["categories"] for c in SUPPORT_CATS) for r in w_unb + w_low)
    L.append(f"- {pct(sup, len(w_unb + w_low))} of WISMO app reviews (all pulls) also report a support "
             "failure (unreachable, bot loop or a vague/scripted answer).")
    mb = metrics.get("v2_B")
    if mb:
        wf = mb["wismo_flag"]
        L.append(f"- Classifier check on a fresh hand-labelled holdout (n={mb['n_labelled']}): WISMO-flag precision "
                 f"{100 * (wf['precision'] or 0):.0f}% ({wf['correct']}/{wf['predicted']}); "
                 f"{wf['missed_in_negative_stratum']} of {wf['negative_stratum_n']} sampled 1–2★/complaint rows "
                 "it called non-WISMO were in fact WISMO, so WISMO shares are lower bounds (section 8).")
    L.append("")

    # sources
    L.append("## 1. What was collected\n")
    rows = []
    for s in bd.source_table():
        rng = f"{s['date_min']} → {s['date_max']}" if s["date_min"] else "–"
        rows.append([s["source"], s["status"], s["kind"] or "–", f"{s['rows']:,}", rng,
                     f"{s['low']:,}" if s["kind"] == "app_review" else "–", f"{s['wismo']:,}",
                     s["detail"].replace("|", "/")])
    L.append(table(["Source", "Status", "Kind", "Rows", "Date range", "1–2★", "WISMO", "Detail"], rows,
                   "lllrlrrl"))
    cov = bd.play_star_coverage()
    newest = [r["date"] for r in bd.rows if r["source"] == "google_play" and "newest" in r["pull"]]
    if newest:
        L.append(f"\nGoogle Play windows: all-ratings sample {min(newest)} → {max(newest)}; "
                 + "; ".join(f"{s}★ complete from {d}" for s, d in sorted(cov.items()) if s <= 2) + ".")
    langs = Counter(r.get("lang") for r in app_all)
    L.append(f"Detected language of app reviews: " + ", ".join(f"{k} {v:,}" for k, v in langs.most_common())
             + " (Play pulled with `lang=en`; `hi-Latn` = romanised Hindi/Hinglish).\n")

    # share by rating
    L.append("## 2. How much of the review stream is WISMO?\n")
    rows = []
    for label, sub in [("All ratings (unbiased app sample)", unb),
                       ("1★", [r for r in app_all if r.get("rating") == 1]),
                       ("2★", [r for r in app_all if r.get("rating") == 2]),
                       ("3★", [r for r in unb if r.get("rating") == 3]),
                       ("4–5★", [r for r in unb if r.get("rating") in (4, 5)])]:
        rows.append([label, f"{len(sub):,}", pct(len(bd.wismo(sub)), len(sub), True)])
    for src in ("google_play", "app_store"):
        sub = [r for r in unb if r["source"] == src]
        if sub:
            rows.append([f"… {src} only (all ratings)", f"{len(sub):,}", pct(len(bd.wismo(sub)), len(sub), True)])
    if comp:
        rows.append(["Complaint-board posts", f"{len(comp):,}", pct(len(w_comp), len(comp), True)])
    if cur:
        rows.append(["Curated complaints (manual research)", f"{len(cur):,}", pct(len(bd.wismo(cur)), len(cur), True)])
    L.append(table(["Sample", "n", "WISMO share (95% CI)"], rows))
    L.append("\n1★ and 2★ rows include the extra low-star pulls (longer window); 3★ and 4–5★ come from the "
             "all-ratings sample only.\n")

    # hypotheses
    L.append("## 3. Hypothesis scorecard\n")
    L.append("Share of WISMO reviews (all-ratings app sample) that mention each hypothesised pain, with the "
             "same measure among all 1–2★ reviews and complaint-board posts. Verdict thresholds (share of "
             "WISMO reviews): strong ≥15%, moderate 5–15%, weak 2–5%, rare <2%.\n")
    rows = []
    for h in clf.hypotheses:
        kh = hyp_share(bd, w_unb, h)
        lo, hi = wilson(kh, len(w_unb))
        rows.append([h["name"], ", ".join(f"`{c}`" for c in h["categories"]),
                     f"{pct(kh, len(w_unb))} ({100*lo:.0f}–{100*hi:.0f})",
                     pct(hyp_share(bd, w_low, h), len(w_low)),
                     pct(hyp_share(bd, low, h), len(low)),
                     pct(hyp_share(bd, comp, h), len(comp)) if comp else "–",
                     verdict(kh / len(w_unb)) if w_unb else "–", hyp_check(metrics, h["categories"])])
    L.append(table(["Hypothesis", "Categories", f"% of WISMO reviews (n={len(w_unb)})",
                    f"% of 1–2★ WISMO (n={len(w_low)})", f"% of all 1–2★ (n={len(low)})",
                    f"% of complaint posts (n={len(comp)})", "Verdict", "Classifier check (holdout)"],
                   rows, "llrrrrll"))
    L.append("\nClassifier check = precision (P) and recall (R) of the hypothesis categories on the fresh "
             "hand-labelled holdout (section 8). Low recall means the share is an undercount; tiny n means "
             "the check itself is rough.")
    L.append("")

    # categories
    L.append("## 4. Every category\n")
    rows = []
    order = core_rank + bd.ranked_categories(w_unb + w_low + w_comp, ("cross_cutting", "adjacent"))
    for c in order:
        rows.append([bd.label[c], GROUP_NAME[bd.group[c]],
                     pct(bd.count(unb, c), len(unb)), pct(bd.count(w_unb, c), len(w_unb)),
                     pct(bd.count(low, c), len(low)),
                     pct(bd.count(comp, c), len(comp)) if comp else "–",
                     pct(bd.count(cur, c), len(cur)) if cur else "–",
                     best_precision(metrics, c)])
    rows.append(["Other / non-WISMO", "derived", pct(len(unb) - len(w_unb), len(unb)), "–",
                 pct(len(low) - len(w_low), len(low)), pct(len(comp) - len(w_comp), len(comp)) if comp else "–",
                 pct(len(cur) - len(bd.wismo(cur)), len(cur)) if cur else "–", "–"])
    L.append(table(["Category", "Group", f"% all reviews (n={len(unb):,})", f"% WISMO reviews (n={len(w_unb)})",
                    f"% 1–2★ (n={len(low):,})", f"% complaint posts (n={len(comp)})",
                    f"% curated (n={len(cur)})", "Holdout precision · recall"], rows, "llrrrrrl"))
    L.append("\nCross-cutting and adjacent categories do not make a review WISMO on their own; they are "
             "counted so their overlap with WISMO can be measured (section 6).\n")

    # trend
    L.append("## 5. Trend by month (Google Play)\n")
    by_all, by_low = bd.monthly()
    if by_all:
        L.append("All-ratings sample (the newest-reviews pull):\n")
        rows = [[m + (" (partial)" if part else ""), f"{len(rs):,}", pct(len(bd.wismo(rs)), len(rs)),
                 "low n" if len(rs) < 30 else ""] for m, rs, part in by_all]
        L.append(table(["Month", "Reviews", "WISMO share", ""], rows))
    if by_low:
        tops = core_rank[:4]
        L.append("\n1–2★ reviews, months where both star levels are fully covered:\n")
        rows = []
        for m, rs, part in by_low:
            rows.append([m + (" (partial)" if part else ""), f"{len(rs):,}", pct(len(bd.wismo(rs)), len(rs))]
                        + [pct(bd.count(rs, c), len(rs)) for c in tops] + ["low n" if len(rs) < 30 else ""])
        L.append(table(["Month", "1–2★ reviews", "WISMO share"] + [bd.label[c] for c in tops] + [""], rows))
    L.append("\nThe current month is to date. Month-to-month moves under ~5 points on n<200 are within noise.\n")
    if comp:
        yrs = Counter(r["date"][:4] for r in comp)
        L.append("Complaint-board posts by year: " + ", ".join(
            f"{y}: {n} ({pct(len(bd.wismo([r for r in comp if r['date'][:4] == y])), n)} WISMO)"
            for y, n in sorted(yrs.items())) + ".\n")

    # co-occurrence
    L.append("## 6. Co-occurrence\n")
    pool = bd.wismo(app_all) + w_comp
    cats = [c.id for c in clf.categories if not c.derived]
    pairs, single, npool = bd.cooccurrence(pool, cats)
    L.append(f"Pool: all WISMO app reviews (any pull) plus WISMO complaint posts, n={npool:,}. "
             "P(B|A) = share of reviews with A that also mention B; lift >1 means they travel together "
             "more than chance.\n")
    focus = [("delivered_not_received", "support_unreachable_loop"), ("order_not_delivered", "support_unreachable_loop"),
             ("eta_slip_late", "support_unreachable_loop"), ("eta_slip_late", "vague_support_answer"),
             ("eta_slip_late", "cancelled_by_platform"), ("eta_slip_late", "proactive_comms_missing"),
             ("order_not_delivered", "refund_stuck"), ("multiple_batched_orders", "eta_slip_late"),
             ("rider_stuck", "eta_slip_late"), ("tracking_stale_wrong", "eta_slip_late"),
             ("address_location", "rider_behaviour"), ("traffic_weather_excuse", "eta_slip_late")]
    idx = {(p["a"], p["b"]): p for p in pairs}
    rows = []
    for a, b in focus:
        p = idx.get(tuple(sorted((a, b))))
        na = single.get(a, 0)
        if not na:
            continue
        nab = p["n_ab"] if p else 0
        base = single.get(b, 0) / npool if npool else 0
        lift = (nab / na) / base if base and na else 0
        rows.append([f"{bd.label[a]} → {bd.label[b]}", na, nab, pct(nab, na), pct(single.get(b, 0), npool),
                     f"{lift:.1f}×" if nab else "–"])
    L.append(table(["A → B", "n(A)", "n(A∧B)", "P(B|A)", "P(B) baseline", "Lift"], rows))
    L.append("\nMost frequent pairs overall:\n")
    rows = [[bd.label[p["a"]], bd.label[p["b"]], p["n_ab"], f"{p['lift']:.1f}×"] for p in pairs[:10]]
    L.append(table(["Category A", "Category B", "Both", "Lift"], rows, "llrr"))
    L.append("")

    # quotes
    L.append("## 7. What shoppers say (verbatim)\n")
    L.append("Excerpts are verbatim (line breaks collapsed); `…` marks a cut, and long numbers/emails are "
             "masked. Hand-checked rows are shown first, and rows the hand-check rejected for a category are "
             "never shown; the rest are a deterministic pseudo-random pick, so an occasional misfire can still "
             "appear. App Store links go to the app's review list (Apple has no per-review permalink); the id "
             "identifies the review.\n")
    quote_cats = [c for c in core_rank if single.get(c, 0) >= 3][:6] + list(SUPPORT_CATS)
    for c in quote_cats:
        qs = bd.quotes(c, k=4, wismo_only=c in SUPPORT_CATS)   # support quotes in a WISMO context
        if not qs:
            continue
        L.append(f"### {bd.label[c]}" + (" (WISMO reviews only)" if c in SUPPORT_CATS else "") + "\n")
        for q in qs:
            stars = f"{q['rating']}★ · " if q.get("rating") else ""
            src = q["source"] if q["kind"] != "curated" else f"manual research ({q.get('origin', '')})"
            chk = " · ✓ hand-checked" if q.get("verified") else ""
            L.append(f"> {q['excerpt']}\n>\n> — {stars}{src} · {q.get('date') or 'n.d.'} · "
                     f"[{q['id']}]({q['url']}){chk}\n")

    # validation
    L.append("## 8. Classifier validation\n")
    if metrics:
        L.append("Every sampled review was read in full and its true categories recorded "
                 "(`research/wismo_mining/validation/labels_*.jsonl`, with notes on judgement calls).\n")
        L.append("- **Sample A** (60 per brand, seeded random): 45 drawn from reviews the v1 classifier called "
                 "WISMO, 15 from the rest (any rating). Used to fix patterns once (v1 → v2), so v2-on-A is "
                 "optimistic.\n- **Sample B** (40 per brand, drawn after v2 was frozen, never used for tuning): "
                 "30 predicted-WISMO, 10 predicted-non-WISMO taken only from 1–2★ reviews and complaint posts, "
                 "where missed WISMO would hide. **v2 on B is the honest estimate.**\n")
        keys = [k for k in ("v1_A", "v2_A", "v2_B") if k in metrics]
        names = {"v1_A": "v1 on A (before fixes)", "v2_A": "v2 on A (tuned)", "v2_B": "v2 on B (holdout)"}
        wf = []
        for kname in keys:
            m = metrics[kname]["wismo_flag"]
            wf.append([names[kname], metrics[kname]["n_labelled"],
                       f"{100 * (m['precision'] or 0):.0f}% ({m['correct']}/{m['predicted']})",
                       f"{m['missed_in_negative_stratum']}/{m['negative_stratum_n']}"])
        L.append(table(["Run", "Labelled", "WISMO-flag precision",
                        "True WISMO among sampled predicted-non-WISMO"], wf))
        L.append("")
        allc = []
        for kname in keys:
            for c in metrics[kname]["categories"]:
                if c not in allc:
                    allc.append(c)
        last = metrics[keys[-1]]["categories"]
        allc.sort(key=lambda c: -((last.get(c) or {}).get("predicted") or 0))
        rows = []
        for c in allc:
            cells = []
            for kname in keys:
                v = metrics[kname]["categories"].get(c)
                cells.append(f"{100 * v['precision']:.0f}% ({v['correct']}/{v['predicted']})"
                             if v and v["predicted"] else "–")
            vb = (metrics.get("v2_B") or {"categories": {}})["categories"].get(c)
            cells.append(f"{100 * vb['correct'] / vb['gold']:.0f}% ({vb['correct']}/{vb['gold']})"
                         if vb and vb["gold"] else "–")
            rows.append([bd.label.get(c, c)] + cells)
        L.append(table(["Category"] + [f"Precision: {names[k]}" for k in keys] + ["Recall: v2 on B"], rows))
        L.append("\nSmall n per category means wide error bars (8/10 is compatible with ~50–95%). Recall on B is "
                 "measured within a WISMO-enriched sample, so treat it as indicative. Known v2 failure modes "
                 "seen on the holdout: tracker complaints phrased as 'shows wrong delivery time' / 'time shown "
                 "is not correct' are missed (tracker share is an undercount); generic 'poor customer support' "
                 "is not counted as support failure; 'taking too much charges' and 'took forever to refund' can "
                 "trip the ETA rule; 'rain' as a fee can trip the weather rule.\n")
    else:
        L.append("No hand-labelled sample yet (`python -m wismo_mining sample` then `validate`).\n")
    if cur:
        L.append("### Agreement with the manual Smytten research labels\n")
        L.append("The curated dataset carries a researcher's primary and secondary category per complaint. "
                 "Recall here = share of complaints with that manual label where the classifier fired a "
                 "matching category. Text is the verbatim fragment plus the researcher's summary.\n")
        rows = []
        for mc, ours in MANUAL_MAP.items():
            sub = [r for r in cur if r.get("manual_category") == mc or mc in (r.get("manual_secondary") or [])]
            if not sub:
                continue
            hit = sum(bool(ours & set(r["categories"])) for r in sub)
            rows.append([mc, ", ".join(f"`{o}`" for o in sorted(ours)), len(sub), pct(hit, len(sub))])
        L.append(table(["Manual category (primary or secondary)", "Expected taxonomy ids", "n", "Recall"], rows, "llrr"))
        mw = [r for r in cur if r.get("manual_category") in MANUAL_WISMO]
        L.append(f"\nManual primary category in the WISMO-core group (n={len(mw)}): classifier flags "
                 f"{pct(sum(r['wismo'] for r in mw), len(mw))} as WISMO.\n")

    # bias
    L.append("## 9. Sampling bias and limitations\n")
    notes = [
        "**Reviews are not contacts.** App-store reviews are written by a self-selected few, skew to "
        "extremes, and are shaped by in-app rating prompts (which inflate 5★). The WISMO share of reviews "
        "is not the WISMO share of support tickets or orders; it measures what hurts enough to be written "
        "about publicly.",
        "**Windows differ by source and brand** (section 1). Each Play pull is newest-first and capped, so "
        "high-volume apps get short windows. Shares are only comparable across brands as rough levels.",
        "**Low-star pulls** extend the 1–2★ window; they feed the 1–2★ columns only, never the "
        "'all reviews' denominator.",
        "**English only on Play** (`lang=en`): Devanagari-script reviews are largely absent; romanised "
        "Hindi is included and matched by Hinglish patterns, but coverage of it is thinner.",
        "**Apple RSS** returns at most 500 most-recent reviews and intermittently returns empty pages; "
        "gaps are listed in section 1.",
        "**Complaint boards are complaint-only by construction**, so their WISMO share is a mix measure, "
        "not a rate. Listing excerpts were expanded to full text where the post had its own page.",
        "**Rule-based classifier.** Precision is estimated from small hand-checked samples (section 8); "
        "recall is not fully measured (only the miss rate among sampled 'non-WISMO' rows). Short reviews "
        "('worst app', 'late') carry little signal, and sarcasm or negation outside the handled patterns "
        "can slip through. Shares should be read as ±a few points.",
        "**Duplicates across sources** (for example a curated App Store complaint that is also in the "
        "Apple feed) are not reconciled; the curated set is small and never pooled into shares of reviews.",
    ]
    skipped = [f"`{s}` ({m['status']}: {m['detail']})" for s, m in bd.manifest.items() if m["status"] != "ok"]
    if skipped:
        notes.append("**Sources not collected:** " + "; ".join(skipped) + ".")
    if cur:
        notes.append("**Curated Smytten dataset** (`data/complaints.json`): hand-picked complaints from "
                     "Trustpilot, Voxya, IndiaCustomerCare, MouthShut and the App Store (2019–2026). Its text "
                     "is partly a researcher's paraphrase; it is used for mix and as a cross-check, never "
                     "for shares of reviews. Only its verbatim fragments are quoted.")
    notes += [f"**Brand note:** {n}" for n in cfg.get("notes") or []]
    L += [f"- {n}" for n in notes]
    L.append("")
    DOCS.mkdir(parents=True, exist_ok=True)
    path = DOCS / f"wismo-{brand}.md"
    path.write_text("\n".join(L), encoding="utf-8")
    return str(path)


# --------------------------------------------------------------------- compare report

def write_compare_report(brands: list[str]) -> str:
    clf = Classifier()
    bds = {b: BrandData(b, clf) for b in brands}
    names = {b: bds[b].cfg["name"] for b in brands}
    L = [f"# WISMO complaint mining: {' vs '.join(names.values())}\n",
         f"_Generated {today()} by `python -m wismo_mining compare` · taxonomy v{clf.version} · per-brand detail in "
         + ", ".join(f"[wismo-{b}.md](wismo-{b}.md)" for b in brands) + "_\n"]

    # headline
    L.append("## Headline numbers\n")
    rows = []
    for b, bd in bds.items():
        unb, low, comp = bd.unbiased, bd.low, bd.complaint
        rows.append([names[b], bd.cfg["delivery_model"], f"{len(unb):,}", pct(len(bd.wismo(unb)), len(unb), True),
                     f"{len(low):,}", pct(len(bd.wismo(low)), len(low), True),
                     f"{len(comp)}" if comp else "–", pct(len(bd.wismo(comp)), len(comp)) if comp else "–"])
    L.append(table(["Brand", "Delivery", "App reviews (all ratings)", "WISMO share (95% CI)", "1–2★ reviews",
                    "WISMO share of 1–2★", "Complaint posts", "WISMO share"], rows, "llrrrrrr"))
    L.append("")

    # hypotheses
    L.append("## The eight hypotheses, measured\n")
    L.append("Cell = share of WISMO app reviews (all-ratings sample) that mention the pain · in brackets the "
             "share among 1–2★ WISMO reviews. Verdicts use the brand's all-ratings share: strong ≥15%, "
             "moderate 5–15%, weak 2–5%, rare <2%.\n")
    rows = []
    for h in clf.hypotheses:
        row = [h["name"]]
        for b, bd in bds.items():
            wu, wl = bd.wismo(bd.unbiased), bd.wismo(bd.low)
            k = hyp_share(bd, wu, h)
            row.append(f"{pct(k, len(wu))} ({pct(hyp_share(bd, wl, h), len(wl))}) · {verdict(k / len(wu)) if wu else '–'}")
        rows.append(row)
    L.append(table(["Hypothesis"] + [f"{names[b]} (n={len(bds[b].wismo(bds[b].unbiased))}/{len(bds[b].wismo(bds[b].low))})"
                                     for b in brands], rows, "l" + "r" * len(brands)))
    L.append("")

    # categories
    L.append("## Category mix among WISMO reviews\n")
    allcats = [c.id for c in clf.categories if not c.derived]
    rows = []
    for c in allcats:
        row = [bds[brands[0]].label[c], GROUP_NAME[bds[brands[0]].group[c]]]
        for b, bd in bds.items():
            wu, lw = bd.wismo(bd.unbiased), bd.low
            row.append(f"{pct(bd.count(wu, c), len(wu))} / {pct(bd.count(lw, c), len(lw))}")
        rows.append(row)
    L.append("Cell = % of WISMO reviews (all-ratings sample) / % of all 1–2★ reviews.\n")
    L.append(table(["Category", "Group"] + [names[b] for b in brands], rows, "ll" + "r" * len(brands)))
    L.append("")

    # support overlap
    L.append("## Where WISMO and support failure meet\n")
    rows = []
    for b, bd in bds.items():
        pool = bd.wismo(bd.app_all) + bd.wismo(bd.complaint)
        n = len(pool)
        sup = sum(any(c in r["categories"] for c in SUPPORT_CATS) for r in pool)
        dnr = [r for r in pool if "delivered_not_received" in r["categories"]]
        dnr_sup = sum(any(c in r["categories"] for c in SUPPORT_CATS) for r in dnr)
        late = [r for r in pool if "eta_slip_late" in r["categories"]]
        late_sup = sum(any(c in r["categories"] for c in SUPPORT_CATS) for r in late)
        pro = sum("proactive_comms_missing" in r["categories"] for r in pool)
        rows.append([names[b], n, pct(sup, n), f"{pct(dnr_sup, len(dnr))} (n={len(dnr)})",
                     f"{pct(late_sup, len(late))} (n={len(late)})", pct(pro, n)])
    L.append(table(["Brand", "WISMO pool", "…also support failure", "Delivered-not-received → support failure",
                    "Late → support failure", "…also 'nobody told me'"], rows))
    L.append("\nPool = WISMO app reviews from every pull plus WISMO complaint posts. Support failure = "
             "unreachable/bot loop or vague/scripted answer.\n")

    # classifier check
    L.append("## How far to trust the classifier\n")
    rows = []
    for b in brands:
        m = load_metrics(b)
        cells = [names[b]]
        for key in ("v1_A", "v2_B"):
            wf = (m.get(key) or {}).get("wismo_flag")
            cells.append(f"{100 * (wf['precision'] or 0):.0f}% ({wf['correct']}/{wf['predicted']})" if wf else "–")
        wf = (m.get("v2_B") or {}).get("wismo_flag")
        cells.append(f"{wf['missed_in_negative_stratum']}/{wf['negative_stratum_n']}" if wf else "–")
        rows.append(cells)
    L.append(table(["Brand", "WISMO-flag precision, v1 (sample A)", "WISMO-flag precision, v2 (holdout B)",
                    "Holdout: true WISMO among 1–2★ rows called non-WISMO"], rows))
    L.append("\nOne round of pattern fixes (v1 → v2) was made on sample A; sample B was drawn afterwards and "
             "never used for tuning. Per-category precision and recall are in each brand report (section 8).\n")

    # auto findings
    L.append("## Findings (computed)\n")
    L += [f"- {f}" for f in findings(bds, clf)]
    L.append("")

    # coverage + caveats
    L.append("## Data coverage\n")
    rows = []
    order = ["google_play", "app_store", "consumercomplaints", "manual_research", "trustpilot", "mouthshut", "reddit"]
    srcs = sorted({s for bd in bds.values() for s in bd.manifest}, key=lambda x: order.index(x) if x in order else 99)
    for s in srcs:
        row = [s]
        for b, bd in bds.items():
            m = bd.manifest.get(s)
            if not m:
                row.append("–")
            elif m["status"] == "ok":
                dates = sorted(r["date"] for r in bd.rows if r["source"] == s and r.get("date"))
                row.append(f"{m.get('rows', 0):,} ({dates[0][:7]} → {dates[-1][:7]})" if dates else f"{m.get('rows', 0)}")
            else:
                row.append(m["status"])
        rows.append(row)
    L.append(table(["Source"] + [names[b] for b in brands], rows, "l" + "l" * len(brands)))
    skipped, missing = {}, {}
    for b, bd in bds.items():
        for src, m in bd.manifest.items():
            if m["status"] in ("skipped", "failed"):
                skipped.setdefault(src, m["detail"])
            elif m["status"] == "not_configured":
                missing.setdefault(src, []).append(names[b])
    if skipped:
        L.append("\nNot collected: " + "; ".join(f"**{k}**: {v}" for k, v in skipped.items()) + ".")
    if missing:
        L.append("No brand page: " + "; ".join(f"{k} ({', '.join(v)})" for k, v in missing.items()) + ".")
    L.append("")
    L.append("## Read this before quoting a number\n")
    wins = []
    for b, bd in bds.items():
        d = sorted(r["date"] for r in bd.rows if r["source"] == "google_play" and "newest" in (r.get("pull") or []))
        if d:
            days = (date.fromisoformat(d[-1]) - date.fromisoformat(d[0])).days + 1
            wins.append(f"{names[b]} {days} days ({d[0]} → {d[-1]})")
    L += ["- App-store reviews over-represent angry and delighted shoppers; the WISMO share of reviews is not "
          "the share of tickets. It is a ranking of what hurts enough to be written down in public.",
          "- Windows are not aligned. The all-ratings Google Play sample covers: " + "; ".join(wins)
          + ". Treat cross-brand gaps of a few points as noise.",
          "- Categories come from a rule-based classifier with hand-checked precision (above, and section 8 of "
          "each brand report). Recall is only partly measured and is weakest for tracker and support "
          "complaints, so those shares are undercounts."]
    for b, bd in bds.items():
        L += [f"- {names[b]}: {n}" for n in bd.cfg.get("notes") or []]
    L.append("")
    DOCS.mkdir(parents=True, exist_ok=True)
    path = DOCS / "wismo-compare.md"
    path.write_text("\n".join(L), encoding="utf-8")
    return str(path)


def findings(bds: dict, clf: Classifier) -> list[str]:
    out = []
    names = {b: bd.cfg["name"] for b, bd in bds.items()}
    # 1. level
    lv = {b: (len(bd.wismo(bd.unbiased)), len(bd.unbiased), len(bd.wismo(bd.low)), len(bd.low)) for b, bd in bds.items()}
    out.append("WISMO is a minority of all reviews but a large block of angry ones: "
               + "; ".join(f"{names[b]} {pct(v[0], v[1])} of all vs {pct(v[2], v[3])} of 1–2★" for b, v in lv.items()) + ".")
    # 2. top issue per brand
    parts = []
    for b, bd in bds.items():
        wu = bd.wismo(bd.unbiased)
        rank = bd.ranked_categories(wu)
        if rank and wu:
            parts.append(f"{names[b]}: {bd.label[rank[0]].lower()} ({pct(bd.count(wu, rank[0]), len(wu))}), then "
                         f"{bd.label[rank[1]].lower()} ({pct(bd.count(wu, rank[1]), len(wu))})")
    out.append("Top WISMO issue among WISMO reviews — " + "; ".join(parts) + ".")
    # 3. hypotheses strong/weak everywhere
    strong, weak = [], []
    for h in clf.hypotheses:
        shares = []
        for b, bd in bds.items():
            wu = bd.wismo(bd.unbiased)
            shares.append(hyp_share(bd, wu, h) / len(wu) if wu else 0)
        if min(shares) >= 0.15:
            strong.append(h["name"])
        if max(shares) < 0.05:
            weak.append(h["name"])
    if strong:
        out.append("Hypotheses at ≥15% of WISMO reviews for every brand: " + "; ".join(strong) + ".")
    if weak:
        parts = []
        for name in weak:
            h = next(x for x in clf.hypotheses if x["name"] == name)
            corr = gold = 0
            for b in bds:
                mb = load_metrics(b).get("v2_B") or {"categories": {}}
                for c in h["categories"]:
                    v = mb["categories"].get(c) or {}
                    corr += v.get("correct", 0)
                    gold += v.get("gold", 0)
            parts.append(f"{name} (holdout recall {corr}/{gold}, so partly a detection gap)" if gold else name)
        out.append("Hypotheses under 5% of WISMO reviews for every brand (little explicit evidence in review "
                   "text, which does not mean the problem is absent): " + "; ".join(parts) + ".")
    # 4. biggest spread
    spread = []
    for h in clf.hypotheses:
        vals = {}
        for b, bd in bds.items():
            wu = bd.wismo(bd.unbiased)
            vals[b] = hyp_share(bd, wu, h) / len(wu) if wu else 0
        hi, lo = max(vals, key=vals.get), min(vals, key=vals.get)
        spread.append((vals[hi] - vals[lo], h["name"], hi, lo, vals))
    spread.sort(reverse=True)
    for d, name, hi, lo, vals in spread[:3]:
        out.append(f"Biggest brand gap — {name}: {names[hi]} {100 * vals[hi]:.0f}% vs {names[lo]} {100 * vals[lo]:.0f}% "
                   "of WISMO reviews.")
    # 5. support overlap
    parts = []
    for b, bd in bds.items():
        pool = bd.wismo(bd.app_all) + bd.wismo(bd.complaint)
        sup = sum(any(c in r["categories"] for c in SUPPORT_CATS) for r in pool)
        parts.append(f"{names[b]} {pct(sup, len(pool))}")
    out.append("Share of WISMO complaints (all pulls + complaint posts) that also describe a support failure: "
               + ", ".join(parts) + ".")
    return out
