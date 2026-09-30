"""Detectors (ADR-003): named, explainable rules over the projection and commitments.

A finding is either an ``exception`` (something is wrong; act and tell the customer)
or a ``check`` (cheap verification, e.g. ask "did you get it?"). Checks are not alarms.
Each rule fires at most once per order; the engine records it in the log.
"""
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from .commitments import Commitment, State
from .profiles import Profile
from .projection import OrderProjection, ProofState
from .taxonomy import Status

EXCEPTION, CHECK = "exception", "check"


@dataclass(frozen=True)
class Finding:
    rule: str
    kind: str
    severity: str        # low | medium | high | critical
    holder: str          # who must act: carrier | merchant | bank | customer
    message: str         # plain language, customer-safe
    evidence: dict = field(default_factory=dict)


Rule = Callable[[OrderProjection, list[Commitment], Profile, datetime], Finding | None]
RULES: list[Rule] = []


def rule(fn: Rule) -> Rule:
    RULES.append(fn)
    return fn


def _breached(commitments: list[Commitment], kind: str) -> Commitment | None:
    return next((c for c in commitments if c.kind == kind and c.state is State.BREACHED), None)


def _span(td) -> str:
    minutes = td.total_seconds() / 60
    if minutes < 90:
        return f"{round(minutes)} min"
    hours = minutes / 60
    if hours < 48:
        return f"{round(hours)} h"
    days = round(hours / 24)
    return f"{days} days"


@rule
def confirm_receipt(p, cs, profile, now):
    if p.delivery_claim and p.proof_state is ProofState.CLAIMED:
        return Finding("confirm_receipt", CHECK, "low", "customer",
                       "Marked delivered without proof. Ask the customer: did you get it?",
                       {"claimed_at": p.delivery_claim.at.isoformat()})


@rule
def suspicious_delivery(p, cs, profile, now):
    c = p.delivery_claim
    if not c or p.proof_state is ProofState.VERIFIED:
        return None
    flags = []
    if c.otp_verified is False:
        flags.append("no OTP used")
    if c.call_logged is False:
        flags.append("no call to the customer")
    if not c.after_out_for_delivery and profile.name == "parcel":   # food apps have no separate out-for-delivery step
        flags.append("no out-for-delivery scan before it")
    if p.phone_mismatch:
        flags.append("courier had a different phone number")
    if len(flags) >= 2:
        return Finding("suspicious_delivery", EXCEPTION, "critical", "carrier",
                       "Marked delivered, but " + " and ".join(flags) + ".", {"flags": flags})


@rule
def delivery_disputed(p, cs, profile, now):
    if p.proof_state is ProofState.DISPUTED:
        return Finding("delivery_disputed", EXCEPTION, "critical", "carrier",
                       "The customer says the order did not arrive, though it was marked delivered.",
                       {"claimed_at": p.delivery_claim.at.isoformat()})


@rule
def eta_breached(p, cs, profile, now):
    if c := _breached(cs, "eta"):
        return Finding("eta_breached", EXCEPTION, "high", "carrier",
                       f"Promised by {c.due_at:%d %b}; not delivered.", {"promised": c.detail})


@rule
def eta_slipping(p, cs, profile, now):
    revisions = [e for e in p.eta_promises if e.kind == "revision"]
    if len(revisions) >= 2 and not p.delivery_claim:
        return Finding("eta_slipping", EXCEPTION, "medium", "carrier",
                       f"Delivery date moved {len(revisions)} times.",
                       {"dates": [e.due_by.isoformat() for e in p.eta_promises]})


@rule
def tracking_stalled(p, cs, profile, now):
    if p.delivery_claim or p.cancelled_at or p.rto_at:
        return None
    if p.packed_at and not p.picked_up_at and now - p.packed_at >= profile.pickup_within:
        return Finding("tracking_stalled", EXCEPTION, "high", "merchant",
                       f"Packed {_span(now - p.packed_at)} ago and not yet picked up by the courier.")
    # Only orders that are moving can go quiet; waiting for pickup is covered by pickup_within.
    if p.last_scan_at and p.carrier_status in (Status.PACKED, Status.IN_TRANSIT) \
            and now - p.last_scan_at >= profile.stall_after:
        where = f" (last seen: {p.last_scan_where})" if p.last_scan_where else ""
        return Finding("tracking_stalled", EXCEPTION, "high", "carrier",
                       f"No tracking update for {_span(now - p.last_scan_at)}{where}.",
                       {"last_scan": p.last_scan_at.isoformat(), "where": p.last_scan_where})


@rule
def rider_stalled(p, cs, profile, now):
    """The rider's app keeps reporting the same spot. Evidence-based: measured between pings, never extrapolated."""
    if p.delivery_claim or p.cancelled_at or p.rto_at:
        return None
    stopped = p.rider_stopped_for
    if stopped is not None and stopped >= profile.rider_stall_after:
        near = f" near {p.rider_near}" if p.rider_near else ""
        return Finding("rider_stalled", EXCEPTION, "medium", "carrier",
                       f"The rider has been stopped for {_span(stopped)}{near}.",
                       {"since": p.rider_still_since.isoformat(), "near": p.rider_near,
                        "minutes": round(stopped.total_seconds() / 60)})


@rule
def address_mismatch(p, cs, profile, now):
    """The map pin and the typed address disagree: a cheap check the customer can settle with one tap."""
    c = p.address_check
    if not c or p.delivery_claim or p.cancelled_at or p.rto_at:
        return None
    if p.address_confirmed_at and p.address_confirmed_at >= c.at:
        return None
    if c.distance_m >= profile.address_mismatch_m or (c.confidence is not None and c.confidence < 0.5):
        where = f" (pin in {c.pin_area}, address in {c.text_area})" if c.pin_area and c.text_area else ""
        return Finding("address_mismatch", CHECK, "medium", "customer",
                       f"The map pin is {_distance(c.distance_m)} from the typed address{where}. "
                       f"Ask the customer to confirm the spot.",
                       {"distance_m": c.distance_m, "confidence": c.confidence})


def _distance(metres: float) -> str:
    return f"{metres / 1000:.1f} km" if metres >= 1000 else f"{round(metres / 10) * 10:.0f} m"


@rule
def out_for_delivery_overdue(p, cs, profile, now):
    if p.delivery_claim or not p.ofd_at or p.cancelled_at or p.rto_at:
        return None
    outcome_after = any(at > p.ofd_at for at, _ in p.failed_attempts)
    if (now - p.ofd_at >= profile.ofd_max and not outcome_after) or p.ofd_count >= 3:
        return Finding("out_for_delivery_overdue", EXCEPTION, "high", "carrier",
                       f"Out for delivery {p.ofd_count} time(s), no delivery or attempt reported.")


@rule
def failed_attempt(p, cs, profile, now):
    if p.failed_attempts and not p.delivery_claim:
        at, sub = p.failed_attempts[-1]
        return Finding("failed_attempt", EXCEPTION, "high", "carrier",
                       "The courier reported a failed delivery attempt. Confirm with the customer before it is returned.",
                       {"reason": sub, "at": at.isoformat()})


@rule
def phone_mismatch(p, cs, profile, now):
    if p.phone_mismatch:
        return Finding("phone_mismatch", EXCEPTION, "high", "merchant",
                       "The phone number on the parcel is not the customer's; the courier can't call or send the OTP.",
                       {"account": p.account_phone_last4, "parcel": p.consignee_phone_last4})


@rule
def status_conflict(p, cs, profile, now):
    if p.conflicts:
        return Finding("status_conflict", EXCEPTION, "high", "merchant",
                       "The courier and the store disagree about this order's status.", {"conflicts": p.conflicts})


@rule
def returned_to_origin(p, cs, profile, now):
    if p.rto_at:
        return Finding("returned_to_origin", EXCEPTION, "high", "carrier",
                       "The parcel is being returned to the seller.", {"at": p.rto_at.isoformat()})


@rule
def refund_not_started(p, cs, profile, now):
    if c := _breached(cs, "refund_start"):
        return Finding("refund_not_started", EXCEPTION, "high", "merchant",
                       "The order ended without delivery and no refund has started.", {"due": c.due_at.isoformat()})


@rule
def refund_overdue(p, cs, profile, now):
    if c := _breached(cs, "refund_credit"):
        holder = "bank" if p.refund.reference else "merchant"
        return Finding("refund_overdue", EXCEPTION, "high", holder,
                       f"Refund started {p.refund.initiated_at:%d %b} but hasn't reached the customer.",
                       {"due": c.due_at.isoformat(), "reference": p.refund.reference})


@rule
def partial_refund(p, cs, profile, now):
    r = p.refund
    expected = r.amount_inr or p.amount_inr
    if r.credited_amount_inr is not None and expected and r.credited_amount_inr < expected:
        return Finding("partial_refund", EXCEPTION, "medium", "merchant",
                       f"Refunded ₹{r.credited_amount_inr:g} of ₹{expected:g}.",
                       {"expected": expected, "credited": r.credited_amount_inr})


@rule
def payment_without_order(p, cs, profile, now):
    if _breached(cs, "order_after_payment"):
        return Finding("payment_without_order", EXCEPTION, "critical", "merchant",
                       "Money was taken but no order was created. RBI rules require automatic reversal by T+5.")


@rule
def support_silence(p, cs, profile, now):
    if c := _breached(cs, "support_ack"):
        return Finding("support_silence", EXCEPTION, "high", "merchant",
                       "The customer contacted support and got no reply within 48 hours.",
                       {"since": c.opened_at.isoformat()})


@rule
def repeat_contact(p, cs, profile, now):
    recent = [c for c in p.unreplied_contacts if now - c.at <= profile.repeat_contact_window]
    if len(recent) >= 2:
        return Finding("repeat_contact", EXCEPTION, "medium", "merchant",
                       f"The customer has asked {len(recent)} times without an answer.")


def evaluate(p: OrderProjection, commitments: list[Commitment], profile: Profile, now: datetime) -> list[Finding]:
    found = []
    for r in RULES:
        f = r(p, commitments, profile, now)
        if f and f.rule not in p.findings:
            found.append(f)
    return found
