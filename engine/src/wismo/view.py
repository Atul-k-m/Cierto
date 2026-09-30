"""Order view: what a shopper-facing surface needs, built from the engine's truth.

Semantic, not presentational: states, reasons, proof, promises, clocks, who holds the
problem, which actions make sense now, why the order is where it is (``cause``), and what
Cierto decided to do about it (``resolution``). The widget turns this into the host's words
and look. Timeline lines are plain English here; the cause line and the resolution's shopper
message come in the requested locale.
"""
from datetime import datetime

from .commitments import State, derive
from .detectors import RULES, EXCEPTION
from .engine import Engine
from .events import AssertedBy, Event, EventType
from .profiles import Profile
from .projection import OrderProjection, ProofState, project
from .resolver import _clock, _day, _rs, _when, issue_id, resolution_view
from .taxonomy import Status

_DELAY_RULES = {"eta_breached", "eta_slipping", "tracking_stalled", "out_for_delivery_overdue"}
_CHECK_RULES = {"rider_stalled", "address_mismatch"}     # worth a look, not (yet) a delay
_IN_FLIGHT = {"placed", "packed", "preparing", "rider_assigned", "on_the_way", "out_for_delivery", "delayed",
              "attempt_failed"}
_CLOCK_KINDS = {"report_window", "support_ack", "resolution", "refund_start", "refund_credit", "rbi_reversal"}


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _tri(value: bool | None, yes: str, no: str) -> str:
    return "unknown" if value is None else (yes if value else no)


def _base_state(p, live: set[str]) -> tuple[str, str, list[str]]:
    """(state, tone, reasons). Tone: calm | check | attention | urgent | resolved."""
    if p.proof_state is ProofState.DISPUTED:
        return "delivery_disputed", "attention", []
    if p.proof_state is ProofState.CLAIMED:
        return "delivery_claimed", "check", sorted(live & {"suspicious_delivery", "phone_mismatch"})
    if p.proof_state is ProofState.VERIFIED and p.delivery_claim:
        return "delivered", "resolved", []
    if "payment_without_order" in live:
        return "payment_issue", "urgent", []
    if p.cancelled_at or p.rto_at:
        if p.refund.credited_at:
            return "refunded", "resolved", []
        if "refund_overdue" in live:
            return "refund_overdue", "urgent", []
        if p.refund.initiated_at:
            return "refund_on_its_way", "calm", []
        if "refund_not_started" in live:
            return "refund_not_started", "attention", []
        return ("returning" if p.rto_at else "cancelled"), "calm", []
    if "failed_attempt" in live:
        return "attempt_failed", "attention", []
    if delay := sorted(live & _DELAY_RULES):
        return "delayed", "attention", delay
    if p.carrier_substatus in ("pending.preparing",):
        return "preparing", "calm", []
    if p.carrier_substatus in ("pending.agent_assigned", "pending.searching_agent"):
        return "rider_assigned", "calm", []
    if p.carrier_status is Status.OUT_FOR_DELIVERY:
        return "out_for_delivery", "calm", []
    if p.carrier_status is Status.IN_TRANSIT:
        return "on_the_way", "calm", []
    if p.merchant_status is Status.PACKED or p.packed_at:
        return "packed", "calm", []
    return "placed", "calm", []


def _state(p, live: set[str]) -> tuple[str, str, list[str]]:
    state, tone, reasons = _base_state(p, live)
    if state in _IN_FLIGHT and (flags := live & _CHECK_RULES):
        reasons = sorted(set(reasons) | flags)
        tone = "check" if tone == "calm" else tone
    return state, tone, reasons


def _actions(state: str, has_reference: bool, quick: bool, live: set[str]) -> list[dict]:
    person = {"id": "talk_to_person", "primary": False}
    match state:
        case "delivery_claimed":
            return [{"id": "confirm_received", "primary": True}, {"id": "report_not_received", "primary": False}]
        case "delivery_disputed" | "refund_overdue" | "payment_issue" | "attempt_failed" | "delayed" | "refund_not_started":
            acts = [{**person, "primary": True}]
            if quick and state == "delayed":   # late food: "still not here" gets an instant answer
                acts.append({"id": "report_not_received", "primary": False})
            if has_reference and state.startswith("refund"):   # a Cierto refund's reference lives in the resolution
                acts.append({"id": "copy_reference", "primary": False})
        case "refund_on_its_way":
            return [{"id": "copy_reference", "primary": False}] if has_reference else []
        case "delivered" | "refunded":
            return []
        case _:
            acts = [person]
    if state in _IN_FLIGHT and "address_mismatch" in live:   # one tap settles it, before the rider is lost
        acts = [{"id": "fix_address", "primary": True}] + [{**a, "primary": False} for a in acts]
    return acts


def _timeline(events, brand: str, carrier: str | None) -> list[dict]:
    courier = carrier or "The rider"
    out = []
    for e in events:
        text = None
        who = e.asserted_by.value
        d = e.data
        match e.type:
            case EventType.ORDER_PLACED:
                text = "Order placed"
            case EventType.ORDER_CANCELLED:
                text = "You cancelled the order" if d.get("by") == "customer" else f"{brand} cancelled the order"
            case EventType.ETA_PROMISED if d.get("kind") == "revision":
                text = f"{brand} moved the delivery date: {d.get('shown_to_customer')}"
            case EventType.ETA_REVISED:
                why = {"traffic": "traffic", "weather": "rain", "batched": "another drop first",
                       "kitchen": "the kitchen"}.get(d.get("reason"), "a delay")
                text = f"New estimate {_clock(datetime.fromisoformat(d['expected_by']))} because of {why}"
            case EventType.DISPATCH_STOP_SEQUENCE:
                text = "The rider's drop order changed"
            case EventType.ADDRESS_CHECK:
                text = f"Address check: map pin {_distance(float(d['distance_m']))} from the typed address"
            case EventType.ADDRESS_CONFIRMED:
                text = "You confirmed the delivery spot"
            case EventType.REFUND_STATUS:
                text = {"initiated": f"{brand} started a refund of ₹{d.get('amount_inr')}",
                        "credited": f"₹{d.get('amount_inr')} reached your account"}.get(d["stage"])
            case EventType.CUSTOMER_RECEIPT_CONFIRMED:
                text = "You confirmed you received it"
            case EventType.CUSTOMER_RECEIPT_DISPUTED:
                text = "You said it didn't arrive"
            case EventType.CUSTOMER_CONTACTED:
                text = "You asked for help" + ("" if d.get("replied") else " · no reply yet")
            case EventType.ENGINE_FINDING if d["kind"] == EXCEPTION:
                text = d["message"]
            case EventType.SHIPMENT_STATUS:
                city = e.location.city if e.location and e.location.city else None
                text = {
                    "packed.packed": "Packed",
                    "pending.preparing": "Being prepared",
                    "pending.agent_assigned": f"{d.get('rider', 'A rider')} is assigned",
                    "in_transit.picked_up": f"Picked up by {courier}" + (f" in {city}" if city else ""),
                    "in_transit.hub_scan": f"In transit" + (f" · {city}" if city else ""),
                    "in_transit.at_destination_hub": f"Reached the {city} hub" if city else "Reached the delivery hub",
                    "out_for_delivery.out_for_delivery": "Out for delivery",
                    "delivered.delivered": f"{courier} marked it delivered",
                    "cancelled.doorstep_rejected": "Returned at the door with the cancellation code",
                }.get(e.substatus)
                if e.asserted_by is AssertedBy.MERCHANT and e.substatus == "in_transit.picked_up":
                    text = f"{brand} marked it shipped"
        if text:
            out.append({"at": e.occurred_at.isoformat(), "who": who, "text": text,
                        "notice": e.type is EventType.ENGINE_FINDING})
    return out


# ---- cause: why the order is where it is ------------------------------------------------------

def _distance(metres: float | None) -> str | None:
    if metres is None:
        return None
    return f"{metres / 1000:.1f} km" if metres >= 1000 else f"{round(metres / 10) * 10:.0f} m"


def _minutes(td) -> int:
    return max(0, round(td.total_seconds() / 60))


def _span(td) -> str:
    minutes = _minutes(td)
    if minutes < 90:
        return f"{minutes} min"
    hours = round(minutes / 60)
    return f"{hours} hours" if hours < 48 else f"{round(hours / 24)} days"


def _span_hi(td) -> str:
    return _span(td).replace("hours", "ghante").replace("days", "din")


def _mins(n: int, hi: bool) -> str:
    return f"{n} minute" if hi or n == 1 else f"{n} minutes"


def cause_of(p: OrderProjection, live: set[str], profile: Profile, state: str, courier: str, rider: str | None,
             now: datetime, locale: str = "en-IN") -> dict | None:
    """The one reason that best explains the order right now, as {id, text, facts}. Only from the data."""
    hi = locale == "hi-Latn-IN"
    quick = profile.name == "quick"
    who = rider or ("Aapke rider" if hi else "Your rider")

    def out(cid: str, en: str, hin: str, **facts) -> dict:
        return {"id": cid, "text": hin if hi else en,
                "facts": {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in facts.items()}}

    claim = p.delivery_claim
    if claim and p.proof_state in (ProofState.CLAIMED, ProofState.DISPUTED):
        missing = [x for x, bad in (("no OTP", claim.otp_verified is not True), ("no photo", not claim.photo)) if bad]
        missing_hi = [x.replace("no ", "na ") for x in missing]
        at = _clock(claim.at) if quick else _when(claim.at)
        at_en = f"at {at}" if quick else f"on {at}"
        if p.proof_state is ProofState.DISPUTED:
            return out("delivered_not_received", f"You told us it didn't arrive, though {courier} marked it delivered {at_en}",
                       f"Aapne bataya ki order nahi aaya, jabki {courier} ne ise {at} par delivered mark kiya",
                       claimed_at=claim.at, otp=claim.otp_verified, photo=claim.photo)
        return out("delivered_not_received",
                   f"{courier} marked it delivered {at_en}" + (f", with {' and '.join(missing)}" if missing else ""),
                   f"{courier} ne ise {at} par delivered mark kiya" + (f" ({', '.join(missing_hi)})" if missing_hi else ""),
                   claimed_at=claim.at, otp=claim.otp_verified, photo=claim.photo)
    if state not in _IN_FLIGHT:
        return _money_cause(p, live, profile, out)

    c = p.address_check
    if "address_mismatch" in live and c:
        dist = _distance(c.distance_m)
        areas = c.pin_area and c.text_area
        open_ = c.fix_by and c.fix_by > now   # a passed cut-off is not repeated as if it still held
        by = (_clock(c.fix_by) if quick or c.fix_by.date() == now.date() else _when(c.fix_by)) if open_ else None
        return out("address_mismatch",
                   f"Your map pin is {dist} from the address you typed"
                   + (f" (pin in {c.pin_area}, address in {c.text_area})" if areas else "")
                   + (f"; confirm the right spot by {by} to keep today's delivery" if by else ""),
                   f"Aapka map pin aapke likhe address se {dist} door hai"
                   + (f" (pin {c.pin_area} mein, address {c.text_area} mein)" if areas else "")
                   + (f"; aaj ki delivery ke liye {by} tak sahi jagah confirm karein" if by else ""),
                   distance_m=c.distance_m, confidence=c.confidence, pin_area=c.pin_area, text_area=c.text_area,
                   fix_by=c.fix_by)
    if "rider_stalled" in live and p.rider_stopped_for:
        n = _minutes(p.rider_stopped_for)
        near = p.rider_near
        return out("rider_stalled",
                   f"{who} has been stopped for {_mins(n, False)}" + (f" near {near}" if near else ""),
                   f"{who}" + (f" {near} ke paas" if near else "") + f" {n} minute se ruke hue hain",
                   rider=rider, minutes=n, near=near, since=p.rider_still_since, last_ping=p.last_ping_at,
                   distance_m=p.rider_distance_m)
    if "tracking_stalled" in live and p.last_scan_at:
        where = p.last_scan_where
        if not p.picked_up_at and p.packed_at:
            return out("courier_silent", f"Packed {_when(p.packed_at)} and not yet picked up by the courier",
                       f"{_when(p.packed_at)} ko pack hua, par courier ne abhi tak pick up nahi kiya",
                       packed_at=p.packed_at)
        if quick:
            idle = now - p.last_scan_at
            return out("courier_silent", f"No update from {who} for {_span(idle)}",
                       f"{who} ka {_span_hi(idle)} se koi update nahi", last_scan_at=p.last_scan_at, where=where)
        hub = p.carrier_substatus in ("in_transit.hub_scan", "in_transit.at_destination_hub")
        at_en = (f", at the {where} hub" if hub else f", in {where}") if where else ""
        at_hi = (f" ({where} hub par)" if hub else f" ({where} mein)") if where else ""
        return out("courier_silent",
                   f"{courier} hasn't scanned your parcel since {_when(p.last_scan_at)}{at_en}",
                   f"{courier} ne {_when(p.last_scan_at)}{at_hi} ke baad aapka parcel scan nahi kiya",
                   carrier=courier, last_scan_at=p.last_scan_at, where=where,
                   hours=round((now - p.last_scan_at).total_seconds() / 3600))
    seq = p.stop_sequence
    if seq and seq.stops_before and not claim:
        dist = _distance(seq.distance_m)
        if seq.stops_before == 1:
            en = f"{who} is dropping one other order first" + (f", {dist} from you" if dist else "") + "; you're next"
            hin = f"{who} pehle ek aur order deliver kar rahe hain" + (f", aapse {dist} door" if dist else "") + "; uske baad aap"
        else:
            en = f"{who} has {seq.stops_before} other drops before yours"
            hin = f"{who} ke paas aapse pehle {seq.stops_before} aur drops hain"
        if seq.added_minutes:
            en += f". That adds about {_mins(seq.added_minutes, False)}"
            hin += f". Isse lagbhag {seq.added_minutes} minute aur lagenge"
        return out("batched", en, hin, stops_before=seq.stops_before, distance_m=seq.distance_m,
                   added_minutes=seq.added_minutes, rider=rider)
    eta = p.eta_promises[-1] if p.eta_promises else None
    if eta and eta.kind == "revision" and eta.reason and not claim:
        prev = p.eta_promises[-2] if len(p.eta_promises) > 1 else None
        n = eta.delay_minutes
        if n is None and prev and eta.expected:
            n = _minutes((eta.expected or eta.due_by) - (prev.expected or prev.due_by))
        where = eta.where
        subject_en = {"traffic": "Traffic" + (f" on {where}" if where else ""),
                      "weather": "Rain" + (f" in {where}" if where else ""),
                      "kitchen": "The kitchen", "batched": "Another drop"}.get(eta.reason, "A delay")
        subject_hi = {"traffic": (f"{where} par " if where else "") + "traffic",
                      "weather": (f"{where} mein " if where else "") + "baarish",
                      "kitchen": "kitchen", "batched": "ek aur drop"}.get(eta.reason, "ek deri")
        en = f"{subject_en} added {_mins(n, False)}" if n else f"{subject_en} moved the estimate"
        hin = f"{subject_hi} ki wajah se {n} minute aur lagenge" if n else f"{subject_hi} ki wajah se estimate badla"
        if p.rider_distance_m is not None and eta.reason == "traffic":
            en += f"; {who} is {_distance(p.rider_distance_m)} away"
            hin += f"; {who} {_distance(p.rider_distance_m)} door hain"
        return out("traffic_delay" if eta.reason == "traffic" else "eta_revised", en, hin, reason=eta.reason,
                   delay_minutes=n, where=where, expected=eta.expected, latest_by=eta.due_by,
                   distance_m=p.rider_distance_m)
    phone = "phone_mismatch" in live and p.consignee_phone_last4 and p.account_phone_last4
    phone_en = (f"; the parcel carries a different phone number (••{p.consignee_phone_last4}), so {courier} can't "
                f"call you") if phone else ""
    phone_hi = (f"; parcel par doosra phone number (••{p.consignee_phone_last4}) hai, isliye {courier} aapko call "
                f"nahi kar sakta") if phone else ""
    if "out_for_delivery_overdue" in live and p.ofd_at:
        return out("stuck_out_for_delivery", f"Out for delivery since {_when(p.ofd_at)}, with no attempt reported{phone_en}",
                   f"{_when(p.ofd_at)} se out for delivery hai, koi attempt report nahi hua{phone_hi}", ofd_at=p.ofd_at)
    if "failed_attempt" in live and p.failed_attempts:
        at, _sub = p.failed_attempts[-1]
        return out("failed_attempt", f"{courier} reported a failed delivery attempt at {_when(at)}{phone_en}",
                   f"{courier} ne {_when(at)} par delivery attempt fail report kiya{phone_hi}", at=at)
    if "phone_mismatch" in live and p.consignee_phone_last4 and p.account_phone_last4:
        return out("phone_mismatch",
                   f"The phone number on the parcel (••{p.consignee_phone_last4}) isn't yours (••{p.account_phone_last4}), "
                   f"so {courier} can't call you or send the OTP",
                   f"Parcel par phone number (••{p.consignee_phone_last4}) aapka (••{p.account_phone_last4}) nahi hai, "
                   f"isliye {courier} aapko call ya OTP nahi bhej sakta",
                   parcel_phone_last4=p.consignee_phone_last4, account_phone_last4=p.account_phone_last4)
    if "eta_slipping" in live:
        n = sum(e.kind == "revision" for e in p.eta_promises)
        return out("eta_slipping", f"The delivery date has moved {n} times", f"Delivery ki date {n} baar badli hai",
                   revisions=n)
    if "eta_breached" in live and eta:
        due = _clock(eta.due_by) if quick else _day(eta.due_by)
        return out("late", f"It was due by {due}", f"Ise {due} tak aana tha", due=eta.due_by)
    return None


def _money_cause(p, live, profile, out) -> dict | None:
    r = p.refund
    if "refund_overdue" in live and r.initiated_at:
        amt = _rs(r.amount_inr or p.amount_inr)
        return out("refund_overdue", f"Your {amt} refund started {_day(r.initiated_at)} but hasn't reached your account",
                   f"Aapka {amt} refund {_day(r.initiated_at)} ko shuru hua, par abhi tak account mein nahi aaya",
                   initiated_at=r.initiated_at, reference=r.reference, amount_inr=r.amount_inr)
    if "refund_not_started" in live:
        return out("refund_not_started", "The order ended without delivery and no refund has started",
                   "Order bina delivery ke khatam hua aur refund shuru nahi hua")
    if "payment_without_order" in live:
        return out("payment_without_order", "Money was taken but no order was created",
                   "Paisa kat gaya par order nahi bana")
    return None


# ---- the view ---------------------------------------------------------------------------------

def rider_of(events: list[Event]) -> str | None:
    return next((e.data["rider"] for e in reversed(events) if e.data.get("rider")), None)


def build_view(engine: Engine, tenant_id: str, order_ref: str, brand: str, locale: str = "en-IN") -> dict | None:
    now = engine.clock.now()
    events = engine.events(tenant_id, order_ref)
    if not events:
        return None
    profile = engine.profile(tenant_id, order_ref, events)
    p = project(events, now, profile)
    cs = derive(p, profile, now)
    live = {f.rule for rule in RULES if (f := rule(p, cs, profile, now))}
    state, tone, reasons = _state(p, live)
    placed = next((e for e in events if e.type is EventType.ORDER_PLACED), None)
    info = placed.data if placed else {}
    carrier = next((e.raw.carrier for e in reversed(events) if e.raw and e.raw.carrier), None)
    rider = rider_of(events)
    findings = [e for e in events if e.type is EventType.ENGINE_FINDING and e.data["kind"] == EXCEPTION]
    holder_event = next((f for f in reversed(findings) if f.data["rule"] in live), findings[-1] if findings else None)

    etas = [c for c in cs if c.kind == "eta"]
    current_eta = next((c for c in reversed(etas) if c.state is not State.VOID), etas[-1] if etas else None)
    promise = p.eta_promises[-1] if p.eta_promises else None
    clocks = [{"kind": c.kind, "due_at": c.due_at.isoformat(), "state": c.state.value}
              for c in cs if c.kind in _CLOCK_KINDS and c.state in (State.OPEN, State.BREACHED)]

    issue = None
    if tone in ("attention", "urgent") and findings:
        opened = findings[0].occurred_at
        if p.customer_claim_at and state == "delivery_disputed":
            opened = p.customer_claim_at
        issue = {"id": issue_id(order_ref), "opened_at": opened.isoformat(),
                 "reply_by": (opened + profile.support_ack).isoformat(),
                 "resolve_by": (opened + profile.resolution).isoformat()}

    party = holder_event.data["holder"] if holder_event else None
    quick = profile.name == "quick"
    courier = carrier or rider or ("the rider" if quick else "the courier")
    names = {"carrier": carrier or ("the rider" if quick else "the courier"),
             "merchant": brand, "bank": "your bank", "customer": "you"}
    claim = p.delivery_claim
    return {
        "order_ref": order_ref, "tenant": tenant_id, "brand": brand, "vertical": profile.name,
        "now": now.isoformat(), "title": info.get("title"), "items": info.get("items", []),
        "amount_inr": p.amount_inr, "placed_at": _iso(p.placed_at),
        "extras": {k: info[k] for k in ("restaurant", "kitchen", "rider", "area") if k in info},
        "carrier": carrier,
        "state": state, "tone": tone, "reasons": reasons,
        "cause": cause_of(p, live, profile, state, courier, rider, now, locale),
        "proof": {
            "state": p.proof_state.value, "verified_by": p.verified_by, "claimed_at": _iso(claim.at if claim else None),
            "otp": _tri(claim.otp_verified if claim else None, "used", "not_used"),
            "call": _tri(claim.call_logged if claim else None, "logged", "none"),
            "photo": "yes" if claim and claim.photo else ("unknown" if not claim else "none"),
        },
        "eta": None if not current_eta else {
            "due": current_eta.due_at.isoformat(), "shown": current_eta.detail, "state": current_eta.state.value,
            "history": [{"due": c.due_at.isoformat(), "shown": c.detail.removeprefix("superseded: ")}
                        for c in etas if c.state is State.VOID and c is not current_eta],
            "expected": ((promise.expected or promise.due_by) if promise else current_eta.due_at).isoformat(),
            "latest_by": current_eta.due_at.isoformat(),
            "reason": promise.reason if promise else None,
            "delay_minutes": promise.delay_minutes if promise else None,
        },
        "clocks": clocks,
        "holder": {"party": party, "name": names.get(party)} if party else None,
        "issue": issue,
        "refund": None if not p.refund.stage else {
            "stage": p.refund.stage, "amount_inr": p.refund.amount_inr, "reference": p.refund.reference,
            "initiated_at": _iso(p.refund.initiated_at), "credited_at": _iso(p.refund.credited_at)},
        "phone_mismatch": p.phone_mismatch,
        "last_scan": {"at": _iso(p.last_scan_at), "where": p.last_scan_where} if p.last_scan_at else None,
        "notices": [{"at": f.occurred_at.isoformat(), "rule": f.data["rule"], "message": f.data["message"],
                     "holder": names.get(f.data["holder"])} for f in findings],
        "actions": _actions(state, bool(p.refund.reference), quick, live),
        "timeline": _timeline(sorted(events, key=lambda e: e.occurred_at), brand, carrier),
        "resolution": resolution_view(events, locale),
    }
