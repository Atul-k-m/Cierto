import warnings

import pytest

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fastapi.testclient import TestClient

from wismo.api import app


@pytest.fixture()
def client():
    return TestClient(app)


def states(summary):
    return {o["key"]: (o["state"], o["proof"]) for o in summary["orders"]}


def test_signature_demo_walk(client):
    s = client.post("/v1/demo/sessions").json()
    sid = s["id"]
    assert states(s)["swish"][0] == "preparing"               # every phone has an order at the start
    assert states(s)["smytten-refund"][0] == "refund_overdue"
    s = client.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "claimed"}).json()
    assert {k: v for k, v in states(s).items() if k in ("smytten-delivered", "zomato", "swish")} == {
        "smytten-delivered": ("delivery_claimed", "claimed"),
        "zomato": ("delivery_claimed", "claimed"),
        "swish": ("delivery_claimed", "claimed"),
    }
    rules = {f["rule"] for f in s["feed"]}
    assert "tracking_stalled" not in {f["rule"] for f in s["feed"] if f["host"] == "zomato"}   # cooking is not a stall
    assert {"confirm_receipt", "suspicious_delivery", "phone_mismatch", "refund_overdue"} <= rules


def test_dispute_opens_a_host_neutral_issue(client):
    sid = client.post("/v1/demo/sessions").json()["id"]
    client.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "claimed"})
    view = client.post(f"/v1/demo/sessions/{sid}/orders/zomato/actions", json={"action": "report_not_received"}).json()["view"]
    assert view["state"] == "delivery_disputed"
    assert view["issue"]["id"].startswith("#") and len(view["issue"]["id"]) == 7
    assert [a["id"] for a in view["actions"]] == ["talk_to_person"]


def test_suspicious_delivery_never_verifies_by_silence(client):
    sid = client.post("/v1/demo/sessions").json()["id"]
    s = client.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "two_days"}).json()
    assert states(s)["smytten-delivered"] == ("delivery_claimed", "claimed")   # flagged: silence is not proof
    assert states(s)["swish"] == ("delivered", "verified")                    # ordinary claim: window lapsed


def test_refund_view_names_the_bank_and_reference(client):
    sid = client.post("/v1/demo/sessions").json()["id"]
    view = client.get(f"/v1/demo/sessions/{sid}/orders/smytten-refund").json()["view"]
    assert view["holder"] == {"party": "bank", "name": "your bank"}
    assert view["refund"]["reference"].startswith("RRN")
    assert {a["id"] for a in view["actions"]} == {"talk_to_person", "copy_reference"}


def test_unknown_action_is_rejected(client):
    sid = client.post("/v1/demo/sessions").json()["id"]
    assert client.post(f"/v1/demo/sessions/{sid}/orders/zomato/actions", json={"action": "refund_me"}).status_code == 400


def test_demo_actions_are_resolved_under_the_host_policy(client):
    sid = client.post("/v1/demo/sessions").json()["id"]
    client.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "claimed"})
    food = client.post(f"/v1/demo/sessions/{sid}/orders/zomato/actions", json={"action": "report_not_received"}).json()
    assert food["view"]["resolution"]["decision"] == "refund_now"            # quick commerce: refunded at once
    parcel = client.post(f"/v1/demo/sessions/{sid}/orders/smytten-delivered/actions",
                         json={"action": "report_not_received", "locale": "hi-Latn-IN"}).json()["view"]["resolution"]
    assert parcel["decision"] == "investigate_and_refund" and "Case #" in parcel["shopper_message"]
    client.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "next_day"})
    view = client.get(f"/v1/demo/sessions/{sid}/orders/smytten-delivered").json()["view"]
    assert view["refund"]["stage"] == "initiated"                             # the courier never proved delivery
    for key in ("zomato", "smytten-delivered"):   # the preset also holds a scripted report (smytten-silent)
        types = [w["type"] for w in client.get(f"/v1/demo/sessions/{sid}/webhooks?order={key}").json()["data"]]
        assert types.count("case.opened") == 1 and types.count("remedy.executed") == 1
