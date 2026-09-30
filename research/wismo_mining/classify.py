"""Deterministic, explainable multi-label classifier over taxonomy.yaml.

Every label carries the phrase that triggered it and the index of the pattern, so any
number in a report can be traced back to text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import load_taxonomy
from .store import classified_path, load_reviews, write_jsonl

_MACRO = re.compile(r"\{([A-Z_]+)\}")


@dataclass
class Category:
    id: str
    label: str
    group: str
    wismo: bool
    patterns: list = field(default_factory=list)
    exclude: list = field(default_factory=list)
    suppressed_by: list = field(default_factory=list)
    derived: bool = False
    raw: dict = field(default_factory=dict)


class Classifier:
    def __init__(self, taxonomy: dict | None = None):
        tax = taxonomy or load_taxonomy()
        self.version = tax.get("version", 1)
        self.vocab = tax.get("vocab", {})
        self.norm = [(re.compile(rf"\b{re.escape(k)}\b"), v) for k, v in (tax.get("normalize") or {}).items()]
        self.strip_quotes = bool(tax.get("strip_quotes", False))
        self.categories: list[Category] = []
        for c in tax["categories"]:
            self.categories.append(Category(
                id=c["id"], label=c["label"], group=c.get("group", ""), wismo=bool(c.get("wismo")),
                patterns=[self._compile(p) for p in c.get("patterns") or []],
                exclude=[self._compile(p) for p in c.get("exclude") or []],
                suppressed_by=c.get("suppressed_by") or [], derived=bool(c.get("derived")), raw=c))
        self.by_id = {c.id: c for c in self.categories}
        self.hypotheses = tax.get("hypotheses") or []

    def _compile(self, pattern: str) -> re.Pattern:
        expanded = _MACRO.sub(lambda m: self.vocab[m.group(1)], pattern)
        return re.compile(expanded, re.IGNORECASE)

    def normalize(self, text: str) -> str:
        t = (text or "").lower()
        t = re.sub(r"[‘’‛ʼ`´]", "'", t)
        t = t.replace("'", "")
        if self.strip_quotes:                                         # quoted statuses: shows "delivered"
            t = re.sub(r"[\"“”«»*]", " ", t)
        t = re.sub(r"\s*[\r\n]+\s*", ". ", t)
        t = re.sub(r"(\d)\s*(minutes|minute|mins|min|hrs|hr|hours|hour)\b", r"\1 \2", t)
        for rx, rep in self.norm:
            t = rx.sub(rep, t)
        return re.sub(r"\s+", " ", t).strip()

    def classify(self, text: str) -> dict:
        t = self.normalize(text)
        hits: dict[str, list] = {}
        for c in self.categories:
            if c.derived:
                continue
            spans = [m.span() for rx in c.exclude for m in rx.finditer(t)]
            found = []
            for i, rx in enumerate(c.patterns):
                for m in rx.finditer(t):
                    s, e = m.span()
                    if s == e or any(s < xe and xs < e for xs, xe in spans):
                        continue
                    found.append({"p": i, "m": m.group(0)[:120]})
                    break
            if found:
                hits[c.id] = found
        for cid in list(hits):
            if any(s in hits for s in self.by_id[cid].suppressed_by):
                hits.pop(cid)
        wismo = any(self.by_id[cid].wismo for cid in hits)
        cats = [c.id for c in self.categories if c.id in hits]
        if not wismo:
            cats.append("other_non_wismo")
        return {"wismo": wismo, "categories": cats,
                "matches": {k: [h["m"] for h in v] for k, v in hits.items()},
                "pattern_ids": {k: [h["p"] for h in v] for k, v in hits.items()}}


def classify_rows(rows: list[dict], clf: Classifier | None = None) -> list[dict]:
    clf = clf or Classifier()
    out = []
    for r in rows:
        res = clf.classify(r["text"])
        out.append({"id": r["id"], "brand": r["brand"], "source": r["source"], "kind": r.get("kind"),
                    "date": r.get("date"), "rating": r.get("rating"), "lang": r.get("lang"),
                    "pull": r.get("pull"), **res, "taxonomy_version": clf.version})
    return out


def classify_brand(brand: str) -> tuple[int, int]:
    rows = load_reviews(brand)
    out = classify_rows(rows)
    write_jsonl(classified_path(brand), out)
    return len(out), sum(r["wismo"] for r in out)
