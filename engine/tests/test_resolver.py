"""The AI resolver: deterministic money decisions under tenant policy, and the desk that acts on them."""
import json
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from wismo.cases import CaseDesk
from wismo.clock import VirtualClock
from wismo.engine import Engine
from wismo.events import AssertedBy, Event, EventType
from wismo.profiles import PROFILES
from wismo.resolver import Policy, current, issue_id, rephrase, resolve, situation
from wismo.scenario import Scenario
from wismo.store.memory import MemoryEventStore
from wismo.view import build_view

DEMO = Path(__file__).resolve().parents[2] / "scenarios" / "demo"
PARCEL = Policy(auto_refund_cap_inr=1000, trust_min_for_instant=0.6, investigate_window_hours=24,
                reattempt_first=True, food_instant_refund=False)
FOOD = Policy(auto_refund_cap_inr=500, trust_min_for_instant=0.6, investigate_window_hours=2,
              reattempt_first=False, food_instant_refund=True)
GOOD_CUSTOMER = {"ref": "cus_1", "account_age_days": 420, "orders_90d": 7, "remedies_90d": 0}


class Setup:
    """A scenario replayed to a moment, with a desk on top. ``drop`` cuts a substatus from the timeline."""

    def __init__(self, file: str, after: timedelta, policy: Policy, drop: str | None = None,
                 customer: dict | None = None, at_event: str | None = None):
        sc = Scenario.load(DEMO / file)
        self.tenant, self.order = sc.tenant.id, sc.order_ref
        arrivals = [(a, e) for a, e in sc.arrivals() if not (drop and e.substatus == drop)]
        if customer is not None:
            arrivals = [(a, e.model_copy(update={"data": {**e.data, "customer": customer}})
                         if e.type is EventType.ORDER_PLACED else e) for a, e in arrivals]
        self.clock = VirtualClock(arrivals[0][0])
        self.store = MemoryEventStore(received_at=self.clock.now)
        self.engine = Engine(self.store, self.clock, lambda _t: PROFILES[sc.tenant.vertical])
        self.policy = policy
        self.hooks: list[tuple[str, dict]] = []
        self.desk = CaseDesk(self.engine, lambda _t: "Brand", lambda _t: self.policy,
                             emit=lambda _t, kind, obj: self.hooks.append((kind, obj)))
        for at, e in arrivals:
            self.clock.advance_to(at)
            self.engine.ingest(e)
        anchor = next((e.occurred_at for _, e in arrivals if e.substatus == at_event), arrivals[-1][1].occurred_at)
        self.clock.advance_to(anchor + after)

    def situation(self, **changes):
        s = situation(self.engine, self.tenant, self.order, "Brand")
        return replace(s, **changes) if changes else s

    def resolve(self, action="report_not_received", policy=None, **changes):
        return resolve(self.situation(**changes), action, policy or self.policy)

    def advance(self, **delta):
        self.clock.advance_to(self.clock.now() + timedelta(**delta))

    def ingest(self, **fields):
        base = {"event_id": f"late-{len(self.store.events_for_order(self.tenant, self.order))}",
                "tenant_id": self.tenant, "order_ref": self.order, "occurred_at": self.clock.now(),
                "source_adapter": "test"}
        return self.desk.ingest(Event.model_validate({**base, **fields}))


def unproven_parcel(**kw):
    return Setup("smytten-delivered.json", timedelta(minutes=10), PARCEL, **kw)


# ---- policy branches ----------------------------------------------------------------------------

def test_unproven_parcel_within_policy_investigates_then_refunds():
    r = unproven_parcel(customer=GOOD_CUSTOMER).resolve()
    assert (r.decision, r.remedy["kind"], r.remedy["amount_inr"], r.needs_approval) == \
        ("investigate_and_refund", "refund", 599, False)
    assert r.follow_up["kind"] == "refund_unless_proven"
    assert datetime.fromisoformat(r.remedy["eta"]) - datetime.fromisoformat(r.decided_at) == timedelta(hours=24)
    texts = [s["text"] for s in r.steps]
    assert texts[0].startswith("Checked delivery proof: no OTP, no photo, no call to you")
    assert any(t.startswith("Asked Delhivery to re-verify the delivery (ticket DEL-RV-") for t in texts)
    assert any("scheduled for" in t and "unless Delhivery proves delivery" for t in texts)
    assert texts[-1] == f"Case {issue_id('SMY-4821360')} opened · 48h acknowledgement clock started"
    assert {s["actor"] for s in r.steps} <= {"cierto", "courier", "host", "bank", "agent"}
    assert r.case_id == issue_id("SMY-4821360") and r.trust.score >= 0.9


def test_refund_above_the_cap_needs_approval():
    r = unproven_parcel().resolve(policy=PARCEL.model_copy(update={"auto_refund_cap_inr": 500}))
    assert r.decision == "investigate_and_refund" and r.needs_approval and r.status == "proposed"
    assert "₹599 is above the ₹500 auto-refund limit" in r.approval_reason
    assert any(s["actor"] == "host" and "sent to Brand for approval" in s["text"] for s in r.steps)
    assert "ready for Brand to approve" in r.shopper_message["en-IN"]


def test_low_trust_needs_approval_even_under_the_cap():
    shaky = {"ref": "cus_2", "account_age_days": 12, "orders_90d": 1, "remedies_90d": 3}
    r = Setup("zomato-delivered.json", timedelta(minutes=2), FOOD, customer=shaky).resolve()
    assert r.trust.score < FOOD.trust_min_for_instant
    assert r.decision == "refund_now" and r.needs_approval and "trust" in r.approval_reason
    assert r.remedy["eta"] is None                       # nothing moves until a person approves
    assert "Trust" not in r.shopper_message["en-IN"]    # the shopper is never told they look risky


def test_food_refunds_at_once_or_investigates_by_policy():
    food = Setup("zomato-delivered.json", timedelta(minutes=2), FOOD)
    now = food.resolve()
    assert (now.decision, now.needs_approval, now.follow_up["kind"]) == ("refund_now", False, "execute_now")
    later = food.resolve(policy=FOOD.model_copy(update={"food_instant_refund": False}))
    assert later.decision == "investigate_and_refund"
    assert datetime.fromisoformat(later.remedy["eta"]) - datetime.fromisoformat(later.decided_at) == timedelta(hours=2)


def test_otp_proof_goes_to_a_person_not_to_money():
    setup = unproven_parcel()
    claim = setup.situation().p.delivery_claim
    proven = replace(setup.situation().p, delivery_claim=replace(claim, otp_verified=True))
    r = resolve(setup.situation(p=proven), "report_not_received", PARCEL)
    assert (r.decision, r.remedy["kind"], r.remedy["amount_inr"], r.needs_approval) == \
        ("escalate_human", "human_review", None, False)
    assert "recorded your OTP at the door" in r.shopper_message["en-IN"]


def test_stuck_out_for_delivery_reattempts_first_if_policy_says_so():
    stuck = Setup("smytten-delivered.json", timedelta(hours=26), PARCEL, drop="delivered.delivered",
                  at_event="out_for_delivery.out_for_delivery")
    r = stuck.resolve()
    assert (r.decision, r.remedy["kind"], r.follow_up["kind"]) == ("reattempt", "reattempt", "check_reattempt")
    assert r.remedy["reference"].startswith("DEL-NDR-")
    assert "••2946" in r.shopper_message["en-IN"]      # the reattempt goes out with the right phone number
    r2 = stuck.resolve(policy=PARCEL.model_copy(update={"reattempt_first": False}))
    assert r2.decision == "investigate_and_refund" and r2.follow_up["kind"] == "refund_unless_delivered"


def test_stuck_refund_is_traced_with_the_bank_reference():
    r = Setup("smytten-refund.json", timedelta(days=12), PARCEL).resolve("talk_to_person")
    assert (r.decision, r.remedy["kind"], r.remedy["reference"]) == ("escalate_human", "refund_trace", "RRN 535418027766")
    assert any(s["actor"] == "bank" for s in r.steps)


def test_asking_for_a_person_hands_over_the_policy_answer_for_approval():
    r = unproven_parcel().resolve("talk_to_person")
    assert r.decision == "escalate_human" and r.remedy["kind"] == "refund" and r.needs_approval
    assert r.follow_up["kind"] == "execute_on_approval"
    assert "ready for them to approve" in r.shopper_message["en-IN"]


def test_missing_item_refunds_its_share_for_food_and_reships_for_parcels():
    food = Setup("zomato-delivered.json", timedelta(minutes=2), FOOD)
    r = resolve(food.situation(), "report_missing_item", FOOD, {"items": ["Masala fries"]})
    assert (r.decision, r.remedy["kind"], r.remedy["amount_inr"]) == ("refund_now", "partial_refund", 137)   # 412 / 3
    parcel = unproven_parcel(customer=GOOD_CUSTOMER)
    r2 = resolve(parcel.situation(), "report_missing_item", PARCEL, {"items": ["Plum green tea toner 20 ml"]})
    assert (r2.decision, r2.remedy["kind"]) == ("reship", "reship")


def test_cash_on_delivery_never_auto_refunds():
    setup = unproven_parcel()
    cod = replace(setup.situation().p, prepaid=False)
    r = resolve(setup.situation(p=cod), "report_not_received", PARCEL)
    assert r.needs_approval and "cash on delivery" in r.approval_reason


def test_confirming_receipt_needs_nothing():
    r = unproven_parcel().resolve("confirm_received")
    assert (r.decision, r.remedy["kind"], r.case_id) == ("none", "none", None)


def test_hinglish_carries_the_same_numbers():
    r = unproven_parcel().resolve()
    en, hi = r.shopper_message["en-IN"], r.shopper_message["hi-Latn-IN"]
    for fact in ("₹599", r.case_id, "Thu 25 Dec"):
        assert fact in en and fact in hi
    assert "refund apne aap ho jayega" in hi


# ---- the LLM may reword, never re-decide --------------------------------------------------------

def test_rephrase_keeps_templates_without_a_model(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert rephrase({}, "Refund ₹599. Case #123456.", "s", "en-IN") == ("Refund ₹599. Case #123456.", "s", False)


def test_rephrase_rejects_a_rewrite_that_changes_an_amount():
    shopper = "We'll refund ₹599 by Thu 25 Dec, 2:02 pm. Case #485922."
    faithful = lambda payload: {"shopper_message": "Your ₹599 refund goes out on Thu 25 Dec at 2:02 pm. Case #485922.",
                                "agent_summary": "Refund ₹599 scheduled."}
    greedy = lambda payload: {"shopper_message": "We'll refund ₹699 today. Case #485922.", "agent_summary": "Refund ₹699."}
    dropped = lambda payload: {"shopper_message": "We'll sort it out soon.", "agent_summary": "ok"}
    broken = lambda payload: (_ for _ in ()).throw(RuntimeError("timeout"))
    assert rephrase({}, shopper, "Refund ₹599.", "en-IN", call=faithful)[2] is True
    for call in (greedy, dropped, broken):
        assert rephrase({}, shopper, "Refund ₹599.", "en-IN", call=call) == (shopper, "Refund ₹599.", False)


# ---- the desk: log, follow-ups, approvals -------------------------------------------------------

def test_scheduled_refund_executes_when_the_courier_stays_silent():
    setup = unproven_parcel()
    state = setup.desk.act(setup.tenant, setup.order, "report_not_received")
    assert state["status"] == "approved" and [k for k, _ in setup.hooks][-3:] == \
        ["case.opened", "remedy.proposed", "remedy.approved"]
    setup.advance(hours=25)
    view = build_view(setup.engine, setup.tenant, setup.order, "Brand")
    assert view["refund"]["stage"] == "initiated" and view["refund"]["reference"] == state["remedy"]["reference"]
    assert view["resolution"]["steps"][-2]["text"].startswith("Refunded ₹599")
    assert "remedy.executed" in [k for k, _ in setup.hooks]
    kinds = [e.type for e in setup.engine.events(setup.tenant, setup.order)]
    assert EventType.ENGINE_RESOLUTION in kinds and EventType.REMEDY_EXECUTED in kinds


def test_proof_arriving_before_the_deadline_pauses_the_refund():
    setup = unproven_parcel()
    setup.desk.act(setup.tenant, setup.order, "report_not_received")
    setup.advance(hours=3)
    setup.ingest(type="shipment.status", status="delivered", substatus="delivered.delivered", asserted_by="carrier",
                 proof={"otp_verified": True}, raw={"carrier": "Delhivery"})
    state = current(setup.engine.events(setup.tenant, setup.order))
    assert (state["action"], state["decision"]) == ("proof_arrived", "escalate_human")
    assert [k for k, _ in setup.hooks][-2:] == ["order.proof_changed", "remedy.cancelled"]
    setup.advance(hours=30)
    assert build_view(setup.engine, setup.tenant, setup.order, "Brand")["refund"] is None   # no money moved


def test_approval_loop_executes_an_approved_refund():
    setup = Setup("zomato-delivered.json", timedelta(minutes=2), FOOD.model_copy(update={"auto_refund_cap_inr": 100}))
    state = setup.desk.act(setup.tenant, setup.order, "report_not_received")
    assert state["needs_approval"] and state["status"] == "proposed"
    assert build_view(setup.engine, setup.tenant, setup.order, "Brand")["refund"] is None
    remedy = setup.desk.approve(setup.tenant, state["remedy"]["id"], "ops@brand")
    assert remedy["status"] == "executed" and remedy["approved_by"] == "ops@brand"
    view = build_view(setup.engine, setup.tenant, setup.order, "Brand")
    assert view["resolution"]["needs_approval"] is False and view["refund"]["amount_inr"] == 412
    events = setup.engine.events(setup.tenant, setup.order)
    approval = next(e for e in events if e.type is EventType.REMEDY_APPROVED)
    assert approval.asserted_by is AssertedBy.MERCHANT     # provenance: the host approved, not Cierto


@pytest.mark.parametrize("customer,status", [(GOOD_CUSTOMER, "executed"), (None, "proposed")])
def test_missed_reattempt_moves_to_a_refund(customer, status):
    # No delivery evidence to weigh here, so trust rests on the customer's history: none shared → a person approves.
    stuck = Setup("smytten-delivered.json", timedelta(hours=26), PARCEL, drop="delivered.delivered",
                  at_event="out_for_delivery.out_for_delivery", customer=customer)
    stuck.desk.act(stuck.tenant, stuck.order, "report_not_received")
    stuck.advance(hours=25)
    state = current(stuck.engine.events(stuck.tenant, stuck.order))
    assert (state["action"], state["decision"], state["status"]) == ("reattempt_missed", "refund_now", status)


def test_repeating_an_action_is_a_no_op():
    setup = unproven_parcel()
    first = setup.desk.act(setup.tenant, setup.order, "report_not_received")
    again = setup.desk.act(setup.tenant, setup.order, "report_not_received")
    assert first["resolution_id"] == again["resolution_id"]
    assert sum(e.type is EventType.ENGINE_RESOLUTION for e in setup.engine.events(setup.tenant, setup.order)) == 1


def test_view_resolution_has_exactly_the_public_shape():
    setup = unproven_parcel()
    assert build_view(setup.engine, setup.tenant, setup.order, "Brand")["resolution"] is None
    setup.desk.act(setup.tenant, setup.order, "report_not_received")
    res = build_view(setup.engine, setup.tenant, setup.order, "Brand", "hi-Latn-IN")["resolution"]
    assert set(res) == {"decision", "remedy", "needs_approval", "steps", "shopper_message", "agent_summary", "case_id"}
    assert set(res["remedy"]) == {"kind", "amount_inr", "eta", "reference"}
    assert all(set(s) == {"at", "actor", "text"} for s in res["steps"])
    assert "Kisi ke peeche" in res["shopper_message"]


@pytest.mark.parametrize("action", ["talk_to_person", "report_not_received", "confirm_received", "report_missing_item"])
def test_every_action_resolves_on_every_demo_order(action):
    for file, policy in (("smytten-ok.json", PARCEL), ("smytten-late.json", PARCEL), ("swish-delivered.json", FOOD)):
        r = Setup(file, timedelta(minutes=5), policy).resolve(action)
        assert r.decision in ("investigate_and_refund", "refund_now", "reattempt", "reship", "escalate_human", "none")
        assert r.shopper_message["en-IN"] and r.shopper_message["hi-Latn-IN"]


def test_rephrase_request_shape_with_the_real_sdk(monkeypatch):
    """The optional LLM path, against the real anthropic SDK with a mocked transport (no network)."""
    anthropic = pytest.importorskip("anthropic")
    httpx = pytest.importorskip("httpx2")   # the 1.x SDK's HTTP client

    seen = {}

    def handler(request):
        seen["body"], seen["beta"] = json.loads(request.content), request.headers.get("anthropic-beta", "")
        text = json.dumps({"shopper_message": "Your ₹599 refund goes out by Thu 25 Dec, 2:02 pm unless the courier proves "
                                              "delivery. Case #485922.", "agent_summary": "Refund ₹599 scheduled."})
        return httpx.Response(200, json={
            "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-sonnet-5-5",
            "content": [{"type": "text", "text": text}], "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 10}})

    real = anthropic.Anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: real(
        api_key="test", http_client=httpx.Client(transport=httpx.MockTransport(handler)), **kw))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    shopper = "If they can't prove delivery by Thu 25 Dec, 2:02 pm, your ₹599 refund goes out. Case #485922."
    new, summary, used = rephrase({"amount_text": "₹599"}, shopper, "Refund ₹599.", "en-IN")
    assert used and new.startswith("Your ₹599 refund")
    body = seen["body"]
    assert body["model"] == "claude-sonnet-5-5" and body["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in seen["beta"]
    assert body["output_config"]["format"]["type"] == "json_schema" and body["output_config"]["effort"] == "low"
    assert json.loads(body["messages"][0]["content"])["facts"] == {"amount_text": "₹599"}   # facts only, as data
