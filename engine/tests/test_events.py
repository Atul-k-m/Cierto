from datetime import datetime

import pytest
from pydantic import ValidationError

from conftest import make_event


def test_substatus_must_belong_to_status():
    with pytest.raises(ValidationError, match="does not belong"):
        make_event("O1", status="delivered", substatus="in_transit.hub_scan")


def test_unknown_substatus_rejected():
    with pytest.raises(ValidationError, match="unknown substatus"):
        make_event("O1", status="in_transit", substatus="in_transit.teleported")


def test_shipment_status_needs_status():
    with pytest.raises(ValidationError, match="need status and substatus"):
        make_event("O1", status=None, substatus=None)


def test_non_shipment_event_cannot_carry_status():
    with pytest.raises(ValidationError, match="do not carry a fulfilment status"):
        make_event("O1", type="payment.captured")


def test_naive_timestamps_rejected():
    with pytest.raises(ValidationError):
        make_event("O1", occurred_at=datetime(2025, 12, 22, 10, 0))


def test_ondc_state_mapping():
    event = make_event("O1", status="delivered", substatus="delivered.delivered")
    assert event.ondc_state == "Order-delivered"


def test_proof_absence_differs_from_unknown():
    no_otp = make_event("O1", status="delivered", substatus="delivered.delivered", proof={"otp_verified": False})
    unknown = make_event("O1", status="delivered", substatus="delivered.delivered")
    assert no_otp.proof.otp_verified is False
    assert unknown.proof is None
