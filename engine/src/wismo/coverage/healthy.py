"""Synthetic orders that go right, to measure false alarms. Deterministic by seed."""
import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..events import Event
from .generate import IST

TENANTS = {"parcel": "healthy-parcel", "quick": "healthy-quick"}


@dataclass
class HealthyOrder:
    order_ref: str
    vertical: str
    arrivals: list[tuple[datetime, Event]]
    until: datetime
    truth: str | None      # "received" if the customer answers a prompt, None if they ignore it


def _ev(order_ref, vertical, n, at, type, asserted_by, **fields):
    return at, Event.model_validate({
        "event_id": f"{order_ref}-{n:03d}", "tenant_id": TENANTS[vertical], "order_ref": order_ref,
        "occurred_at": at, "type": type, "asserted_by": asserted_by, "source_adapter": "healthy", **fields})


def _proof(rng: random.Random) -> dict | None:
    roll = rng.random()
    if roll < 0.4:
        return {"otp_verified": True}
    if roll < 0.6:
        return {"photo_url": "https://example.invalid/pod.jpg", "geo_verified": True}
    return None   # carrier says nothing about proof: the engine will ask the customer


def parcel(i: int, rng: random.Random, max_gap_hours: int = 60) -> HealthyOrder:
    ref, items = f"HP-{i:04d}", []
    add = lambda at, type, who, **kw: items.append(_ev(ref, "parcel", len(items) + 1, at, type, who, **kw))
    # Times first, strictly increasing; events after. Healthy means every promise is kept.
    placed = datetime(2026, 1, 5, 9, tzinfo=IST) + timedelta(days=rng.randint(0, 240), minutes=rng.randint(0, 600))
    packed = placed + timedelta(hours=rng.randint(3, 20))
    picked = packed + timedelta(hours=rng.randint(2, 8))
    ofd = max(picked + timedelta(hours=12), placed + timedelta(days=rng.randint(2, 5)))
    ofd = ofd.replace(hour=rng.randint(8, 11), minute=0) + (timedelta(days=1) if ofd.hour > 11 else timedelta(0))
    scans, at = [], picked
    while (nxt := at + timedelta(hours=rng.randint(12, max_gap_hours))) < ofd - timedelta(hours=2):
        scans.append(nxt)
        at = nxt
    if ofd - at > timedelta(hours=max_gap_hours):   # keep every gap within range
        scans.append(ofd - timedelta(hours=12))
    delivered = ofd + timedelta(hours=rng.randint(1, 6))
    due = max((placed + timedelta(days=5)).replace(hour=23, minute=59),
              (delivered + timedelta(days=rng.randint(0, 2))).replace(hour=23, minute=59))

    amount = rng.choice([299, 499, 799])
    add(placed, "order.placed", "merchant", data={"amount_inr": amount, "account_phone_last4": "1111"})
    add(placed, "payment.captured", "payment", data={"amount_inr": amount})
    revised = rng.random() < 0.1   # one honest revision: the first promise was a day too optimistic
    first_due = due - timedelta(days=1) if revised else due
    add(placed + timedelta(minutes=1), "eta.promised", "merchant",
        data={"due_by": first_due.isoformat(), "shown_to_customer": "checkout", "kind": "checkout"})
    add(packed, "shipment.status", "merchant", status="packed", substatus="packed.packed",
        data={"consignee_phone_last4": "1111"})
    add(picked, "shipment.status", "carrier", status="in_transit", substatus="in_transit.picked_up")
    for at in scans:
        add(at, "shipment.status", "carrier", status="in_transit", substatus="in_transit.hub_scan")
    if revised:
        add(min(first_due - timedelta(hours=12), ofd - timedelta(hours=1)), "eta.promised", "merchant",
            data={"due_by": due.isoformat(), "shown_to_customer": "revised", "kind": "revision"})
    add(ofd, "shipment.status", "carrier", status="out_for_delivery", substatus="out_for_delivery.out_for_delivery")
    add(delivered, "shipment.status", "carrier", status="delivered", substatus="delivered.delivered", proof=_proof(rng))
    if rng.random() < 0.15:   # asks a question and gets an answer
        add(placed + timedelta(days=1), "customer.contacted", "customer", data={"channel": "chat", "replied": True})
    truth = "received" if rng.random() < 0.6 else None
    return HealthyOrder(ref, "parcel", _late_arrivals(items, rng, timedelta(hours=2), timedelta(hours=10)),
                        delivered + timedelta(days=5), truth)


def quick(i: int, rng: random.Random) -> HealthyOrder:
    ref, items = f"HQ-{i:04d}", []
    add = lambda at, type, who, **kw: items.append(_ev(ref, "quick", len(items) + 1, at, type, who, **kw))
    placed = datetime(2026, 3, 2, 12, tzinfo=IST) + timedelta(days=rng.randint(0, 180), minutes=rng.randint(0, 600))
    picked = placed + timedelta(minutes=rng.randint(6, 9))
    delivered = picked + timedelta(minutes=rng.randint(4, 7))
    due = delivered + timedelta(minutes=rng.randint(1, 5))   # healthy means the promise is kept
    add(placed, "order.placed", "merchant", data={"amount_inr": 229})
    add(placed, "payment.captured", "payment", data={"amount_inr": 229})
    add(placed, "eta.promised", "merchant", data={"due_by": due.isoformat(), "shown_to_customer": "checkout", "kind": "checkout"})
    add(placed + timedelta(minutes=1), "shipment.status", "rider", status="pending", substatus="pending.preparing")
    add(placed + timedelta(minutes=rng.randint(2, 4)), "shipment.status", "rider", status="pending", substatus="pending.agent_assigned")
    add(picked, "shipment.status", "rider", status="in_transit", substatus="in_transit.picked_up")
    add(delivered, "shipment.status", "rider", status="delivered", substatus="delivered.delivered", proof=_proof(rng))
    truth = "received" if rng.random() < 0.6 else None
    return HealthyOrder(ref, "quick", _late_arrivals(items, rng, timedelta(seconds=20), timedelta(minutes=2)),
                        delivered + timedelta(hours=3), truth)


def _late_arrivals(items, rng: random.Random, low: timedelta, high: timedelta):
    """20% of carrier/rider scans reach the engine late, as real pushes do."""
    out = []
    for at, event in items:
        late = event.asserted_by.value in ("carrier", "rider") and rng.random() < 0.2
        out.append((at + (low + (high - low) * rng.random() if late else timedelta(0)), event))
    return sorted(out, key=lambda p: p[0])


def generate(n_parcel: int = 300, n_quick: int = 100, seed: int = 7, max_gap_hours: int = 60) -> list[HealthyOrder]:
    rng = random.Random(seed)
    return [parcel(i, rng, max_gap_hours) for i in range(n_parcel)] + [quick(i, rng) for i in range(n_quick)]
