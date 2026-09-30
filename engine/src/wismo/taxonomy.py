"""Two-level fulfilment status taxonomy.

Top-level statuses follow the tracking-industry pattern (AfterShip/EasyPost style);
substatuses are namespaced under their status and carry the ONDC fulfilment state
they correspond to, so an ONDC adapter is a thin mapping later (ADR-002).
The source's raw code is always kept on the event alongside these values.
"""
from dataclasses import dataclass
from enum import StrEnum


class Status(StrEnum):
    PENDING = "pending"                    # accepted, not yet with a carrier / rider
    PACKED = "packed"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    FAILED_ATTEMPT = "failed_attempt"      # NDR in Indian logistics
    DELIVERED = "delivered"                # a claim until proven (see proof on the event)
    AVAILABLE_FOR_PICKUP = "available_for_pickup"
    RETURN_TO_ORIGIN = "return_to_origin"  # RTO
    CANCELLED = "cancelled"
    EXCEPTION = "exception"


@dataclass(frozen=True)
class Substatus:
    code: str
    status: Status
    ondc_state: str | None
    description: str


_SUBSTATUSES = [
    Substatus("pending.awaiting_pickup", Status.PENDING, "Pending", "Order ready, waiting for carrier pickup"),
    Substatus("pending.preparing", Status.PENDING, "Pending", "Kitchen or store is preparing the order"),
    Substatus("pending.searching_agent", Status.PENDING, "Searching-for-Agent", "Looking for a delivery partner"),
    Substatus("pending.agent_assigned", Status.PENDING, "Agent-assigned", "Delivery partner assigned"),
    Substatus("packed.packed", Status.PACKED, "Packed", "Packed and ready to hand over"),
    Substatus("in_transit.picked_up", Status.IN_TRANSIT, "Order-picked-up", "Picked up by the carrier or rider"),
    Substatus("in_transit.hub_scan", Status.IN_TRANSIT, None, "Scanned at a hub"),
    Substatus("in_transit.en_route", Status.IN_TRANSIT, None, "Rider moving towards the customer (location ping)"),
    Substatus("in_transit.at_destination_hub", Status.IN_TRANSIT, "At-destination-hub", "Reached the delivery hub"),
    Substatus("out_for_delivery.out_for_delivery", Status.OUT_FOR_DELIVERY, "Out-for-delivery", "Out for delivery"),
    Substatus("failed_attempt.customer_unreachable", Status.FAILED_ATTEMPT, "Customer-not-found", "Courier says the customer could not be reached"),
    Substatus("failed_attempt.address_issue", Status.FAILED_ATTEMPT, "Delivery-failed", "Courier says the address was wrong or incomplete"),
    Substatus("failed_attempt.not_serviceable", Status.FAILED_ATTEMPT, "Delivery-failed", "No delivery partner available for the area"),
    Substatus("failed_attempt.other", Status.FAILED_ATTEMPT, "Delivery-failed", "Delivery attempt failed"),
    Substatus("delivered.delivered", Status.DELIVERED, "Order-delivered", "Marked delivered"),
    Substatus("available_for_pickup.at_branch", Status.AVAILABLE_FOR_PICKUP, None, "Held at a branch for collection"),
    Substatus("return_to_origin.initiated", Status.RETURN_TO_ORIGIN, "RTO-Initiated", "Return to origin started"),
    Substatus("return_to_origin.delivered", Status.RETURN_TO_ORIGIN, "RTO-Delivered", "Returned to the seller"),
    Substatus("return_to_origin.disposed", Status.RETURN_TO_ORIGIN, "RTO-Disposed", "Return disposed"),
    Substatus("cancelled.cancelled", Status.CANCELLED, "Cancelled", "Cancelled"),
    Substatus("cancelled.doorstep_rejected", Status.CANCELLED, "Cancelled", "Rejected at the doorstep"),
    Substatus("exception.unknown", Status.EXCEPTION, None, "Carrier reported an exception"),
]

SUBSTATUSES: dict[str, Substatus] = {s.code: s for s in _SUBSTATUSES}


def substatus(code: str) -> Substatus:
    try:
        return SUBSTATUSES[code]
    except KeyError:
        raise ValueError(f"unknown substatus {code!r}") from None
