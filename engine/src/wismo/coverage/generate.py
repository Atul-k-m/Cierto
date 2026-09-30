"""Turn a complaint's stated facts into an event timeline for the engine.

Rules of the game (so the coverage number means something):
- Only stated facts become signals. "No OTP" in the text -> ``otp_verified: false``;
  silence about OTP -> proof unknown (``null``), never ``false``.
- Unstated things take the value that makes detection *harder*: tracking keeps moving
  unless the complaint says it froze; an out-for-delivery scan precedes every "delivered".
- Times not stated in the complaint use fixed defaults (listed in ``DEFAULT_DAYS``),
  anchored on the complaint's real posting date.
- The simulated customer only answers the engine's "did you get it?" prompt truthfully;
  it never volunteers anything the complaint doesn't say.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from ..events import Event
from .facts import Facts

IST = timezone(timedelta(hours=5, minutes=30))
TENANT = "smytten-coverage"
ACCOUNT_PHONE, OTHER_PHONE = "2946", "7310"

DEFAULT_DAYS = {  # days from order to complaint when the complaint gives no dates
    "transit": {1: 10, 2: 25, 4: 12, 19: 10},
    "attempt": 8,
    "cancel": 8,
    "refund_since_cancel": 14,
    "payment": 3,
}

EXPECTED: dict[int, set[str] | str] = {
    1: {"eta_breached", "eta_slipping", "tracking_stalled", "out_for_delivery_overdue", "failed_attempt"},
    2: {"eta_breached", "eta_slipping", "tracking_stalled", "out_for_delivery_overdue", "failed_attempt"},
    3: {"suspicious_delivery", "delivery_disputed", "phone_mismatch"},
    4: {"tracking_stalled", "eta_breached", "eta_slipping", "status_conflict", "out_for_delivery_overdue"},
    5: {"failed_attempt", "phone_mismatch", "out_for_delivery_overdue", "returned_to_origin", "eta_breached"},
    6: {"returned_to_origin", "status_conflict"},
    13: {"refund_not_started", "refund_overdue", "eta_slipping", "eta_breached", "status_conflict"},
    14: {"refund_not_started", "refund_overdue", "partial_refund", "status_conflict", "payment_without_order"},
    15: {"refund_not_started", "refund_overdue", "partial_refund", "status_conflict", "payment_without_order"},
    16: {"refund_not_started", "refund_overdue", "partial_refund", "status_conflict", "payment_without_order"},
    18: "any",
    19: "any",
    20: {"payment_without_order"},
}   # categories 7-12 and 17 (wrong, missing, damaged items; replacements) need the customer's report


@dataclass
class Case:
    complaint_id: str
    category_id: int
    facts: Facts
    template: str
    arrivals: list[tuple[datetime, Event]]
    complaint_at: datetime
    truth: str | None                      # what the customer answers if asked "did you get it?"
    expected: set[str] | str = field(default_factory=set)
    timing_stated: bool = False            # False: timing comes from DEFAULT_DAYS, so lead time is an assumption


class _Timeline:
    def __init__(self, order_ref: str):
        self.order_ref = order_ref
        self.items: list[tuple[datetime, Event]] = []

    def add(self, at: datetime, type: str, asserted_by: str, **fields) -> None:
        n = len(self.items) + 1
        self.items.append((at, Event.model_validate({
            "event_id": f"{self.order_ref}-{n:03d}", "tenant_id": TENANT, "order_ref": self.order_ref,
            "occurred_at": at, "type": type, "asserted_by": asserted_by, "source_adapter": "coverage", **fields})))

    def scan(self, at, status, sub, asserted_by="carrier", **fields):
        self.add(at, "shipment.status", asserted_by, status=status, substatus=sub, **fields)


def _at(d: date, hh: int, mm: int = 0) -> datetime:
    return datetime.combine(d, time(hh, mm), IST)


def _order_start(t: _Timeline, order_at: datetime, due: datetime, amount: int, wrong_phone=False,
                 pack=True, pickup=True) -> datetime:
    t.add(order_at, "order.placed", "merchant", data={"amount_inr": amount, "payment": "prepaid",
                                                      "account_phone_last4": ACCOUNT_PHONE})
    t.add(order_at, "payment.captured", "payment", data={"amount_inr": amount})
    t.add(order_at + timedelta(minutes=1), "eta.promised", "merchant",
          data={"shown_to_customer": f"Arrives by {due:%a, %d %b}", "due_by": due.isoformat(), "kind": "checkout"})
    picked = order_at + timedelta(days=1, hours=2)
    if pack:
        t.scan(order_at + timedelta(hours=20), "packed", "packed.packed", "merchant",
               data={"consignee_phone_last4": OTHER_PHONE if wrong_phone else ACCOUNT_PHONE})
    if pickup:
        t.scan(picked, "in_transit", "in_transit.picked_up")
    return picked


def _hub_scans(t: _Timeline, start: datetime, until: datetime, every=timedelta(hours=30)) -> None:
    at = start + every
    while at < until:
        t.scan(at, "in_transit", "in_transit.hub_scan")
        at += every


def _eta_revisions(t: _Timeline, due: datetime, until: datetime) -> None:
    """Complaints describe the ETA slipping "daily": each promise is pushed by a day just before it lapses."""
    for _ in range(6):
        at, due = due - timedelta(hours=12), due + timedelta(days=1)
        if at >= until:
            return
        t.add(at, "eta.promised", "merchant",
              data={"shown_to_customer": f"Arrives by {due:%a, %d %b}", "due_by": due.isoformat(), "kind": "revision"})


def _contacts(t: _Timeline, f: Facts, first: datetime, complaint_at: datetime, issue: str | None = None) -> None:
    if not f.flags.get("support_contacted"):
        return
    failed = f.flags.get("support_failure", False)
    count = 3 if f.has("many_contacts") else (2 if failed else 1)
    latest_start = complaint_at - timedelta(hours=6 * count)
    first = min(first, latest_start)
    step = min(timedelta(days=1), (complaint_at - first) / (count + 1))
    for i in range(count):
        data = {"channel": "chatbot" if f.has("bot_loop") else "email", "replied": not failed}
        if issue:
            data["issue"] = issue
        t.add(first + step * i, "customer.contacted", "customer", data=data)


def _due(f: Facts, order_at: datetime) -> datetime:
    return _at(f.dates["due"], 23, 59) if "due" in f.dates else _at((order_at + timedelta(days=6)).date(), 23, 59)


def build(c: dict, f: Facts) -> Case:
    cat = f.category_id
    complaint_at = _at(f.complaint_date, 20)
    t = _Timeline(f"COV-{c['id']}")
    amount = f.amount_inr or 499

    if f.has("payment_no_order") or cat == 20:
        template, truth = "payment", None
        paid = complaint_at - timedelta(days=f.days or DEFAULT_DAYS["payment"])
        t.add(paid, "payment.captured", "payment", data={"amount_inr": amount})
        _contacts(t, f, paid + timedelta(hours=2), complaint_at)
    elif cat == 3:
        template, truth = "claimed_delivered", "not_received"
        if "delivered" in f.dates:
            claim = _at(f.dates["delivered"], 14, 2)
        elif f.has("delivered_early") and "due" in f.dates:
            claim = _at(f.dates["due"] - timedelta(days=2), 14, 2)
        else:
            back = 5 if f.flags.get("support_failure") else 3
            claim = _at((complaint_at - timedelta(days=back)).date(), 14, 2)
        order_at = _at(f.dates["ordered"], 10, 30) if "ordered" in f.dates else claim - timedelta(days=5, hours=3)
        due = _due(f, order_at)
        picked = _order_start(t, order_at, due, amount, wrong_phone=f.has("wrong_phone"))
        _hub_scans(t, picked, claim - timedelta(hours=8))
        t.scan(claim - timedelta(hours=5), "out_for_delivery", "out_for_delivery.out_for_delivery")
        proof = {}
        if f.has("no_otp"):
            proof["otp_verified"] = False
        if f.has("no_call"):
            proof["call_logged"] = False
        t.scan(claim, "delivered", "delivered.delivered", proof=proof or None)
        _contacts(t, f, claim + timedelta(days=1), complaint_at)
    elif cat == 5:
        template, truth = "delivery_attempt", None
        order_at = _at(f.dates["ordered"], 10, 30) if "ordered" in f.dates else \
            complaint_at - timedelta(days=f.days or DEFAULT_DAYS["attempt"])
        due = _due(f, order_at)
        picked = _order_start(t, order_at, due, amount, wrong_phone=f.has("wrong_phone"))
        attempt_day = min(due.date(), (complaint_at - timedelta(days=1)).date())
        _hub_scans(t, picked, _at(attempt_day, 8))
        if f.has("still_out_for_delivery"):
            t.scan(complaint_at - timedelta(hours=30), "out_for_delivery", "out_for_delivery.out_for_delivery")
        else:
            t.scan(_at(attempt_day, 9, 30), "out_for_delivery", "out_for_delivery.out_for_delivery")
            reason = ("failed_attempt.not_serviceable" if f.has("no_partner") or f.has("failed_attempt_msg") else
                      "failed_attempt.address_issue" if f.has("address_blamed") else
                      "failed_attempt.customer_unreachable" if f.has("wrong_phone") else None)
            if reason:
                t.scan(_at(attempt_day, 17), "failed_attempt", reason)
            if f.has("returned"):
                t.scan(order_at + timedelta(days=f.days or 11), "return_to_origin", "return_to_origin.initiated")
        _contacts(t, f, _at(attempt_day, 19), complaint_at)
    elif cat in (13,):
        template, truth = "cancelled", None
        order_at = complaint_at - timedelta(days=DEFAULT_DAYS["cancel"])
        due = _due(f, order_at)
        if f.has("system_cancelled") and not f.has("eta_slipping"):
            cancel_at = order_at + timedelta(hours=18)
            _order_start(t, order_at, due, amount, pack=False, pickup=False)
        else:
            cancel_at = complaint_at - timedelta(days=3)
            if f.has("eta_slipping"):   # the ETA must have slipped before the cancellation, as stated
                order_at = cancel_at - timedelta(days=9)
                due = _due(f, order_at)
            picked = _order_start(t, order_at, due, amount)
            _hub_scans(t, picked, cancel_at)
            if f.has("eta_slipping"):
                _eta_revisions(t, due, cancel_at)
        t.add(cancel_at, "order.cancelled", "merchant", data={"by": "system"})
        if f.has("refund_initiated"):
            t.add(cancel_at + timedelta(days=1), "refund.status", "merchant", data={"stage": "initiated", "amount_inr": amount})
        _contacts(t, f, cancel_at + timedelta(days=1), complaint_at)
    elif cat in (14, 15, 16):
        template, truth = "refund", None
        since = f.days or DEFAULT_DAYS["refund_since_cancel"]
        if f.has("doorstep_cancel"):
            cancel_at = complaint_at - timedelta(days=since)
            order_at = cancel_at - timedelta(days=5)
            picked = _order_start(t, order_at, _due(f, order_at), amount)
            t.scan(picked + timedelta(hours=1), "in_transit", "in_transit.picked_up", "merchant")   # store says Shipped
            _hub_scans(t, picked, cancel_at - timedelta(hours=6))
            t.scan(cancel_at - timedelta(hours=4), "out_for_delivery", "out_for_delivery.out_for_delivery")
            t.scan(cancel_at, "cancelled", "cancelled.doorstep_rejected")
        elif cat == 14 and not f.has("cancelled") and not f.has("refund_initiated"):
            # A return after delivery: returns are not modelled in Phase 1.
            template = "return_not_modelled"
            delivered = complaint_at - timedelta(days=since)
            order_at = delivered - timedelta(days=5)
            picked = _order_start(t, order_at, _due(f, order_at), amount)
            _hub_scans(t, picked, delivered - timedelta(hours=8))
            t.scan(delivered - timedelta(hours=4), "out_for_delivery", "out_for_delivery.out_for_delivery")
            t.scan(delivered, "delivered", "delivered.delivered", proof={"otp_verified": True})
            cancel_at = delivered
        else:
            if "due" in f.dates and f.has("refund_initiated"):     # "refund promised <date>"
                cancel_at = _at(f.dates["due"], 11) - timedelta(days=6)
            else:
                cancel_at = complaint_at - timedelta(days=since)
            order_at = cancel_at - (timedelta(minutes=10) if "within minutes" in c["summary"].lower() else timedelta(days=1))
            _order_start(t, order_at, _due(f, order_at), amount, pack=False, pickup=False)
            t.add(cancel_at, "order.cancelled", "merchant", data={"by": "customer"})
        if f.has("refund_initiated"):
            t.add(cancel_at + timedelta(days=1), "refund.status", "merchant", data={"stage": "initiated", "amount_inr": amount})
        _contacts(t, f, cancel_at + timedelta(days=1), complaint_at)
    elif cat in (1, 2, 4) or (cat in (18, 19) and f.has("tracking_frozen")):
        template, truth = "in_transit", None
        default = DEFAULT_DAYS["transit"].get(cat, 10)
        order_at = _at(f.dates["ordered"], 10, 30) if "ordered" in f.dates else \
            complaint_at - timedelta(days=f.days or default)
        due = _due(f, order_at)
        if f.has("doorstep_cancel"):
            template = "doorstep_cancel"
            picked = _order_start(t, order_at, due, amount)
            t.scan(picked + timedelta(hours=1), "in_transit", "in_transit.picked_up", "merchant")
            cancel_at = complaint_at - timedelta(days=4)
            _hub_scans(t, picked, cancel_at - timedelta(hours=6))
            t.scan(cancel_at - timedelta(hours=4), "out_for_delivery", "out_for_delivery.out_for_delivery")
            t.scan(cancel_at, "cancelled", "cancelled.doorstep_rejected")
            _contacts(t, f, cancel_at + timedelta(days=1), complaint_at)
        else:
            undispatched = f.has("undispatched")
            picked = _order_start(t, order_at, due, amount, pickup=not undispatched)
            if not undispatched:
                if f.has("tracking_frozen"):
                    t.scan(picked + timedelta(days=1), "in_transit", "in_transit.hub_scan")
                elif f.has("still_out_for_delivery") or f.has("failed_attempt_msg"):
                    _hub_scans(t, picked, due - timedelta(days=1))
                    ofd = _at(due.date(), 9, 30)
                    t.scan(ofd, "out_for_delivery", "out_for_delivery.out_for_delivery")
                    if f.has("failed_attempt_msg"):
                        t.scan(ofd + timedelta(hours=8), "failed_attempt", "failed_attempt.other")
                else:
                    _hub_scans(t, picked, complaint_at)
            if f.has("eta_slipping"):
                _eta_revisions(t, due, complaint_at)
            _contacts(t, f, max(due + timedelta(days=1), order_at + timedelta(days=7)), complaint_at)
    else:
        template, truth = "item_issue", "received"
        delivered = complaint_at - timedelta(days=(f.days or 3) + 1)
        order_at = delivered - timedelta(days=5)
        picked = _order_start(t, order_at, _due(f, order_at), amount)
        _hub_scans(t, picked, delivered - timedelta(hours=8))
        t.scan(delivered - timedelta(hours=4), "out_for_delivery", "out_for_delivery.out_for_delivery")
        t.scan(delivered, "delivered", "delivered.delivered")
        if f.refunded_of:
            got, owed = f.refunded_of
            t.add(delivered + timedelta(days=1), "refund.status", "merchant", data={"stage": "initiated", "amount_inr": owed})
            t.add(delivered + timedelta(days=2), "refund.status", "payment", data={"stage": "credited", "amount_inr": got})
        issue = c["category"]
        if f.flags.get("support_contacted"):
            _contacts(t, f, delivered + timedelta(days=1), complaint_at, issue=issue)
        else:
            t.add(delivered + timedelta(days=1), "customer.contacted", "customer",
                  data={"channel": "email", "replied": True, "issue": issue})

    items = sorted((pair for pair in t.items if pair[0] <= complaint_at), key=lambda p: p[0])
    return Case(c["id"], cat, f, template, items, complaint_at, truth, EXPECTED.get(cat, set()),
                timing_stated=bool(f.dates or f.days))
