"""Order projection (ADR-002): what is actually known about an order.

A pure function of the event log and the current time. Keeps each source's view
(merchant, carrier/rider, customer) separately, reconciles them, flags conflicts,
and decides whether a delivery is claimed, verified or disputed.
"""
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from .events import AssertedBy, Event, EventType
from .profiles import Profile
from .taxonomy import Status

_CARRIER_SIDE = {AssertedBy.CARRIER, AssertedBy.RIDER}
_ACTIVE = {Status.PENDING, Status.PACKED, Status.IN_TRANSIT, Status.OUT_FOR_DELIVERY, Status.FAILED_ATTEMPT}
_MOVING = {Status.PACKED, Status.IN_TRANSIT, Status.OUT_FOR_DELIVERY, Status.FAILED_ATTEMPT}
STILL_WITHIN_M = 40   # GPS jitter: pings closer than this to the last spot count as not moving


class ProofState(StrEnum):
    NONE = "none"             # nobody has said it was delivered
    CLAIMED = "claimed"       # the carrier or rider says delivered; not yet proven
    VERIFIED = "verified"     # OTP, photo + geofence, customer confirmation, or the report window lapsed
    DISPUTED = "disputed"     # the customer says it did not arrive


class CustomerClaim(StrEnum):
    NONE = "none"
    RECEIVED = "received"
    NOT_RECEIVED = "not_received"


@dataclass(frozen=True)
class DeliveryClaim:
    at: datetime
    asserted_by: AssertedBy
    otp_verified: bool | None
    call_logged: bool | None
    photo: bool
    geo_verified: bool | None
    after_out_for_delivery: bool


@dataclass(frozen=True)
class EtaPromise:
    at: datetime
    due_by: datetime                   # the commitment: after a revision, the latest-by time
    shown: str
    kind: str                          # checkout | revision
    expected: datetime | None = None   # the current estimate (eta.revised expected_by); None = due_by
    reason: str | None = None          # eta.revised: traffic | weather | batched | kitchen | other
    delay_minutes: int | None = None
    where: str | None = None           # e.g. "Hosur Road"


@dataclass(frozen=True)
class StopSequence:
    at: datetime
    stops_before: int                  # drops the rider makes before this order
    distance_m: float | None           # how far the drop just before this one is from this customer
    added_minutes: int | None


@dataclass(frozen=True)
class AddressCheck:
    at: datetime
    distance_m: float                  # map pin to the geocoded typed address
    confidence: float | None           # 0..1: how sure the check is that the pin is the right place
    pin_area: str | None
    text_area: str | None
    fix_by: datetime | None            # the courier's cut-off for a correction to keep today's delivery
    by: str


@dataclass(frozen=True)
class Contact:
    at: datetime
    channel: str
    replied: bool


@dataclass
class Refund:
    stage: str | None = None          # initiated | processed | credited
    initiated_at: datetime | None = None
    credited_at: datetime | None = None
    amount_inr: float | None = None
    credited_amount_inr: float | None = None
    reference: str | None = None      # UPI RRN / card ARN


@dataclass
class OrderProjection:
    tenant_id: str
    order_ref: str
    placed_at: datetime | None = None
    amount_inr: float | None = None
    prepaid: bool = True
    account_phone_last4: str | None = None
    consignee_phone_last4: str | None = None
    payment_captured_at: datetime | None = None
    merchant_status: Status | None = None
    carrier_status: Status | None = None
    carrier_substatus: str | None = None
    carrier_status_at: datetime | None = None
    packed_at: datetime | None = None
    picked_up_at: datetime | None = None
    last_scan_at: datetime | None = None
    last_scan_where: str | None = None
    last_ping_at: datetime | None = None
    rider_pos: tuple[float, float] | None = None
    rider_still_since: datetime | None = None   # first ping at the rider's current spot
    rider_near: str | None = None
    rider_distance_m: float | None = None       # rider to the customer's drop, as the rider app reports it
    stop_sequence: StopSequence | None = None
    address_check: AddressCheck | None = None
    address_confirmed_at: datetime | None = None
    ofd_at: datetime | None = None
    ofd_count: int = 0
    failed_attempts: list[tuple[datetime, str]] = field(default_factory=list)
    delivery_claim: DeliveryClaim | None = None
    customer_claim: CustomerClaim = CustomerClaim.NONE
    customer_claim_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancelled_by: str | None = None
    rto_at: datetime | None = None
    eta_promises: list[EtaPromise] = field(default_factory=list)
    refund: Refund = field(default_factory=Refund)
    contacts: list[Contact] = field(default_factory=list)
    findings: dict[str, datetime] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)
    proof_state: ProofState = ProofState.NONE
    verified_by: str | None = None
    reconciled_state: str = "unknown"

    @property
    def phone_mismatch(self) -> bool:
        return bool(self.account_phone_last4 and self.consignee_phone_last4
                    and self.account_phone_last4 != self.consignee_phone_last4)

    @property
    def rider_stopped_for(self):
        """How long the rider's pings have come from one spot (evidence, not extrapolation), or None."""
        if self.rider_still_since and self.last_ping_at and self.last_ping_at > self.rider_still_since:
            return self.last_ping_at - self.rider_still_since
        return None

    @property
    def unreplied_contacts(self) -> list[Contact]:
        last_reply = max((c.at for c in self.contacts if c.replied), default=None)
        return [c for c in self.contacts if not c.replied and (last_reply is None or c.at > last_reply)]


def project(events: list[Event], now: datetime, profile: Profile) -> OrderProjection:
    if not events:
        raise ValueError("cannot project an order with no events")
    p = OrderProjection(tenant_id=events[0].tenant_id, order_ref=events[0].order_ref)
    for e in sorted(events, key=lambda e: e.occurred_at):   # stable: ties keep log order
        _apply(p, e)
    _decide_proof(p, now, profile)
    _find_conflicts(p)
    p.reconciled_state = _reconcile(p)
    return p


def _apply(p: OrderProjection, e: Event) -> None:
    d = e.data
    match e.type:
        case EventType.ORDER_PLACED:
            p.placed_at = e.occurred_at
            p.amount_inr = d.get("amount_inr", p.amount_inr)
            p.prepaid = d.get("payment", "prepaid") != "cod"
            p.account_phone_last4 = d.get("account_phone_last4", p.account_phone_last4)
        case EventType.ORDER_CANCELLED:
            p.cancelled_at = e.occurred_at
            p.cancelled_by = d.get("by", e.asserted_by.value)
            if e.asserted_by is AssertedBy.MERCHANT:
                p.merchant_status = Status.CANCELLED
        case EventType.PAYMENT_CAPTURED:
            p.payment_captured_at = e.occurred_at
            p.amount_inr = p.amount_inr or d.get("amount_inr")
        case EventType.ETA_PROMISED:
            p.eta_promises.append(EtaPromise(
                at=e.occurred_at, due_by=datetime.fromisoformat(d["due_by"]),
                shown=d.get("shown_to_customer", ""), kind=d.get("kind", "checkout")))
        case EventType.ETA_REVISED:
            expected = datetime.fromisoformat(d["expected_by"])
            latest = datetime.fromisoformat(d["latest_by"]) if d.get("latest_by") else expected
            p.eta_promises.append(EtaPromise(
                at=e.occurred_at, due_by=max(latest, expected), shown=d.get("shown_to_customer", ""), kind="revision",
                expected=expected, reason=d.get("reason"), delay_minutes=d.get("delay_minutes"), where=d.get("where")))
        case EventType.RIDER_LOCATION:
            pos = (float(d["lat"]), float(d["lng"]))
            if p.rider_pos is None or _meters(p.rider_pos, pos) > STILL_WITHIN_M:
                p.rider_still_since = e.occurred_at
            p.rider_pos, p.last_ping_at = pos, e.occurred_at
            p.rider_near = d.get("near")
            p.rider_distance_m = d.get("distance_to_drop_m")
            p.last_scan_at = max(filter(None, [p.last_scan_at, e.occurred_at]))
            p.last_scan_where = d.get("near") or p.last_scan_where
        case EventType.DISPATCH_STOP_SEQUENCE:
            stops = list(d.get("stops") or [])
            mine = next((i for i, st in enumerate(stops) if st.get("order_ref") == p.order_ref), None)
            if mine is not None:
                before = stops[mine - 1] if mine else {}
                p.stop_sequence = StopSequence(e.occurred_at, mine, before.get("distance_to_you_m"),
                                               d.get("added_minutes"))
        case EventType.ADDRESS_CHECK:
            p.address_check = AddressCheck(
                at=e.occurred_at, distance_m=float(d["distance_m"]), confidence=d.get("confidence"),
                pin_area=d.get("pin_area"), text_area=d.get("text_area"),
                fix_by=datetime.fromisoformat(d["fix_by"]) if d.get("fix_by") else None, by=e.asserted_by.value)
        case EventType.ADDRESS_CONFIRMED:
            p.address_confirmed_at = e.occurred_at
        case EventType.SHIPMENT_STATUS:
            _apply_shipment(p, e)
        case EventType.REFUND_STATUS:
            stage = d["stage"]
            p.refund.stage = stage
            if stage == "initiated":
                p.refund.initiated_at = e.occurred_at
                p.refund.amount_inr = d.get("amount_inr", p.amount_inr)
            p.refund.reference = d.get("reference", p.refund.reference)
            if stage == "credited":
                p.refund.credited_at = e.occurred_at
                p.refund.credited_amount_inr = d.get("amount_inr", p.refund.amount_inr)
        case EventType.CUSTOMER_CONTACTED:
            p.contacts.append(Contact(e.occurred_at, d.get("channel", "unknown"), bool(d.get("replied", False))))
        case EventType.CUSTOMER_RECEIPT_CONFIRMED:
            p.customer_claim, p.customer_claim_at = CustomerClaim.RECEIVED, e.occurred_at
        case EventType.CUSTOMER_RECEIPT_DISPUTED:
            p.customer_claim, p.customer_claim_at = CustomerClaim.NOT_RECEIVED, e.occurred_at
        case EventType.ENGINE_FINDING:
            p.findings.setdefault(d["rule"], e.occurred_at)


def _apply_shipment(p: OrderProjection, e: Event) -> None:
    status = e.status
    if e.asserted_by is AssertedBy.MERCHANT:
        p.merchant_status = status
        p.consignee_phone_last4 = e.data.get("consignee_phone_last4", p.consignee_phone_last4)
        if status is Status.PACKED:
            p.packed_at = e.occurred_at
        return
    if e.asserted_by not in _CARRIER_SIDE:
        return
    p.carrier_status, p.carrier_substatus, p.carrier_status_at = status, e.substatus, e.occurred_at
    p.last_scan_at = max(filter(None, [p.last_scan_at, e.occurred_at]))
    if e.location and e.location.city:
        p.last_scan_where = e.location.city
    p.consignee_phone_last4 = e.data.get("consignee_phone_last4", p.consignee_phone_last4)
    match status:
        case Status.PACKED:
            p.packed_at = p.packed_at or e.occurred_at
        case Status.IN_TRANSIT:
            if e.substatus == "in_transit.picked_up":
                p.picked_up_at = p.picked_up_at or e.occurred_at
        case Status.OUT_FOR_DELIVERY:
            p.ofd_at = e.occurred_at
            p.ofd_count += 1
        case Status.FAILED_ATTEMPT:
            p.failed_attempts.append((e.occurred_at, e.substatus))
        case Status.DELIVERED:
            proof = e.proof
            p.delivery_claim = DeliveryClaim(
                at=e.occurred_at, asserted_by=e.asserted_by,
                otp_verified=proof.otp_verified if proof else None,
                call_logged=proof.call_logged if proof else None,
                photo=bool(proof and proof.photo_url),
                geo_verified=proof.geo_verified if proof else None,
                after_out_for_delivery=p.ofd_count > 0,
            )
        case Status.RETURN_TO_ORIGIN:
            p.rto_at = p.rto_at or e.occurred_at
        case Status.CANCELLED:
            p.cancelled_at = p.cancelled_at or e.occurred_at
            p.cancelled_by = p.cancelled_by or ("doorstep" if e.substatus == "cancelled.doorstep_rejected" else "carrier")


def _meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance in metres (haversine)."""
    lat1, lng1, lat2, lng2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def _decide_proof(p: OrderProjection, now: datetime, profile: Profile) -> None:
    claim = p.delivery_claim
    if claim is None:
        if p.customer_claim is CustomerClaim.RECEIVED:
            p.proof_state, p.verified_by = ProofState.VERIFIED, "customer"
        return
    if p.customer_claim is CustomerClaim.NOT_RECEIVED and p.customer_claim_at >= claim.at:
        p.proof_state = ProofState.DISPUTED
    elif p.customer_claim is CustomerClaim.RECEIVED:
        p.proof_state, p.verified_by = ProofState.VERIFIED, "customer"
    elif claim.otp_verified:
        p.proof_state, p.verified_by = ProofState.VERIFIED, "otp"
    elif claim.photo and claim.geo_verified:
        p.proof_state, p.verified_by = ProofState.VERIFIED, "photo_and_geofence"
    elif now >= claim.at + profile.report_window and "suspicious_delivery" not in p.findings:
        # Silence only verifies an ordinary claim; a delivery already flagged as suspicious stays unproven.
        p.proof_state, p.verified_by = ProofState.VERIFIED, "report_window_lapsed"
    else:
        p.proof_state = ProofState.CLAIMED


def _find_conflicts(p: OrderProjection) -> None:
    carrier_stopped = p.carrier_status in (Status.CANCELLED, Status.RETURN_TO_ORIGIN)
    if carrier_stopped and p.merchant_status in _ACTIVE:
        p.conflicts.append("carrier_stopped_merchant_still_active")
    if (p.cancelled_by in ("merchant", "customer", "system") and p.carrier_status in _MOVING | {Status.DELIVERED}
            and p.carrier_status_at and p.carrier_status_at > p.cancelled_at):
        p.conflicts.append("cancelled_but_carrier_still_moving")


def _reconcile(p: OrderProjection) -> str:
    if p.proof_state is ProofState.DISPUTED:
        return "delivery_disputed"
    if p.proof_state is ProofState.VERIFIED:
        return "delivered"
    if p.proof_state is ProofState.CLAIMED:
        return "delivery_claimed"
    if p.rto_at:
        return "returning"
    if p.cancelled_at:
        return "cancelled"
    if p.carrier_status:
        return p.carrier_status.value
    if p.merchant_status:
        return p.merchant_status.value
    if p.placed_at:
        return "placed"
    if p.payment_captured_at:
        return "payment_without_order"
    return "unknown"
