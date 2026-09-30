"""Commitments (ADR-002): promises and deadlines, each with a due time.

Derived from the projection, so they are always consistent with the event log.
Superseded ETAs are kept (as void) so a slipped promise stays visible.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .profiles import Profile, add_working_days
from .projection import OrderProjection, ProofState
from .taxonomy import Status


class State(StrEnum):
    OPEN = "open"
    MET = "met"
    BREACHED = "breached"
    VOID = "void"          # superseded or no longer applicable


@dataclass(frozen=True)
class Commitment:
    kind: str
    opened_at: datetime
    due_at: datetime
    state: State
    detail: str = ""
    check_at: datetime | None = None   # when a breach is declared; later than due_at if late data is tolerated

    @property
    def decides_at(self) -> datetime:
        return self.check_at or self.due_at


def _state(met_at: datetime | None, due_at: datetime, now: datetime, grace=None) -> State:
    if met_at is not None and met_at <= due_at:
        return State.MET
    return State.BREACHED if now >= due_at + (grace or timedelta(0)) else State.OPEN


def derive(p: OrderProjection, profile: Profile, now: datetime) -> list[Commitment]:
    out: list[Commitment] = []
    ended = p.cancelled_at or p.rto_at

    # ETA shown to the customer; revisions supersede but never erase earlier promises.
    for old in p.eta_promises[:-1]:
        out.append(Commitment("eta", old.at, old.due_by, State.VOID, f"superseded: {old.shown}"))
    if p.eta_promises:
        eta = p.eta_promises[-1]
        delivered_at = p.delivery_claim.at if p.delivery_claim else None
        state = State.VOID if ended and not delivered_at else _state(delivered_at, eta.due_by, now, profile.late_data_grace)
        out.append(Commitment("eta", eta.at, eta.due_by, state, eta.shown, check_at=eta.due_by + profile.late_data_grace))

    # Customer's window to dispute a "delivered".
    if p.delivery_claim:
        claim = p.delivery_claim
        answered = p.customer_claim_at if (p.customer_claim_at and p.customer_claim_at >= claim.at) else None
        due = claim.at + profile.report_window
        state = State.MET if answered else (State.VOID if now >= due else State.OPEN)
        out.append(Commitment("report_window", claim.at, due, state, "time left to report a missing delivery"))

    # Support must acknowledge within 48 hours and resolve within a month (E-Commerce Rules 2020).
    unreplied = p.unreplied_contacts
    if unreplied:
        first = unreplied[0]
        out.append(Commitment("support_ack", first.at, first.at + profile.support_ack,
                              _state(None, first.at + profile.support_ack, now), "acknowledge the customer"))
    first_issue = min((c.at for c in p.contacts), default=None)
    if p.proof_state is ProofState.DISPUTED:
        first_issue = min(filter(None, [first_issue, p.customer_claim_at]))
    if first_issue:
        resolved = p.refund.credited_at or (p.customer_claim_at if p.proof_state is ProofState.VERIFIED else None)
        out.append(Commitment("resolution", first_issue, first_issue + profile.resolution,
                              _state(resolved, first_issue + profile.resolution, now), "resolve the complaint"))

    # A prepaid order that ended without delivery, or was disputed, must start a refund.
    refund_trigger = None
    if p.prepaid and p.payment_captured_at:
        refund_trigger = ended if (ended and not p.delivery_claim) else None
    if refund_trigger:
        out.append(Commitment("refund_start", refund_trigger, refund_trigger + profile.refund_start_within,
                              _state(p.refund.initiated_at, refund_trigger + profile.refund_start_within, now),
                              "start the refund"))
    if p.refund.initiated_at:
        due = add_working_days(p.refund.initiated_at, profile.refund_working_days)
        out.append(Commitment("refund_credit", p.refund.initiated_at, due,
                              _state(p.refund.credited_at, due, now), "refund reaches the customer"))

    # Money taken but no order created: order must appear, else RBI T+5 reversal applies.
    if p.payment_captured_at and (p.placed_at is None or p.placed_at > p.payment_captured_at):
        due = p.payment_captured_at + profile.order_after_payment
        out.append(Commitment("order_after_payment", p.payment_captured_at, due,
                              _state(p.placed_at, due, now), "create the order for this payment"))
        if p.placed_at is None or p.placed_at > due:
            rbi_due = p.payment_captured_at + profile.rbi_reversal
            out.append(Commitment("rbi_reversal", p.payment_captured_at, rbi_due,
                                  _state(p.refund.credited_at, rbi_due, now), "RBI T+5 auto-reversal"))
    return out


def next_wakeups(p: OrderProjection, commitments: list[Commitment], profile: Profile, now: datetime) -> set[datetime]:
    """Times at which a time-based rule could change its answer for this order."""
    times = {c.decides_at for c in commitments if c.state is State.OPEN}
    active = p.delivery_claim is None and not (p.cancelled_at or p.rto_at)
    if active and p.last_scan_at and p.carrier_status in (Status.PACKED, Status.IN_TRANSIT):
        times.add(p.last_scan_at + profile.stall_after)
    if active and p.packed_at and not p.picked_up_at:
        times.add(p.packed_at + profile.pickup_within)
    if active and p.ofd_at:
        times.add(p.ofd_at + profile.ofd_max)
    if p.delivery_claim:
        times.add(p.delivery_claim.at + profile.report_window)
    return {t for t in times if t > now}
