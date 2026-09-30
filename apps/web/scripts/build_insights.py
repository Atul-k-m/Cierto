"""Turn the review-mining reports (docs/research/wismo-*.md) into the JSON the site's charts read.

Run: python apps/web/scripts/build_insights.py   (after `python -m wismo_mining run`)
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs" / "research"
OUT = ROOT / "apps" / "web" / "src" / "site" / "data" / "insights.json"
BRANDS = ["smytten", "swish", "zomato"]


def tables(md: str):
    """Yield (heading, rows) for every markdown table, rows as lists of cell strings."""
    heading, rows, out = "", [], []
    for line in md.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("# ").strip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set(":- "):
                continue
            rows.append(cells)
        elif rows:
            out.append((heading, rows)); rows = []
    if rows:
        out.append((heading, rows))
    return out


def pct(s: str) -> float | None:
    m = re.search(r"(-?\d+(?:\.\d+)?)%", s)
    return float(m.group(1)) if m else None


def num(s: str) -> int | None:
    m = re.search(r"\d[\d,]*", s)
    return int(m.group(0).replace(",", "")) if m else None


def quotes(md: str, limit=3):
    """Verbatim quotes per category from section 7."""
    sec = md.split("## 7.", 1)[-1].split("## 8.", 1)[0]
    out = {}
    for block in re.split(r"\n### ", sec)[1:]:
        title, body = block.split("\n", 1)
        qs = []
        for m in re.finditer(r"> (.+?)\n>\n> — (.+?)\n", body):
            text, meta = m.group(1).strip(), m.group(2)
            link = re.search(r"\[([^\]]+)\]\((https?://[^)]+)\)", meta)
            qs.append({"text": text if len(text) < 260 else text[:257].rsplit(" ", 1)[0] + "…",
                       "meta": re.sub(r"\s*·\s*\[.*", "", meta).strip(),
                       "id": link.group(1) if link else None, "url": link.group(2) if link else None})
            if len(qs) >= limit:
                break
        out[title.strip()] = qs
    return out


def brand(slug: str) -> dict:
    md = (DOCS / f"wismo-{slug}.md").read_text(encoding="utf-8")
    head = md.split("## 1.", 1)[0]
    d = {"slug": slug, "headline": [re.sub(r"\*\*", "", l[2:]).strip() for l in head.splitlines() if l.startswith("- ")]}
    for heading, rows in tables(md):
        h = heading.lower()
        if h.startswith("4. every category"):
            hdr = rows[0]
            col = lambda key: next(i for i, c in enumerate(hdr) if c.startswith(key))
            iw, il, ia = col("% WISMO"), col("% 1–2"), col("% all")
            d["categories"] = [{"name": r[0], "group": r[1], "all": pct(r[ia]), "wismo": pct(r[iw]), "low": pct(r[il])} for r in rows[1:]]
        if h.startswith("5. trend") and "1–2★ reviews" in " ".join(rows[0]):
            d["trend"] = [{"month": r[0], "n": num(r[1]), "wismo": pct(r[2])} for r in rows[1:]]
        if h.startswith("1. what was collected"):
            d["sources"] = rows
    d["quotes"] = quotes(md)
    return d


def compare() -> dict:
    md = (DOCS / "wismo-compare.md").read_text(encoding="utf-8")
    out = {}
    for heading, rows in tables(md):
        h = heading.lower()
        if h.startswith("headline numbers"):
            out["headline"] = [{"brand": r[0], "delivery": r[1], "reviews": num(r[2]), "wismo_all": pct(r[3]),
                                "low_n": num(r[4]), "wismo_low": pct(r[5]), "posts": num(r[6]), "wismo_posts": pct(r[7])} for r in rows[1:]]
        if h.startswith("the eight hypotheses"):
            out["hypotheses"] = [{"name": r[0], "values": [pct(c) for c in r[1:4]], "verdicts": [c.split("·")[-1].strip() for c in r[1:4]]} for r in rows[1:]]
        if h.startswith("category mix"):
            out["mix"] = [{"name": r[0], "group": r[1], "wismo": [pct(c.split("/")[0]) for c in r[2:5]], "low": [pct(c.split("/")[1]) for c in r[2:5]]} for r in rows[1:]]
        if h.startswith("where wismo and support failure meet"):
            out["support"] = [{"brand": r[0], "pool": num(r[1]), "also_support": pct(r[2]), "dnr_support": pct(r[3]), "late_support": pct(r[4])} for r in rows[1:]]
        if h.startswith("how far to trust"):
            out["precision"] = [{"brand": r[0], "v2": pct(r[2])} for r in rows[1:]]
    return out


if __name__ == "__main__":
    data = {"compare": compare(), "brands": {b: brand(b) for b in BRANDS}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", OUT, {b: len(v.get("categories", [])) for b, v in data["brands"].items()})
