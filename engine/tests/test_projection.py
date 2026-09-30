from datetime import datetime, timedelta

import pytest

from conftest import IST, make_event
from wismo.profiles import PARCEL
from wismo.projection import ProofState, project

T0 = datetime(2025, 12, 22, 10, 0, tzinfo=IST)


def ev(order="O1", minutes=0, **fields):
    return make_event(order, minutes=minutes, **fields)


def placed(**data):
    return ev(type="order.placed", status=None, substatus=None, asserted_by="merchant",
              data={"amount_inr": 499, "account_phone_last4": "2946", **data})


def delivered(minutes=600, **proof):
    return ev(minutes=minutes, status="delivered", substatus="delivered.delivered", proof=proof or None)


def customer(kind, minutes):
    return ev(type=f"customer.{kind}", status=None, substatus=None, asserted_by="customer", minutes=minutes)


def at(minutes):
    return T0 + timedelta(minutes=minutes)


@pytest.mark.parametrize("proof,expected,by", [
    ({}, ProofState.CLAIMED, None),
    ({"otp_verified": True}, ProofState.VERIFIED, "otp"),
    ({"otp_verified": False}, ProofState.CLAIMED, None),
    ({"photo_url": "x", "geo_verified": True}, ProofState.VERIFIED, "photo_and_geofence"),
    ({"photo_url": "x"}, ProofState.CLAIMED, None),   # a photo without a geofence match proves little
])
def test_delivery_is_a_claim_until_proven(proof, expected, by):
    p = project([placed(), delivered(**proof)], at(601), PARCEL)
    assert (p.proof_state, p.verified_by) == (expected, by)


def test_customer_confirmation_verifies():
    p = project([placed(), delivered(), customer("receipt_confirmed", 700)], at(701), PARCEL)
    assert (p.proof_state, p.verified_by, p.reconciled_state) == (ProofState.VERIFIED, "customer", "delivered")


def test_customer_dispute_wins_over_the_claim():
    p = project([placed(), delivered(), customer("receipt_disputed", 700)], at(701), PARCEL)
    assert (p.proof_state, p.reconciled_state) == (ProofState.DISPUTED, "delivery_disputed")


def test_unanswered_claim_is_verified_only_after_the_report_window():
    events = [placed(), delivered(minutes=600)]
    window = int(PARCEL.report_window.total_seconds() // 60)
    assert project(events, at(600 + window - 1), PARCEL).proof_state is ProofState.CLAIMED
    after = project(events, at(600 + window), PARCEL)
    assert (after.proof_state, after.verified_by) == (ProofState.VERIFIED, "report_window_lapsed")


def test_doorstep_cancel_while_store_says_shipped_is_a_conflict():
    events = [placed(),
              ev(minutes=60, status="in_transit", substatus="in_transit.picked_up", asserted_by="merchant"),
              ev(minutes=500, status="cancelled", substatus="cancelled.doorstep_rejected")]
    p = project(events, at(501), PARCEL)
    assert p.conflicts == ["carrier_stopped_merchant_still_active"]
    assert p.reconciled_state == "cancelled"
    assert p.cancelled_by == "doorstep"


def test_phone_mismatch():
    events = [placed(), ev(minutes=60, status="packed", substatus="packed.packed", asserted_by="merchant",
                           data={"consignee_phone_last4": "7310"})]
    assert project(events, at(61), PARCEL).phone_mismatch


def test_events_are_applied_in_happened_order_whatever_the_input_order():
    events = [delivered(minutes=600), ev(minutes=300, status="out_for_delivery",
                                         substatus="out_for_delivery.out_for_delivery"), placed()]
    p = project(events, at(601), PARCEL)
    assert p.delivery_claim.after_out_for_delivery is True


def test_payment_without_order_state():
    p = project([ev(type="payment.captured", status=None, substatus=None, asserted_by="payment")], at(1), PARCEL)
    assert p.reconciled_state == "payment_without_order"
