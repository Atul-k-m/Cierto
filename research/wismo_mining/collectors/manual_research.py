"""The hand-researched complaint dataset (data/complaints.json, built by research/research.py).

It is a curated set of complaints, so it is never used for "share of all reviews".
Text for classification = verbatim fragment (`quote`, in-window rows only) + the
researcher's summary (a paraphrase). Only the verbatim fragment is ever quoted.
Rows the dataset itself marks as duplicates are dropped.
"""
from __future__ import annotations

import json

from ..config import ROOT
from ..store import make_row


def collect(brand: dict, cfg: dict, http=None) -> tuple[list[dict], str]:
    data = json.loads((ROOT / cfg["path"]).read_text(encoding="utf-8"))
    rows, dups = [], 0
    for c in data["complaints"]:
        if c.get("brand") != brand["key"]:
            continue
        if c.get("duplicate"):
            dups += 1
            continue
        quote = c.get("quote") or ""
        summary = c.get("summary") or ""
        rows.append(make_row(
            id=f"mr:{c['id']}", brand=brand["key"], source="manual_research",
            date=c.get("date"), rating=None,
            text=(f"{quote}. {summary}" if quote else summary),
            url=c.get("url"), lang=None, quote=quote or None,
            origin=c.get("source"), window=c.get("window"),
            manual_category=c.get("category"), manual_secondary=c.get("secondary") or [],
        ))
    return rows, f"{cfg['path']}: {len(rows)} rows kept, {dups} marked duplicate dropped"
