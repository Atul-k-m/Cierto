from datetime import datetime, timedelta

from conftest import IST, make_event
from wismo.commitments import State, derive
from wismo.profiles import PARCEL, add_working_days
from wismo.projection import project

T0 = datetime(2025, 12, 22, 10, 0, tzinfo=IST)   # a Monday


def ev(minutes=0, **fields):
    fields.setdefault("status", None)
    fields.setdefault("substatus", None)
    return make_event("O1", minutes=minutes, **fields)


def eta(minutes, due, kind="checkout"):
    return ev(minutes, type="eta.promised", asserted_by="merchant",
              data={"due_by": due.isoformat(), "shown_to_customer": "x", "kind": kind})


def commitments(events, now):
    return derive(project(events, now, PARCEL), PARCEL, now)


def of(cs, kind):
    return [c for c in cs if c.kind == kind]


def test_revised_eta_keeps_the_old_promise_visible():
    first, second = T0 + timedelta(days=5), T0 + timedelta(days=7)
    cs = commitments([eta(0, first), eta(60 * 24 * 4, second, "revision")], T0 + timedelta(days=4, hours=1))
    assert [(c.due_at, c.state) for c in of(cs, "eta")] == [(first, State.VOID), (second, State.OPEN)]


def test_eta_breach_waits_for_late_carrier_data():
    due = T0 + timedelta(days=2)
    events = [eta(0, due)]
    assert of(commitments(events, due + PARCEL.late_data_grace - timedelta(minutes=1)), "eta")[0].state is State.OPEN
    assert of(commitments(events, due + PARCEL.late_data_grace), "eta")[0].state is State.BREACHED


def test_on_time_delivery_that_arrives_late_still_meets_the_eta():
    due = T0 + timedelta(days=2)
    delivered = make_event("O1", minutes=60 * 24 * 2 - 60, status="delivered", substatus="delivered.delivered")
    assert of(commitments([eta(0, due), delivered], due + timedelta(hours=13)), "eta")[0].state is State.MET


def test_refund_credit_counts_working_days():
    assert add_working_days(T0, 5) == T0 + timedelta(days=7)          # Mon + 5 working days = next Mon
    refund = ev(0, type="refund.status", asserted_by="merchant", data={"stage": "initiated", "amount_inr": 499})
    [c] = of(commitments([refund], T0 + timedelta(days=1)), "refund_credit")
    assert c.due_at == add_working_days(T0, PARCEL.refund_working_days)


def test_cancelled_prepaid_order_must_start_a_refund():
    events = [ev(0, type="order.placed", asserted_by="merchant", data={"amount_inr": 499}),
              ev(0, type="payment.captured", asserted_by="payment"),
              ev(60, type="order.cancelled", asserted_by="merchant", data={"by": "customer"})]
    [c] = of(commitments(events, T0 + timedelta(hours=50)), "refund_start")
    assert c.state is State.BREACHED


def test_payment_without_order_starts_rbi_clock():
    cs = commitments([ev(0, type="payment.captured", asserted_by="payment")], T0 + timedelta(hours=1))
    assert of(cs, "order_after_payment")[0].state is State.BREACHED
    assert of(cs, "rbi_reversal")[0].due_at == T0 + timedelta(days=5)


def test_support_reply_meets_the_acknowledgement_clock():
    asked = ev(0, type="customer.contacted", asserted_by="customer", data={"replied": False})
    answered = ev(120, type="customer.contacted", asserted_by="customer", data={"replied": True})
    assert of(commitments([asked], T0 + timedelta(hours=49)), "support_ack")[0].state is State.BREACHED
    assert of(commitments([asked, answered], T0 + timedelta(hours=49)), "support_ack") == []
