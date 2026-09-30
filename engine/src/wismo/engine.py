"""The engine: ingest an event, re-project the order, run detectors, schedule the next check."""
from collections.abc import Callable
from datetime import datetime

from .clock import VirtualClock
from .commitments import derive, next_wakeups
from .detectors import Finding, evaluate
from .events import AssertedBy, Event, EventType
from .profiles import PROFILES, Profile
from .projection import OrderProjection, project
from .store.base import EventStore

FindingListener = Callable[[str, str, Finding, datetime], None]


class Engine:
    def __init__(self, store: EventStore, clock: VirtualClock, profile_for: Callable[[str], Profile]):
        self.store = store
        self.clock = clock
        self.profile_for = profile_for
        self.listeners: list[FindingListener] = []

    def ingest(self, event: Event) -> list[Finding]:
        # Re-evaluate even on a duplicate: evaluation is idempotent (findings fire once per order),
        # and a replay over an existing log must still reach the same findings.
        self.store.append(event)
        return self.evaluate(event.tenant_id, event.order_ref)

    def events(self, tenant_id: str, order_ref: str) -> list[Event]:
        """What has happened by now: a log may already hold later events (replays, backfills)."""
        now = self.clock.now()
        return [s.event for s in self.store.events_for_order(tenant_id, order_ref) if s.event.occurred_at <= now]

    def profile(self, tenant_id: str, order_ref: str, events: list[Event] | None = None) -> Profile:
        """The tenant's vertical, unless the order says otherwise (a food app's grocery order, a test order)."""
        for e in events if events is not None else self.events(tenant_id, order_ref):
            if e.type is EventType.ORDER_PLACED and e.data.get("vertical") in PROFILES:
                return PROFILES[e.data["vertical"]]
        return self.profile_for(tenant_id)

    def projection(self, tenant_id: str, order_ref: str) -> OrderProjection:
        events = self.events(tenant_id, order_ref)
        return project(events, self.clock.now(), self.profile(tenant_id, order_ref, events))

    def evaluate(self, tenant_id: str, order_ref: str) -> list[Finding]:
        if not self.events(tenant_id, order_ref):   # only future-dated facts so far: nothing has happened yet
            return []
        now, profile = self.clock.now(), self.profile(tenant_id, order_ref)
        p = self.projection(tenant_id, order_ref)
        commitments = derive(p, profile, now)
        findings = evaluate(p, commitments, profile, now)
        for f in findings:
            self.store.append(Event(
                event_id=f"{order_ref}:{f.rule}", tenant_id=tenant_id, order_ref=order_ref,
                type=EventType.ENGINE_FINDING, occurred_at=now, asserted_by=AssertedBy.ENGINE,
                source_adapter="engine",
                data={"rule": f.rule, "kind": f.kind, "severity": f.severity, "holder": f.holder,
                      "message": f.message, "evidence": f.evidence},
            ))
            for listener in self.listeners:
                listener(tenant_id, order_ref, f, now)
        if findings:   # findings changed the log; re-derive wakeups from the updated projection
            p = self.projection(tenant_id, order_ref)
            commitments = derive(p, profile, now)
        for at in next_wakeups(p, commitments, profile, now):
            self.clock.schedule((tenant_id, order_ref, at), at, lambda t=tenant_id, o=order_ref: self.evaluate(t, o))
        return findings
