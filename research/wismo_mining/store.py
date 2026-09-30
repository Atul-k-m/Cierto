"""JSONL storage, the normalized row shape, and the per-brand collection manifest."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .config import CLASSIFIED, brand_dir

# Required keys of every normalized review row. Collectors may add extra keys
# (title, pull, kind, ...); the classifier and reports rely only on these plus `kind`.
ROW_KEYS = ("id", "brand", "source", "date", "rating", "text", "url", "lang")

# Source kinds drive how numbers are reported:
#   app_review     - app-store reviews: every rating, the closest thing to a population sample
#   complaint_site - complaint boards: every row is a complaint by construction
#   curated        - hand-picked complaint dataset: useful for mix, never for "share of reviews"
KINDS = {"google_play": "app_review", "app_store": "app_review",
         "consumercomplaints": "complaint_site", "trustpilot": "complaint_site",
         "mouthshut": "complaint_site", "reddit": "forum", "manual_research": "curated"}

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_HINGLISH = re.compile(
    r"\b(?:nahi|nahin|nhi|hai|hain|kya|kar|karo|kiya|mera|meri|mujhe|bhi|aur|tha|thi|gaya|gya|"
    r"raha|rha|hota|hoga|kyu|kyun|kab|kaha|kahan|aaya|aya|mila|abhi|bahut|bohot|wala|wale|diya|dia)\b")


def detect_lang(text: str) -> str:
    """Cheap script/lexicon heuristic: 'hi' (Devanagari), 'hi-Latn' (romanised Hindi), or 'en'."""
    if _DEVANAGARI.search(text or ""):
        return "hi"
    if len(_HINGLISH.findall((text or "").lower())) >= 2:
        return "hi-Latn"
    return "en"


def make_row(**kw) -> dict:
    row = {k: kw.pop(k, None) for k in ROW_KEYS}
    row["text"] = (row["text"] or "").strip()
    if not row["lang"]:
        row["lang"] = detect_lang(row["text"])
    row["kind"] = KINDS.get(row["source"], "other")
    row.update({k: v for k, v in kw.items() if v is not None})
    return row


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def source_path(brand: str, source: str) -> Path:
    return brand_dir(brand) / f"{source}.jsonl"


def load_reviews(brand: str) -> list[dict]:
    """All collected rows for a brand, de-duplicated by id (first file wins)."""
    seen, out = set(), []
    for p in sorted(brand_dir(brand).glob("*.jsonl")):
        for r in read_jsonl(p):
            if r["id"] not in seen:
                seen.add(r["id"])
                out.append(r)
    return out


def classified_path(brand: str) -> Path:
    CLASSIFIED.mkdir(parents=True, exist_ok=True)
    return CLASSIFIED / f"{brand}.jsonl"


# ---- manifest: what each collector did, including skips and failures ----------

def manifest_path(brand: str) -> Path:
    return brand_dir(brand) / "_manifest.json"


def load_manifest(brand: str) -> dict:
    p = manifest_path(brand)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def record(brand: str, source: str, status: str, detail: str, **extra) -> None:
    """status: ok | skipped | failed | not_configured."""
    m = load_manifest(brand)
    m[source] = {"status": status, "detail": detail,
                 "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **extra}
    manifest_path(brand).write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding="utf-8")
