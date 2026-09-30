from datetime import datetime, timedelta
from pathlib import Path

from wismo.clock import VirtualClock
from wismo.runner import run_scenario
from wismo.scenario import Scenario
from wismo.store.memory import MemoryEventStore

SCENARIOS = Path(__file__).resolve().parents[2] / "scenarios"


def fired(run):
    return [(f.rule, at.strftime("%d %b %H:%M")) for at, f in run.findings if f.kind == "exception"]


def test_clock_fires_in_time_order_and_replaces_by_key():
    t0 = datetime(2026, 1, 1, 9)
    clock, seen = VirtualClock(t0), []
    clock.schedule("a", t0 + timedelta(hours=2), lambda: seen.append("a-old"))
    clock.schedule("b", t0 + timedelta(hours=1), lambda: seen.append(("b", clock.now())))
    clock.schedule("a", t0 + timedelta(hours=3), lambda: seen.append("a-new"))
    clock.advance_to(t0 + timedelta(hours=5))
    assert seen == [("b", t0 + timedelta(hours=1)), "a-new"]
    assert clock.now() == t0 + timedelta(hours=5)


def test_ic_213360_golden():
    scenario = Scenario.load(SCENARIOS / "IC-213360.json")
    run = run_scenario(scenario, MemoryEventStore(), until=scenario.arrivals()[-1][0] + timedelta(days=3))
    assert fired(run) == [
        ("phone_mismatch", "21 Dec 13:15"),         # three days before the false "delivered"
        ("suspicious_delivery", "24 Dec 14:02"),
        ("delivery_disputed", "25 Dec 12:15"),
        ("support_silence", "27 Dec 12:20"),
        ("repeat_contact", "27 Dec 14:15"),
    ]


def test_vx_07_golden():
    scenario = Scenario.load(SCENARIOS / "VX-07.json")
    run = run_scenario(scenario, MemoryEventStore(), until=scenario.arrivals()[-1][0] + timedelta(days=3))
    assert fired(run) == [
        ("status_conflict", "02 Jan 13:30"),
        ("repeat_contact", "04 Jan 06:40"),
        ("refund_not_started", "04 Jan 13:30"),     # exactly 48 h after the doorstep cancel
        ("support_silence", "05 Jan 09:40"),
    ]


def test_replay_over_an_existing_log_does_not_see_the_future():
    scenario = Scenario.load(SCENARIOS / "IC-213360.json")
    store = MemoryEventStore()
    for event in scenario.to_events():   # the whole scenario is already in the log
        store.append(event)
    run = run_scenario(scenario, store, until=scenario.arrivals()[-1][0] + timedelta(days=3))
    assert fired(run)[0] == ("phone_mismatch", "21 Dec 13:15")


def test_each_rule_fires_once_per_order():
    scenario = Scenario.load(SCENARIOS / "VX-07.json")
    run = run_scenario(scenario, MemoryEventStore(), until=scenario.arrivals()[-1][0] + timedelta(days=30))
    rules = [f.rule for _, f in run.findings]
    assert len(rules) == len(set(rules))
