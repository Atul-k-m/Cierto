"""Export the complaint rows in research.py to data/complaints.json.

research.py builds an Excel workbook; this reuses its data definitions (everything
before the workbook build) so later phases (replay engine, demo scenarios, agent
evals) can load the same dataset and cite complaint IDs.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "data" / "complaints.json"

src = (HERE / "research.py").read_text(encoding="utf-8")
ns = {}
exec(src.split("IN_END = D(")[0], ns)
CATS, STAGE, JOURNEY, grp, sev = ns["CATS"], ns["STAGE"], ns["JOURNEY"], ns["grp"], ns["sev"]

FLAGS = {"S": "support_contacted", "R": "refund_involved", "D": "delivery_involved",
         "X": "support_failure", "T": "templated_text"}


def in_window(row):
    (cid, date, source, url, author, cat, sec, fl, evidence, fragment, summary,
     dup_group, dup_status, stage_override, date_verified) = row
    stage = stage_override or STAGE[cat]
    return {
        "id": cid, "window": "in-window", "brand": "smytten", "date": date,
        "source": source, "url": url, "author": author,
        "category_id": cat, "category": CATS[cat], "category_group": grp(cat),
        "secondary": [CATS[int(x)] for x in sec.split(",")] if sec else [],
        "funnel_stage": stage, "journey": JOURNEY[stage],
        "severity": sev(cat, fl),
        "flags": {name: ch in fl for ch, name in FLAGS.items()},
        "evidence_strength": evidence, "quote": fragment, "summary": summary,
        "duplicate_group": dup_group or None, "duplicate": dup_status == "duplicate",
        "date_verified": date_verified,
    }


def legacy(row):
    cid, date, source, url, author, cat, summary, date_verified = row
    return {
        "id": cid, "window": "legacy", "brand": "smytten", "date": date,
        "source": source, "url": url, "author": author,
        "category_id": cat, "category": CATS[cat], "category_group": grp(cat),
        "funnel_stage": STAGE[cat], "journey": JOURNEY[STAGE[cat]],
        "summary": summary,
        "duplicate": "-dup" in cid or cid == "TP-L1",
        "date_verified": date_verified,
    }


rows = [in_window(r) for r in ns["R"]] + [legacy(r) for r in ns["L"]]
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps({"categories": CATS, "complaints": rows}, indent=1, ensure_ascii=False),
               encoding="utf-8")
unique = [r for r in rows if r["window"] == "in-window" and not r["duplicate"]]
print(f"wrote {len(rows)} rows ({len(unique)} unique in-window) to {OUT}")
