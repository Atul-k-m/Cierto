"""Replay the complaint corpus and healthy orders through the engine; write the coverage report."""
import json
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from ..clock import VirtualClock
from ..detectors import CHECK, Finding
from ..engine import Engine
from ..events import AssertedBy, Event, EventType
from ..profiles import PARCEL, PROFILES
from ..runner import ingest_later
from ..store.memory import MemoryEventStore
from . import healthy
from .facts import extract
from .generate import TENANT, Case, build

# Findings that exist only because the customer said something.
CUSTOMER_DEPENDENT = {"delivery_disputed": "via_prompt", "support_silence": "after_contact", "repeat_contact": "after_contact"}
CATEGORY_GROUPS = {1: "WISMO core", 2: "WISMO core", 3: "WISMO core", 4: "WISMO core", 5: "WISMO core", 6: "WISMO core",
                   7: "Item issue", 8: "Item issue", 9: "Item issue", 10: "Item issue", 11: "Item issue", 12: "Item issue",
                   13: "Cancellation/refund", 14: "Cancellation/refund", 15: "Cancellation/refund", 16: "Cancellation/refund",
                   17: "Item issue", 18: "Support", 19: "Support", 20: "Payment"}


def simulate(arrivals: list[tuple[datetime, Event]], until: datetime, profile, truth: str | None
             ) -> list[tuple[datetime, Finding]]:
    clock = VirtualClock(arrivals[0][0])
    store = MemoryEventStore(received_at=clock.now)
    engine = Engine(store, clock, lambda _t: profile)
    fired: list[tuple[datetime, Finding]] = []

    def on_finding(tenant, order_ref, f: Finding, at: datetime) -> None:
        fired.append((at, f))
        if f.rule == "confirm_receipt" and truth:
            kind = EventType.CUSTOMER_RECEIPT_DISPUTED if truth == "not_received" else EventType.CUSTOMER_RECEIPT_CONFIRMED
            answer_at = at + timedelta(minutes=10 if profile.name == "quick" else 120)
            ingest_later(engine, answer_at, Event(
                event_id=f"{order_ref}:answer", tenant_id=tenant, order_ref=order_ref, type=kind,
                occurred_at=answer_at, asserted_by=AssertedBy.CUSTOMER, source_adapter="simulated_customer",
                data={"via": "engine_prompt"}))

    engine.listeners.append(on_finding)
    for at, event in arrivals:
        clock.advance_to(at)
        engine.ingest(event)
    clock.advance_to(until)
    return fired


@dataclass
class Result:
    complaint_id: str
    category_id: int
    category: str
    group: str
    date: str
    template: str
    stated_facts: list[str]
    status: str                    # caught | missed | needs_customer_report
    mode: str | None = None        # proactive | via_prompt | after_contact
    caught_by: str | None = None
    caught_message: str | None = None
    lead_time_hours: float | None = None
    timing_stated: bool = False
    all_exceptions_before_complaint: list[str] = field(default_factory=list)
    note: str = ""


def classify(case: Case, c: dict, fired: list[tuple[datetime, Finding]]) -> Result:
    before = [(at, f) for at, f in fired if at <= case.complaint_at and f.kind != CHECK]
    after = [(at, f) for at, f in fired if at > case.complaint_at and f.kind != CHECK]
    r = Result(case.complaint_id, case.category_id, c["category"], CATEGORY_GROUPS[case.category_id], c["date"],
               case.template, sorted(case.facts.stated - {"cancelled"}), "missed",
               all_exceptions_before_complaint=[f.rule for _, f in before], timing_stated=case.timing_stated)
    if case.expected == set() or case.template == "item_issue" and case.expected != "any":
        r.status = "needs_customer_report"
        r.note = "Item-level problem (wrong, missing, damaged). No delivery signal reveals it; the engine's job starts at the customer's report."
        return r
    matching = [(at, f) for at, f in before if case.expected == "any" or f.rule in case.expected]
    if matching:
        at, f = min(matching, key=lambda pair: pair[0])
        r.status, r.caught_by, r.caught_message = "caught", f.rule, f.message
        r.mode = CUSTOMER_DEPENDENT.get(f.rule, "proactive")
        r.lead_time_hours = round((case.complaint_at - at).total_seconds() / 3600, 1)
        return r
    late = [f.rule for _, f in after if case.expected == "any" or f.rule in case.expected]
    if case.template == "return_not_modelled":
        r.note = "A return after delivery; returns and reverse pickups aren't modelled in Phase 1."
    elif late:
        r.note = f"Detected only after the complaint was posted ({late[0]}): the complaint came before the engine's deadline."
    else:
        r.note = "No stated fact gives the engine a signal before the complaint."
    return r


def run_corpus(complaints: list[dict]) -> tuple[list[Result], dict]:
    results = []
    for c in complaints:
        case = build(c, extract(c))
        fired = simulate(case.arrivals, case.complaint_at, PARCEL, case.truth)
        results.append(classify(case, c, fired))
    return results, {}


def run_healthy(orders) -> dict:
    per_vertical: dict[str, Counter] = defaultdict(Counter)
    rules: Counter = Counter()
    for o in orders:
        fired = simulate(o.arrivals, o.until, PROFILES[o.vertical], o.truth)
        exceptions = [f for _, f in fired if f.kind != CHECK]
        checks = [f for _, f in fired if f.kind == CHECK]
        v = per_vertical[o.vertical]
        v["orders"] += 1
        v["with_false_alarm"] += bool(exceptions)
        v["prompted"] += bool(checks)
        rules.update(f.rule for f in exceptions)
    return {"per_vertical": {k: dict(v) for k, v in per_vertical.items()}, "false_alarm_rules": dict(rules)}


def summarise(results: list[Result], healthy_stats: dict) -> dict:
    detectable = [r for r in results if r.status != "needs_customer_report"]
    caught = [r for r in detectable if r.status == "caught"]
    leads = [r.lead_time_hours for r in caught if r.timing_stated]   # lead times on assumed timing are not evidence
    by_mode = Counter(r.mode for r in caught)
    by_cat = defaultdict(Counter)
    for r in results:
        by_cat[(r.category_id, r.category)][r.status] += 1
    total_orders = sum(v["orders"] for v in healthy_stats["per_vertical"].values())
    total_fa = sum(v["with_false_alarm"] for v in healthy_stats["per_vertical"].values())
    return {
        "complaints": len(results),
        "detectable": len(detectable),
        "caught": len(caught),
        "needs_customer_report": len(results) - len(detectable),
        "coverage_of_detectable": round(len(caught) / len(detectable), 3) if detectable else None,
        "by_mode": dict(by_mode),
        "lead_time_basis": f"{len(leads)} caught complaints with stated dates or durations",
        "lead_time_hours": {
            "median": statistics.median(leads) if leads else None,
            "p25": statistics.quantiles(leads, n=4)[0] if len(leads) >= 4 else None,
            "min": min(leads) if leads else None,
            "max": max(leads) if leads else None,
        },
        "proactive_median_lead_hours": statistics.median(pro) if (pro := [
            r.lead_time_hours for r in caught if r.mode == "proactive" and r.timing_stated]) else None,
        "by_category": {f"{cid}. {name}": dict(c) for (cid, name), c in sorted(by_cat.items())},
        "healthy": healthy_stats,
        "false_alarm_rate": round(total_fa / total_orders, 4) if total_orders else None,
    }


def _hours(h: float | None) -> str:
    if h is None:
        return "–"
    return f"{h / 24:.1f} d" if h >= 48 else f"{h:.0f} h"


def write_markdown(path: Path, results: list[Result], s: dict) -> None:
    lt = s["lead_time_hours"]
    hv = s["healthy"]["per_vertical"]
    lines = [
        "# Phase 1 coverage report",
        "",
        "*Generated by `python -m wismo coverage`. Do not edit by hand; rerun instead.*",
        "",
        "## What this measures",
        "",
        "Each of the unique 2025–2026 Smytten complaints in `data/complaints.json` is turned into an order timeline "
        "containing **only the facts the complaint states**; anything unstated takes the value that makes detection "
        "harder (tracking keeps moving, an out-for-delivery scan precedes every \"delivered\", proof is unknown rather "
        "than missing). The engine replays each timeline on a virtual clock up to the complaint's real posting time. "
        "A simulated customer only answers the engine's own \"did you get it?\" prompt, truthfully.",
        "",
        "**This measures rule coverage of the failure modes, not a real-world detection rate.** Two limits matter:",
        "",
        "- **In-sample.** The rules were written after reading these same complaints, so a high number shows the rules "
        "cover the failure modes seen here, not that they generalise. The honest out-of-sample tests are the quick-commerce "
        "complaints (Swish, Swiggy, Zomato) and, later, real carrier data.",
        "- **Synthesized timelines.** Real carrier data would add signals (and noise) the complaints don't mention.",
        "",
        "## Headline",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Complaints replayed | {s['complaints']} |",
        f"| Detectable from order data (excludes wrong/missing/damaged items) | {s['detectable']} |",
        f"| **Flagged from order, carrier and payment data alone** | **{s['by_mode'].get('proactive', 0)} of {s['detectable']} "
        f"({s['by_mode'].get('proactive', 0) / s['detectable']:.0%})** |",
        f"| … plus surfaced by the engine asking \"did you get it?\" after an unproven delivery | {s['by_mode'].get('via_prompt', 0)} |",
        f"| … plus after the customer contacted support (silence / repeat contact) | {s['by_mode'].get('after_contact', 0)} |",
        f"| Total before the customer posted publicly | {s['caught']} of {s['detectable']} ({s['coverage_of_detectable']:.0%}) |",
        f"| Median lead time before the public complaint¹ | {_hours(lt['median'])} (from data alone: {_hours(s['proactive_median_lead_hours'])}) |",
        f"| Item problems that need the customer's report | {s['needs_customer_report']} |",
        f"| **False alarms on healthy orders** | **{s['false_alarm_rate']:.1%}** "
        f"({sum(v['with_false_alarm'] for v in hv.values())} of {sum(v['orders'] for v in hv.values())}); "
        f"{s['stress']['per_vertical']['parcel']['with_false_alarm'] / s['stress']['per_vertical']['parcel']['orders']:.0%} "
        f"when carriers can go quiet for up to {s['stress']['max_scan_gap_hours']} h (see below) |",
        f"| Healthy orders that got a \"did you get it?\" prompt (not an alarm) | "
        f"{sum(v['prompted'] for v in hv.values())} of {sum(v['orders'] for v in hv.values())} |",
        "",
        f"¹ Over {s['lead_time_basis']} only. For complaints with no dates, timing comes from fixed defaults "
        "(`DEFAULT_DAYS` in `generate.py`), so their lead times are assumptions and are excluded.",
        "",
        "## By category",
        "",
        "| Category | Caught | Missed | Needs customer report |",
        "|---|---|---|---|",
    ]
    for cat, counts in s["by_category"].items():
        lines.append(f"| {cat} | {counts.get('caught', 0)} | {counts.get('missed', 0)} | {counts.get('needs_customer_report', 0)} |")
    lines += ["", "## Misses, explained", ""]
    misses = [r for r in results if r.status == "missed"]
    if not misses:
        lines.append("None.")
    for r in misses:
        lines.append(f"- **{r.complaint_id}** ({r.category}; stated: {', '.join(r.stated_facts) or 'nothing specific'}). {r.note}")
    lines += ["", "## Every complaint", "",
              "| ID | Date | Category | Stated facts | Result | First rule | Lead time² |", "|---|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: (r.category_id, r.date)):
        result = r.status.replace("_", " ") + (f" ({r.mode.replace('_', ' ')})" if r.mode else "")
        lines.append(f"| {r.complaint_id} | {r.date} | {r.category} | {', '.join(r.stated_facts) or '–'} | {result} | "
                     f"{r.caught_by or '–'} | {_hours(r.lead_time_hours)}{'' if r.timing_stated else ' (assumed)'} |")
    lines += ["", "² (assumed): the complaint states no dates, so the timeline's timing is a default."]
    fa_rules = s["healthy"]["false_alarm_rules"]
    lines += ["", "## False alarms on healthy orders", "",
              f"Healthy orders: {hv.get('parcel', {}).get('orders', 0)} parcel, {hv.get('quick', {}).get('orders', 0)} "
              "quick-commerce, deterministic seed. Parcel transit 2–5 days with scans 12–60 h apart; 20% of scans arrive "
              "late (parcel 2–10 h, quick up to 2 min); proof is OTP (40%), photo + geofence (20%) or unstated (40%); "
              "60% of customers answer the prompt, 40% ignore it; 10% get one honest ETA revision; 15% of parcel "
              "customers ask support a question and get an answer.", ""]
    lines.append("Rules that fired: " + (", ".join(f"{k} ×{v}" for k, v in fa_rules.items()) if fa_rules else "none."))
    st = s.get("stress")
    if st:
        sp = st["per_vertical"]["parcel"]
        rules = ", ".join(f"{k} ×{v}" for k, v in st["false_alarm_rules"].items()) or "none"
        lines += ["", "### Stress: carriers that go quiet", "",
                  f"The standard healthy set never goes quiet longer than 60 h, below the 72 h stall threshold, so its "
                  f"zero is partly by construction. Re-run with scan gaps up to {st['max_scan_gap_hours']} h (weekends, "
                  f"line-haul): **{sp['with_false_alarm']} of {sp['orders']} parcel orders ({sp['with_false_alarm'] / sp['orders']:.0%}) "
                  f"raise an alarm** ({rules}). A 3-day silence is arguably worth telling the customer about even when "
                  "the parcel turns up, so this is a threshold choice for each merchant, not a bug: raise `stall_after` "
                  "and alarms fall, but stalls in the complaint set are caught later."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(complaints_path: Path, out_md: Path, out_json: Path) -> None:
    data = json.loads(complaints_path.read_text(encoding="utf-8"))
    corpus = [c for c in data["complaints"] if c["window"] == "in-window" and not c["duplicate"]]
    results, _ = run_corpus(corpus)
    healthy_stats = run_healthy(healthy.generate())
    stress = run_healthy(healthy.generate(n_quick=0, seed=11, max_gap_hours=96))
    summary = summarise(results, healthy_stats)
    summary["stress"] = {"max_scan_gap_hours": 96, **stress}
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"summary": summary, "results": [asdict(r) for r in results]}, indent=1,
                                   ensure_ascii=False), encoding="utf-8")
    write_markdown(out_md, results, summary)
    print(f"caught {summary['caught']}/{summary['detectable']} detectable ({summary['coverage_of_detectable']:.0%}); "
          f"modes {summary['by_mode']}; median lead {_hours(summary['lead_time_hours']['median'])}; "
          f"needs report {summary['needs_customer_report']}; false alarms {summary['false_alarm_rate']:.1%}")
    print(f"wrote {out_md} and {out_json}")
