"""Aggregations shared by the brand and compare reports.

Samples are kept apart on purpose:
  unbiased  - app-store rows from the all-ratings pulls (Play 'newest', Apple 'mostrecent').
              The only sample used for "share of all reviews".
  low       - app-store rows rated 1-2 stars, from any pull (the low-star pulls deepen the window).
  complaint - complaint-board posts (every row is a complaint by construction).
  curated   - the hand-researched Smytten dataset (never used for shares of reviews).
"""
from __future__ import annotations

import math
import re
import zlib
from collections import Counter
from datetime import date

from .classify import Classifier
from .config import VALIDATION, load_brands
from .store import classified_path, load_manifest, load_reviews, read_jsonl

UNBIASED_PULLS = {"newest", "mostrecent"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def pct(k: int, n: int, ci: bool = False) -> str:
    if not n:
        return "–"
    s = f"{100 * k / n:.1f}%"
    if ci:
        lo, hi = wilson(k, n)
        s += f" ({100 * lo:.1f}–{100 * hi:.1f})"
    return s


class BrandData:
    def __init__(self, brand: str, clf: Classifier | None = None):
        self.brand = brand
        self.cfg = load_brands()[brand]
        self.clf = clf or Classifier()
        reviews = {r["id"]: r for r in load_reviews(brand)}
        self.rows = []
        for c in read_jsonl(classified_path(brand)):
            r = reviews.get(c["id"])
            if r is not None:
                self.rows.append({**r, **c})
        self.manifest = load_manifest(brand)
        self.cats = [c for c in self.clf.categories]
        self.label = {c.id: c.label for c in self.cats}
        self.group = {c.id: c.group for c in self.cats}
        # hand labels (all tags): used to prefer verified quotes and never show a known-wrong one
        self.gold = {}
        for p in VALIDATION.glob(f"labels_*_{brand}.jsonl"):
            for x in read_jsonl(p):
                self.gold[x["id"]] = set(x.get("categories") or [])

    # ---- samples ---------------------------------------------------------
    @property
    def unbiased(self):
        return [r for r in self.rows if r["kind"] == "app_review" and set(r.get("pull") or []) & UNBIASED_PULLS]

    @property
    def low(self):
        return [r for r in self.rows if r["kind"] == "app_review" and r.get("rating") in (1, 2)]

    @property
    def app_all(self):
        return [r for r in self.rows if r["kind"] == "app_review"]

    @property
    def complaint(self):
        return [r for r in self.rows if r["kind"] == "complaint_site"]

    @property
    def curated(self):
        return [r for r in self.rows if r["kind"] == "curated"]

    @staticmethod
    def wismo(rows):
        return [r for r in rows if r["wismo"]]

    @staticmethod
    def count(rows, cat):
        return sum(cat in r["categories"] for r in rows)

    def ranked_categories(self, rows, groups=("wismo_core",)):
        cnt = Counter(c for r in rows for c in r["categories"])
        return [c.id for c in sorted((c for c in self.cats if c.group in groups and not c.derived),
                                     key=lambda c: -cnt[c.id])]

    # ---- sources ---------------------------------------------------------
    def source_table(self):
        out = []
        by_src = Counter(r["source"] for r in self.rows)
        order = ["google_play", "app_store", "consumercomplaints", "manual_research", "trustpilot", "mouthshut", "reddit"]
        for src, m in sorted(self.manifest.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99):
            rows = [r for r in self.rows if r["source"] == src]
            dates = sorted(r["date"] for r in rows if r.get("date"))
            out.append({"source": src, "status": m["status"], "detail": m.get("detail", ""),
                        "rows": by_src.get(src, 0), "kind": rows[0]["kind"] if rows else "",
                        "date_min": dates[0] if dates else "", "date_max": dates[-1] if dates else "",
                        "wismo": sum(r["wismo"] for r in rows),
                        "low": sum(r.get("rating") in (1, 2) for r in rows)})
        return out

    # ---- time coverage ---------------------------------------------------
    def play_star_coverage(self) -> dict[int, str]:
        """Earliest date from which Google Play rows of each star rating are complete.
        Every pull is newest-first and contiguous to 'now', so coverage for star s starts
        at the earliest date among pulls that include s."""
        gp = [r for r in self.rows if r["source"] == "google_play"]
        starts = {}
        for s in range(1, 6):
            cands = []
            newest = [r["date"] for r in gp if "newest" in r["pull"]]
            if newest:
                cands.append(min(newest))
            lows = [r["date"] for r in gp if f"low_{s}" in r["pull"]]
            if lows:
                cands.append(min(lows))
            if cands:
                starts[s] = min(cands)
        return starts

    def monthly(self):
        """Google Play only (one consistent source). Returns (all_rows_by_month, low_by_month)
        each as list of (month, rows, partial_flag)."""
        gp = [r for r in self.rows if r["source"] == "google_play"]
        cov = self.play_star_coverage()
        newest = [r for r in gp if "newest" in r["pull"]]
        out_all, out_low = [], []
        if newest:
            start = min(r["date"] for r in newest)
            months = sorted({r["date"][:7] for r in newest})
            for m in months:
                rows = [r for r in newest if r["date"][:7] == m]
                out_all.append((m, rows, start[:7] == m))
        if 1 in cov and 2 in cov:
            low_start = max(cov[1], cov[2])     # both star levels complete from here
            low = [r for r in gp if r.get("rating") in (1, 2) and r["date"] >= low_start]
            for m in sorted({r["date"][:7] for r in low}):
                rows = [r for r in low if r["date"][:7] == m]
                out_low.append((m, rows, low_start[:7] == m))
        return out_all, out_low

    # ---- co-occurrence ---------------------------------------------------
    def cooccurrence(self, rows, cats):
        n = len(rows)
        single = Counter(c for r in rows for c in r["categories"])
        pairs = Counter()
        for r in rows:
            cs = [c for c in r["categories"] if c in cats]
            for i, a in enumerate(cs):
                for b in cs[i + 1:]:
                    pairs[tuple(sorted((a, b)))] += 1
        out = []
        for (a, b), k in pairs.items():
            pa, pb = single[a] / n, single[b] / n
            out.append({"a": a, "b": b, "n_ab": k, "n_a": single[a], "n_b": single[b],
                        "p_b_given_a": k / single[a], "p_a_given_b": k / single[b],
                        "lift": (k / n) / (pa * pb) if pa and pb else 0})
        return sorted(out, key=lambda x: -x["n_ab"]), single, n

    # ---- quotes ----------------------------------------------------------
    def quotes(self, cat: str, k: int = 4, wismo_only: bool = False) -> list[dict]:
        pool = []
        for r in self.rows:
            if cat not in r["categories"] or (wismo_only and not r["wismo"]):
                continue
            if r["id"] in self.gold and cat not in self.gold[r["id"]]:
                continue            # hand-check said this label is wrong: never quote it
            if r["kind"] == "curated":
                q = r.get("quote") or ""
                if not q or cat not in self.clf.classify(q)["categories"]:
                    continue
                text = q
            elif r["kind"] == "app_review" and r.get("rating") not in (1, 2, 3):
                continue
            else:
                text = r["text"]
            if len(text) < 30:
                continue
            ex = excerpt(text, r["matches"].get(cat, []), self.clf)
            if not ex:
                continue
            verified = r["id"] in self.gold
            pool.append({**r, "excerpt": ex, "verified": verified,
                         "_rank": (0 if verified else 1, zlib.crc32(f"{r['id']}|{cat}".encode()))})
        pool.sort(key=lambda r: r["_rank"])
        # round-robin across sources so one source cannot fill every slot
        by_src: dict[str, list] = {}
        for r in pool:
            by_src.setdefault(r["source"], []).append(r)
        picked, srcs = [], sorted(by_src, key=lambda s: -len(by_src[s]))
        while len(picked) < k and any(by_src.values()):
            for s in srcs:
                if by_src[s] and len(picked) < k:
                    picked.append(by_src[s].pop(0))
        return picked


_SENT = re.compile(r"(?<=[.!?])\s+|\n+")
_DIGITS = re.compile(r"(?:\+?\d[\d\s-]{6,}\d)")
_EMAIL = re.compile(r"\S+@\S+\.\S+")


def mask(s: str) -> str:
    s = re.sub(r"\s+", " ", s)            # one line, so markdown blockquotes stay intact
    return _DIGITS.sub("[number]", _EMAIL.sub("[email]", s))


def excerpt(text: str, phrases: list[str], clf: Classifier, limit: int = 340) -> str | None:
    """Verbatim excerpt of `text` around the sentence containing a matched phrase.
    Cuts are marked with an ellipsis; long digit strings and emails are masked."""
    text = text.strip()
    if len(text) <= limit:
        return mask(text)
    sents = [s for s in _SENT.split(text) if s.strip()]
    norm = [clf.normalize(s) for s in sents]
    idx = next((i for i, s in enumerate(norm) if any(p[:25] in s for p in phrases)), None)
    if idx is None:
        # phrase spans sentences: fall back to the joined text around the first word
        idx = 0
    out, i, j = sents[idx], idx, idx
    while True:
        grew = False
        if i > 0 and len(sents[i - 1]) + len(out) < limit:
            i -= 1
            out = sents[i] + " " + out
            grew = True
        if j < len(sents) - 1 and len(sents[j + 1]) + len(out) < limit:
            j += 1
            out = out + " " + sents[j]
            grew = True
        if not grew:
            break
    if len(out) > limit + 120:
        out = out[: limit + 120].rsplit(" ", 1)[0]
        j = len(sents)  # force trailing ellipsis
    return mask(("… " if i > 0 else "") + out + (" …" if j < len(sents) - 1 else ""))


def today() -> str:
    return date.today().isoformat()
