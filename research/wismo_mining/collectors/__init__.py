"""Collector registry. One module per source; each exposes

    collect(brand: dict, cfg: dict, http: Polite) -> (rows, detail)

and raises http.Blocked when a source refuses us. To add a source: write the module,
register it here, and add a `sources.<name>` entry to brands.yaml.
"""
from __future__ import annotations

import traceback

from ..http import Blocked, Polite
from ..store import record, source_path, write_jsonl
from . import app_store, consumercomplaints, google_play, manual_research, mouthshut, reddit, trustpilot

REGISTRY = {
    "google_play": google_play,
    "app_store": app_store,
    "consumercomplaints": consumercomplaints,
    "trustpilot": trustpilot,
    "mouthshut": mouthshut,
    "reddit": reddit,
    "manual_research": manual_research,
}


def collect_brand(brand: dict, only: list[str] | None = None, log=print) -> None:
    pol = brand["politeness"]
    for name, mod in REGISTRY.items():
        if only and name not in only:
            continue
        if name not in brand["sources"]:
            continue                      # source not relevant to this brand at all
        cfg = brand["sources"][name]
        if cfg is None:
            record(brand["key"], name, "not_configured", "no page for this brand on this source")
            log(f"  {name:20s} not configured")
            continue
        http = Polite(pol["user_agent"], pol.get("sleep_s", 2.5))
        try:
            rows, detail = mod.collect(brand, cfg, http)
        except Blocked as e:
            record(brand["key"], name, "skipped", str(e), requests=http.requests_made)
            log(f"  {name:20s} SKIPPED: {e}")
            continue
        except Exception as e:  # never let one source kill the run; the report shows it
            record(brand["key"], name, "failed", f"{type(e).__name__}: {e}",
                   trace=traceback.format_exc(limit=3), requests=http.requests_made)
            log(f"  {name:20s} FAILED: {type(e).__name__}: {e}")
            continue
        write_jsonl(source_path(brand["key"], name), rows)
        dates = sorted(r["date"] for r in rows if r.get("date"))
        record(brand["key"], name, "ok", detail, rows=len(rows), requests=http.requests_made,
               date_min=dates[0] if dates else None, date_max=dates[-1] if dates else None)
        log(f"  {name:20s} ok: {len(rows)} rows ({detail})")
