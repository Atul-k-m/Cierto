"""Replay scenarios: hand-written event timelines derived from real complaints.

Each event carries an ``at`` offset for when it *happened* and an optional
``arrives`` offset for when the engine receives it (default: immediately), which
reproduces late carrier pushes.
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from .events import Event
from .store.base import AppendResult, EventStore

_OFFSET = re.compile(r"^\+(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?$")


def parse_offset(text: str) -> timedelta:
    match = _OFFSET.match(text)
    if not match or text == "+":
        raise ValueError(f"bad offset {text!r}; expected e.g. +2d4h30m")
    days, hours, minutes = (int(g) if g else 0 for g in match.groups())
    return timedelta(days=days, hours=hours, minutes=minutes)


class Tenant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    vertical: str


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    complaints: list[str] = Field(min_length=1)
    note: str
    tenant: Tenant
    order_ref: str
    start: AwareDatetime
    events: list[dict]
    cause: str | None = None            # the WISMO cause this scenario demonstrates (e.g. rider_stalled)
    script: list[dict] = Field(default_factory=list)   # shopper actions at offsets: [{"at": "+6d17h35m", "action": …}]

    def scripted(self) -> list[tuple[datetime, dict]]:
        """(when, {action, locale, …}) for the shopper actions the demo replays, in time order."""
        out = [(self.start + parse_offset(step["at"]), {k: v for k, v in step.items() if k != "at"})
               for step in self.script]
        return sorted(out, key=lambda pair: pair[0])

    @classmethod
    def load(cls, path: str | Path) -> "Scenario":
        return cls.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_events(self) -> list[Event]:
        return [event for _, event in self.arrivals()]

    def arrivals(self) -> list[tuple[datetime, Event]]:
        """(arrival time, event) pairs in arrival order."""
        out = []
        for i, spec in enumerate(self.events, start=1):
            spec = dict(spec)
            occurred_at = self.start + parse_offset(spec.pop("at"))
            arrives = spec.pop("arrives", None)
            arrival = self.start + parse_offset(arrives) if arrives else occurred_at
            out.append((arrival, Event.model_validate({
                "event_id": spec.pop("event_id", f"{self.order_ref}-{i:03d}"),
                "tenant_id": self.tenant.id,
                "order_ref": self.order_ref,
                "occurred_at": occurred_at,
                "source_adapter": spec.pop("source_adapter", "replay"),
                **spec,
            })))
        return sorted(out, key=lambda pair: pair[0])


def replay(store: EventStore, scenario: Scenario) -> dict[AppendResult, int]:
    counts = {result: 0 for result in AppendResult}
    for event in scenario.to_events():
        counts[store.append(event)] += 1
    return counts


def describe(event: Event) -> str:
    what = event.substatus or event.type.value
    notes = []
    if event.proof:
        p = event.proof
        if p.otp_verified is not None:
            notes.append("OTP used" if p.otp_verified else "no OTP used")
        if p.call_logged is not None:
            notes.append("call logged" if p.call_logged else "no call logged")
        if p.photo_url:
            notes.append("photo")
    if event.raw and event.raw.message:
        notes.append(f'"{event.raw.message}"')
    return f"{what}" + (f"  ({'; '.join(notes)})" if notes else "")


def format_timeline(occurred: list[datetime], lines: list[tuple[str, str]]) -> str:
    return "\n".join(f"{when:%a %d %b %H:%M}  {who:<9} {text}" for when, (who, text) in zip(occurred, lines))
