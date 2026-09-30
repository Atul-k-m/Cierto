"""Hand-validation of the classifier.

1. `sample` draws a seeded, stratified random sample per brand: by default 75% from rows
   the classifier calls WISMO (so every top category gets enough predicted positives to
   estimate precision) and 25% from rows it calls non-WISMO (to see what it misses).
   Curated rows are excluded (their text is partly a researcher's paraphrase).
2. A human reads each row and writes validation/labels_<tag>_<brand>.jsonl:
     {"id": ..., "wismo": true|false, "categories": [...true category ids...], "note": "..."}
3. `validate` re-classifies those rows with the current taxonomy and reports, per
   category, precision = correct predictions / predictions (with n), plus the WISMO
   flag's precision and the share of sampled "non-WISMO" rows that were really WISMO.
"""
from __future__ import annotations

import json
import random
import zlib
from collections import Counter

from .classify import Classifier
from .config import VALIDATION
from .store import load_reviews, read_jsonl, write_jsonl


def _seed(seed: int, brand: str, tag: str) -> int:
    return seed ^ zlib.crc32(f"{brand}:{tag}".encode())


def draw_sample(brand: str, n: int = 60, seed: int = 20260930, tag: str = "A",
                positives: float = 0.75, neg_pool: str = "all") -> str:
    """neg_pool='all': predicted-non-WISMO rows of any rating; 'low': only 1-2 star app reviews
    and complaint posts (where missed WISMO would actually hide)."""
    clf = Classifier()
    rows = [r for r in load_reviews(brand) if r.get("kind") != "curated" and len(r["text"]) >= 15]
    taken = set()
    for p in VALIDATION.glob(f"sample_*_{brand}.jsonl"):
        taken |= {x["id"] for x in read_jsonl(p)}
    rows = [r for r in rows if r["id"] not in taken]
    rows.sort(key=lambda r: r["id"])
    rng = random.Random(_seed(seed, brand, tag))
    pos = [r for r in rows if clf.classify(r["text"])["wismo"]]
    neg = [r for r in rows if not clf.classify(r["text"])["wismo"]]
    if neg_pool == "low":
        neg = [r for r in neg if r.get("rating") in (1, 2) or r.get("kind") == "complaint_site"]
    k_pos = min(len(pos), round(n * positives))
    k_neg = min(len(neg), n - k_pos)
    pick = rng.sample(pos, k_pos) + rng.sample(neg, k_neg)
    out = []
    for r in pick:
        res = clf.classify(r["text"])
        out.append({"id": r["id"], "source": r["source"], "rating": r.get("rating"), "date": r.get("date"),
                    "stratum": "pred_wismo" if res["wismo"] else "pred_non_wismo",
                    "text": r["text"], "pred_categories": res["categories"], "matches": res["matches"]})
    path = VALIDATION / f"sample_{tag}_{brand}.jsonl"
    write_jsonl(path, out)
    meta = {"brand": brand, "tag": tag, "seed": seed, "n": len(out), "neg_pool": neg_pool, "pos_pool": len(pos),
            "neg_pool_size": len(neg), "k_pos": k_pos, "k_neg": k_neg}
    (VALIDATION / f"sample_{tag}_{brand}.meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return f"{path} ({k_pos} predicted-WISMO + {k_neg} predicted-non-WISMO from pools {len(pos)}/{len(neg)})"


def score(brand: str, tag: str = "A", clf: Classifier | None = None) -> dict:
    clf = clf or Classifier()
    sample = {x["id"]: x for x in read_jsonl(VALIDATION / f"sample_{tag}_{brand}.jsonl")}
    labels = {x["id"]: x for x in read_jsonl(VALIDATION / f"labels_{tag}_{brand}.jsonl")}
    ids = [i for i in sample if i in labels]
    pred_n, tp, gold_n = Counter(), Counter(), Counter()
    w = Counter()
    for i in ids:
        res = clf.classify(sample[i]["text"])
        pred = set(res["categories"]) - {"other_non_wismo"}
        gold = set(labels[i].get("categories") or [])
        for c in pred:
            pred_n[c] += 1
            tp[c] += c in gold
        for c in gold:
            gold_n[c] += 1
        gw, pw = bool(labels[i]["wismo"]), res["wismo"]
        w["tp"] += gw and pw
        w["fp"] += pw and not gw
        w["fn"] += gw and not pw
        w["tn"] += (not gw) and (not pw)
        w[f"stratum_{sample[i]['stratum']}"] += 1
        w[f"stratum_{sample[i]['stratum']}_gold_wismo"] += gw
        w["fn_neg"] += gw and not pw and sample[i]["stratum"] == "pred_non_wismo"
    cats = {}
    for c in sorted(set(pred_n) | set(gold_n), key=lambda c: -pred_n[c]):
        cats[c] = {"predicted": pred_n[c], "correct": tp[c],
                   "precision": round(tp[c] / pred_n[c], 3) if pred_n[c] else None,
                   "gold": gold_n[c], "in_sample_recall": round(tp[c] / gold_n[c], 3) if gold_n[c] else None}
    wp = w["tp"] + w["fp"]
    neg_n = w["stratum_pred_non_wismo"]
    return {"brand": brand, "tag": tag, "taxonomy_version": clf.version, "n_labelled": len(ids),
            "wismo_flag": {"precision": round(w["tp"] / wp, 3) if wp else None, "predicted": wp,
                           "correct": w["tp"], "false_negatives_all": w["fn"],
                           "in_sample_recall": round(w["tp"] / (w["tp"] + w["fn"]), 3) if w["tp"] + w["fn"] else None,
                           "missed_in_negative_stratum": w["fn_neg"],
                           "negative_stratum_n": neg_n,
                           "negative_stratum_miss_rate": round(w["fn_neg"] / neg_n, 3) if neg_n else None},
            "categories": cats}


def evaluate(brand: str, tag: str = "A", save: str | None = None, taxonomy: str | None = None) -> str:
    clf = None
    if taxonomy:  # score a frozen snapshot, e.g. validation/taxonomy_v1.yaml
        import yaml
        from pathlib import Path
        clf = Classifier(yaml.safe_load(Path(taxonomy).read_text(encoding="utf-8")))
    m = score(brand, tag, clf)
    if save:
        (VALIDATION / f"metrics_{save}_{tag}_{brand}.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    lines = [f"[validate] {brand} tag={tag} taxonomy v{m['taxonomy_version']} labelled={m['n_labelled']}",
             f"  WISMO flag precision {m['wismo_flag']['precision']} ({m['wismo_flag']['correct']}/{m['wismo_flag']['predicted']}); "
             f"missed in negative stratum {m['wismo_flag']['missed_in_negative_stratum']}/{m['wismo_flag']['negative_stratum_n']}"]
    for c, v in m["categories"].items():
        lines.append(f"  {c:28s} precision {v['precision']!s:>5} ({v['correct']}/{v['predicted']})  "
                     f"gold {v['gold']} in-sample recall {v['in_sample_recall']}")
    return "\n".join(lines)
