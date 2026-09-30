"""Paths and config loading. Everything brand- or category-specific lives in YAML."""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[1]                      # D:\Wismo
DATA = ROOT / "data"
REVIEWS = DATA / "reviews"                 # data/reviews/<brand>/<source>.jsonl
CLASSIFIED = DATA / "classified"           # data/classified/<brand>.jsonl
DOCS = ROOT / "docs" / "research"          # generated reports
VALIDATION = PKG / "validation"            # hand labels + metrics snapshots

BRANDS_FILE = PKG / "brands.yaml"
TAXONOMY_FILE = PKG / "taxonomy.yaml"


def _merge(base: dict, override: dict | None) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_brands() -> dict:
    raw = yaml.safe_load(BRANDS_FILE.read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {})
    brands = {}
    for key, b in raw["brands"].items():
        b = dict(b)
        b["key"] = key
        srcs = {}
        for name, cfg in (b.get("sources") or {}).items():
            # null means "no page exists / deliberately not configured"
            srcs[name] = None if cfg is None else _merge(defaults.get(name, {}), cfg)
        b["sources"] = srcs
        b["politeness"] = _merge(defaults.get("politeness", {}), b.get("politeness"))
        brands[key] = b
    return brands


def load_taxonomy() -> dict:
    return yaml.safe_load(TAXONOMY_FILE.read_text(encoding="utf-8"))


def brand_dir(brand: str) -> Path:
    d = REVIEWS / brand
    d.mkdir(parents=True, exist_ok=True)
    return d
