"""Canonical event model (ADR-002).

Every fact about an order is an immutable event that records who asserted it.
Proof fields are tri-state on purpose: ``None`` means the source said nothing,
``False`` means the source says it did not happen (e.g. no OTP was used). The
difference drives "claimed vs verified" later.
"""
import hashlib
import json
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from .taxonomy import Status, substatus


class EventType(StrEnum):
    ORDER_PLACED = "order.placed"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_CANCELLED = "order.cancelled"
    SHIPMENT_STATUS = "shipment.status"
    ETA_PROMISED = "eta.promised"            # a promise shown to the customer (checkout or revision)
    ETA_REVISED = "eta.revised"              # a new estimate with a reason (traffic, batched…): expected_by, latest_by
    RIDER_LOCATION = "rider.location"        # a GPS ping from the rider's app: lat, lng, near, distance_to_drop_m
    DISPATCH_STOP_SEQUENCE = "dispatch.stop_sequence"   # the rider's drop order: stops[], one of them this order
    ADDRESS_CHECK = "address.check"          # map pin vs typed address: distance_m, confidence, pin_area, text_area
    ADDRESS_CONFIRMED = "address.confirmed"  # the customer confirmed the spot (fix_address)
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_FAILED = "payment.failed"
    REFUND_STATUS = "refund.status"
    CUSTOMER_CONTACTED = "customer.contacted"
    CUSTOMER_RECEIPT_CONFIRMED = "customer.receipt_confirmed"
    CUSTOMER_RECEIPT_DISPUTED = "customer.receipt_disputed"
    ENGINE_FINDING = "engine.finding"        # a rule fired; written by the engine so it is audited and never fires twice
    ENGINE_RESOLUTION = "engine.resolution"  # the resolver decided what to do (decision, remedy, steps, messages)
    REMEDY_APPROVED = "remedy.approved"      # the host (or its support agent) approved a proposed remedy
    REMEDY_EXECUTED = "remedy.executed"      # the remedy happened: refund issued, reship sent, reattempt delivered


class AssertedBy(StrEnum):
    MERCHANT = "merchant"
    CARRIER = "carrier"
    RIDER = "rider"
    PAYMENT = "payment"
    CUSTOMER = "customer"
    ENGINE = "engine"


class Raw(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str | None = None
    message: str | None = None
    carrier: str | None = None


class Proof(BaseModel):
    model_config = ConfigDict(extra="forbid")
    otp_verified: bool | None = None
    photo_url: str | None = None
    geo_verified: bool | None = None
    call_logged: bool | None = None


class Location(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pincode: str | None = None
    city: str | None = None


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    order_ref: str = Field(min_length=1)
    shipment_ref: str | None = None
    type: EventType
    status: Status | None = None
    substatus: str | None = None
    occurred_at: AwareDatetime
    asserted_by: AssertedBy
    source_adapter: str = Field(min_length=1)
    raw: Raw | None = None
    proof: Proof | None = None
    location: Location | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_status(self) -> "Event":
        if self.type is EventType.SHIPMENT_STATUS:
            if self.status is None or self.substatus is None:
                raise ValueError("shipment.status events need status and substatus")
            if substatus(self.substatus).status is not self.status:
                raise ValueError(f"substatus {self.substatus} does not belong to status {self.status}")
        elif self.status is not None or self.substatus is not None:
            raise ValueError(f"{self.type} events do not carry a fulfilment status")
        return self

    @property
    def ondc_state(self) -> str | None:
        return substatus(self.substatus).ondc_state if self.substatus else None

    def payload_hash(self) -> str:
        """Stable hash of the event content, used to tell a retry from a conflicting reuse of an event_id."""
        body = self.model_dump(mode="json")
        return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class StoredEvent(BaseModel):
    """An event as read back from the log, with store-assigned fields."""
    model_config = ConfigDict(frozen=True)

    seq: int
    received_at: datetime
    event: Event
