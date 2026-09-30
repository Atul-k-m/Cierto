"""Run a scenario through the engine on a virtual clock."""
from dataclasses import dataclass, field
from datetime import datetime

from .clock import VirtualClock
from .detectors import Finding
from .engine import Engine
from .events import Event
from .profiles import PROFILES
from .scenario import Scenario
from .store.base import EventStore


@dataclass
class Run:
    engine: Engine
    findings: list[tuple[datetime, Finding]] = field(default_factory=list)


def run_scenario(scenario: Scenario, store: EventStore, until: datetime | None = None,
                 on_finding=None) -> Run:
    arrivals = scenario.arrivals()
    clock = VirtualClock(arrivals[0][0])
    profile = PROFILES[scenario.tenant.vertical]
    engine = Engine(store, clock, lambda _tenant: profile)
    run = Run(engine)
    engine.listeners.append(lambda t, o, f, at: run.findings.append((at, f)))
    if on_finding:
        engine.listeners.append(lambda t, o, f, at: on_finding(engine, f, at))
    for arrival, event in arrivals:
        clock.advance_to(arrival)
        engine.ingest(event)
    clock.advance_to(until or arrivals[-1][0])
    return run


def ingest_later(engine: Engine, at: datetime, event: Event) -> None:
    """Schedule an event to arrive at ``at`` (e.g. a simulated customer's answer to a prompt)."""
    engine.clock.schedule(("arrival", event.event_id), at, lambda: engine.ingest(event))
