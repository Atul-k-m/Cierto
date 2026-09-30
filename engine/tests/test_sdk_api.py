"""The SDK server API: keys, customer sessions, ingestion, views, actions, config, remedies, webhooks."""
import json
import time
import warnings

import pytest

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fastapi.testclient import TestClient

from wismo import sdk, webhooks
from wismo.api import app, reset_state
from wismo.sdk import TENANTS, TEST_CUSTOMER


@pytest.fixture(autouse=True)
def fresh_tenants():
    reset_state()   # every tenant starts on a fresh log: default policy, no sessions, no webhooks


@pytest.fixture()
def client():
    return TestClient(app)


def sk(tenant="smytten"):
    return {"Authorization": f"Bearer {TENANTS[tenant].secret_key}"}


def browser(client, order_id, tenant="smytten", customer_ref=TEST_CUSTOMER["ref"]):
    cs = client.post("/v1/customer_sessions", headers=sk(tenant),
                     json={"order_id": order_id, "customer_ref": customer_ref}).json()["client_secret"]
    return {"Authorization": f"Bearer {TENANTS[tenant].publishable_key}", "Cierto-Client-Secret": cs}


def hooks(client, tenant="smytten"):
    return [w["type"] for w in reversed(client.get("/v1/dev/webhook_log", headers=sk(tenant)).json()["data"])]


def test_dev_keys_list_every_tenant_with_test_orders(client):
    data = client.get("/v1/dev/keys").json()["data"]
    assert [d["tenant"] for d in data] == ["smytten", "zomato", "swish"]
    for d in data:
        assert d["publishable_key"].startswith("pk_test_") and d["secret_key"].startswith("sk_test_")
        assert d["webhook_secret"].startswith("whsec_")
        assert {o["id"] for o in d["test_orders"]} == {"ord_test_unproven", "ord_test_stuck_ofd",
                                                       "ord_test_refund_stuck", "ord_test_qc_late"}


def test_dev_endpoints_vanish_outside_dev_mode(client, monkeypatch):
    monkeypatch.setenv("CIERTO_ENV", "live")
    assert client.get("/v1/dev/keys").status_code == 404


def test_test_orders_sit_at_their_interesting_moment(client):
    states = {o["id"]: o["state"] for o in client.get("/v1/orders", headers=sk()).json()["data"]}
    assert states == {"ord_test_unproven": "delivery_claimed", "ord_test_stuck_ofd": "delayed",
                      "ord_test_refund_stuck": "refund_overdue", "ord_test_qc_late": "delayed"}
    qc = client.get("/v1/orders/ord_test_qc_late/view", headers=sk("zomato")).json()["view"]
    assert qc["vertical"] == "quick" and set(qc["reasons"]) == {"eta_breached", "tracking_stalled"}


def test_keys_and_client_secrets_are_enforced(client):
    assert client.post("/v1/customer_sessions", json={}).json()["error"]["code"] == "missing_api_key"
    pk = {"Authorization": f"Bearer {TENANTS['smytten'].publishable_key}"}
    r = client.post("/v1/customer_sessions", headers=pk, json={"order_id": "ord_test_unproven", "customer_ref": "x"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "secret_key_required"
    assert client.get("/v1/orders/ord_test_unproven/view", headers=pk).json()["error"]["code"] == "client_secret_required"
    h = browser(client, "ord_test_unproven")
    assert client.get("/v1/orders/ord_test_unproven/view", headers=h).status_code == 200
    wrong = client.get("/v1/orders/ord_test_stuck_ofd/view", headers=h)
    assert wrong.status_code == 403 and wrong.json()["error"]["code"] == "client_secret_wrong_order"
    other_tenant = {**h, "Authorization": f"Bearer {TENANTS['zomato'].publishable_key}"}
    assert client.get("/v1/orders/ord_test_unproven/view", headers=other_tenant).status_code == 401
    mismatch = client.post("/v1/customer_sessions", headers=sk(), json={"order_id": "ord_test_unproven",
                                                                         "customer_ref": "cus_someone_else"})
    assert mismatch.status_code == 403 and mismatch.json()["error"]["code"] == "customer_mismatch"


def test_expired_client_secret_is_refused(client, monkeypatch):
    h = browser(client, "ord_test_unproven")
    monkeypatch.setattr(sdk, "_now_ts", lambda: time.time() + sdk.SESSION_TTL.total_seconds() + 1)
    assert client.get("/v1/orders/ord_test_unproven/view", headers=h).json()["error"]["code"] == "client_secret_expired"


def test_report_not_received_resolves_and_signs_webhooks(client):
    h = browser(client, "ord_test_unproven")
    view = client.post("/v1/orders/ord_test_unproven/actions", headers=h,
                       json={"action": "report_not_received", "locale": "hi-Latn-IN"}).json()["view"]
    res = view["resolution"]
    assert view["state"] == "delivery_disputed"
    assert (res["decision"], res["remedy"]["kind"], res["remedy"]["amount_inr"], res["needs_approval"]) == \
        ("investigate_and_refund", "refund", 599, False)
    assert res["case_id"].startswith("#") and "Case " + res["case_id"] in res["shopper_message"]
    assert "apne aap" in res["shopper_message"]                       # Hinglish, as asked
    log = client.get("/v1/dev/webhook_log", headers=sk()).json()["data"]
    assert [w["type"] for w in reversed(log)] == ["order.proof_changed", "case.opened", "remedy.proposed",
                                                  "remedy.approved"]
    secret = TENANTS["smytten"].webhook_secret
    for w in log:
        webhooks.verify(secret, w["headers"], w["body"])
        assert json.loads(w["body"])["data"]["object"]
    audit = client.get("/v1/orders/ord_test_unproven/events", headers=sk()).json()["data"]
    decision = next(e for e in audit if e["type"] == "engine.resolution")
    assert decision["asserted_by"] == "engine" and decision["data"]["trust"]["score"] >= 0.6


def test_the_test_clock_runs_the_scheduled_refund(client):
    client.post("/v1/orders/ord_test_unproven/actions", headers=sk(), json={"action": "report_not_received"})
    client.post("/v1/dev/advance", headers=sk(), json={"hours": 25})
    view = client.get("/v1/orders/ord_test_unproven/view", headers=sk()).json()["view"]
    assert view["refund"]["stage"] == "initiated"
    assert view["resolution"]["steps"][-2]["text"].startswith("Refunded ₹599")
    assert hooks(client)[-1] == "remedy.executed"


def test_approval_loop_over_the_cap(client):
    cfg = client.put("/v1/config", headers=sk("zomato"), json={"policy": {"auto_refund_cap_inr": 300}}).json()
    assert cfg["policy"]["auto_refund_cap_inr"] == 300 and cfg["version"] == 2
    res = client.post("/v1/orders/ord_test_unproven/actions", headers=sk("zomato"),
                      json={"action": "report_not_received"}).json()["view"]["resolution"]
    assert res["decision"] == "refund_now" and res["needs_approval"]
    proposed = [json.loads(w["body"]) for w in client.get("/v1/dev/webhook_log", headers=sk("zomato")).json()["data"]
                if w["type"] == "remedy.proposed"][0]["data"]["object"]
    assert proposed["status"] == "proposed" and "above the ₹300" in proposed["approval_reason"]
    ok = client.post(f"/v1/remedies/{proposed['id']}/approve", headers=sk("zomato"), json={"approved_by": "ops@zomato"})
    assert ok.status_code == 200 and ok.json()["status"] == "executed"
    assert hooks(client, "zomato")[-2:] == ["remedy.approved", "remedy.executed"]
    again = client.post(f"/v1/remedies/{proposed['id']}/approve", headers=sk("zomato"), json={})
    assert again.status_code == 409
    assert client.post("/v1/remedies/rem_nope/approve", headers=sk("zomato"), json={}).status_code == 404


def test_simulate_shows_what_a_policy_change_would_do(client):
    r = client.post("/v1/config/simulate", headers=sk(), json={"policy": {"auto_refund_cap_inr": 300}}).json()
    by_id = {d["order_id"]: d for d in r["data"]}
    assert by_id["ord_test_unproven"]["changed"] == ["needs_approval"]
    assert by_id["ord_test_unproven"]["proposed"]["resolution"]["needs_approval"] is True
    assert r["summary"]["auto_refund_inr"]["current"] > r["summary"]["auto_refund_inr"]["proposed"]
    one = client.post("/v1/config/simulate", headers=sk(), json={
        "order_id": "ord_test_unproven", "customer": {"remedies_90d": 4, "account_age_days": 5, "orders_90d": 0}}).json()["data"][0]
    assert one["current"]["trust"]["score"] < 0.6 and one["current"]["resolution"]["needs_approval"]
    assert client.get("/v1/orders/ord_test_unproven/view", headers=sk()).json()["view"]["resolution"] is None
    bad = client.put("/v1/config", headers=sk(), json={"policy": {"trust_min_for_instant": 3}})
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "invalid_policy"


def test_events_batch_dedupes_rejects_and_is_idempotent(client):
    batch = {"events": [
        {"event_id": "shiprocket:AWB9:1", "order_ref": "SMY-API-1", "type": "order.placed", "asserted_by": "merchant",
         "occurred_at": "2026-09-29T10:00:00+05:30", "source_adapter": "oms", "data": {"amount_inr": 349}},
        {"event_id": "shiprocket:AWB9:1", "order_ref": "SMY-API-1", "type": "order.placed", "asserted_by": "merchant",
         "occurred_at": "2026-09-29T10:00:00+05:30", "source_adapter": "oms", "data": {"amount_inr": 349}},
        {"event_id": "bad", "order_ref": "SMY-API-1", "type": "shipment.status", "asserted_by": "carrier",
         "occurred_at": "2026-09-29T10:00:00+05:30", "source_adapter": "oms"},
        {"event_id": "sneaky", "order_ref": "SMY-API-1", "type": "engine.resolution", "asserted_by": "engine",
         "occurred_at": "2026-09-29T10:00:00+05:30", "source_adapter": "oms", "data": {}},
    ]}
    first = client.post("/v1/events", headers={**sk(), "Idempotency-Key": "k-1"}, json=batch)
    assert first.status_code == 202
    body = first.json()
    assert (body["accepted"], body["duplicates"], [r["event_id"] for r in body["rejected"]]) == (1, 1, ["bad", "sneaky"])
    replay = client.post("/v1/events", headers={**sk(), "Idempotency-Key": "k-1"}, json=batch)
    assert replay.json() == body and replay.headers["Idempotent-Replayed"] == "true"
    clash = client.post("/v1/events", headers={**sk(), "Idempotency-Key": "k-1"}, json={"events": batch["events"][:1]})
    assert clash.status_code == 409 and clash.json()["error"]["code"] == "idempotency_key_reused"


def test_signed_events_are_verified(client):
    event = {"event_id": "sig-1", "order_ref": "SMY-SIG", "type": "order.placed", "asserted_by": "merchant",
             "occurred_at": "2026-09-29T10:00:00+05:30", "source_adapter": "oms", "data": {"amount_inr": 100}}
    body = json.dumps(event)
    good = webhooks.headers(TENANTS["smytten"].webhook_secret, "msg_1", body)
    r = client.post("/v1/events", headers={**sk(), **good, "content-type": "application/json"}, content=body)
    assert r.status_code == 202 and r.json()["accepted"] == 1
    forged = {**good, "webhook-signature": "v1,AAAA"}
    r = client.post("/v1/events", headers={**sk(), **forged, "content-type": "application/json"}, content=body)
    assert r.status_code == 401 and r.json()["error"]["code"] == "signature_invalid"
    stale = webhooks.headers(TENANTS["smytten"].webhook_secret, "msg_2", body, timestamp=int(time.time()) - 900)
    assert client.post("/v1/events", headers={**sk(), **stale}, content=body).status_code == 401


def test_order_upsert_then_courier_proof_pauses_a_pending_refund(client):
    order = {"order_id": "SMY-API-2", "customer_ref": "cus_77", "amount_inr": 799, "items": ["Serum 5 ml"],
             "customer": {"account_age_days": 800, "orders_90d": 9, "remedies_90d": 0},
             "eta": {"due_by": "2026-10-05T23:59:00+05:30"}}
    made = client.post("/v1/orders", headers=sk(), json=order)
    assert made.status_code == 201 and made.json()["view"]["state"] == "placed"
    assert made.json()["view"]["eta"]["shown"].startswith("Arrives by")
    assert client.post("/v1/orders", headers=sk(), json=order).status_code == 200      # same content: no new version
    now = client.post("/v1/dev/advance", headers=sk(), json={"minutes": 1}).json()["now"]
    delivered = {"event_id": "dlv-1", "order_ref": "SMY-API-2", "type": "shipment.status", "status": "delivered",
                 "substatus": "delivered.delivered", "asserted_by": "carrier", "occurred_at": now,
                 "source_adapter": "shiprocket", "raw": {"carrier": "Blue Dart", "code": "DL"},
                 "proof": {"otp_verified": False}}
    client.post("/v1/events", headers=sk(), json=delivered)
    h = browser(client, "SMY-API-2", customer_ref="cus_77")
    res = client.post("/v1/orders/SMY-API-2/actions", headers=h, json={"action": "report_not_received"}).json()
    assert res["view"]["resolution"]["decision"] == "investigate_and_refund"
    now = client.post("/v1/dev/advance", headers=sk(), json={"hours": 2}).json()["now"]
    proof = {**delivered, "event_id": "dlv-2", "occurred_at": now, "proof": {"otp_verified": True}}
    client.post("/v1/events", headers=sk(), json=proof)
    res = client.get("/v1/orders/SMY-API-2/view", headers=sk()).json()["view"]["resolution"]
    assert res["decision"] == "escalate_human" and "Blue Dart has now shared proof" in res["shopper_message"]
    assert hooks(client)[-2:] == ["order.proof_changed", "remedy.cancelled"]


def test_bodies_that_are_not_utf8_json_are_a_400(client):
    r = client.post("/v1/orders", headers={**sk(), "content-type": "application/json"},
                    content='{"order_id": "X", "amount_inr": 1, "title": "Box · 3"}'.encode("cp1252"))
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_json"


def test_unknown_orders_and_actions_are_clear_errors(client):
    r = client.get("/v1/orders/nope/view", headers=sk())
    assert r.status_code == 404 and "ord_test_unproven" in r.json()["error"]["message"]
    r = client.post("/v1/orders/ord_test_unproven/actions", headers=sk(), json={"action": "refund_me"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_action"


def test_appearance_is_validated_and_readable_with_a_publishable_key(client):
    ok = client.put("/v1/config", headers=sk(), json={"appearance": {"theme": "neutral",
                                                                      "variables": {"colorAction": "#E4007C"}}})
    assert ok.json()["appearance"] == {"theme": "neutral", "variables": {"colorAction": "#E4007C"}}
    pk = {"Authorization": f"Bearer {TENANTS['smytten'].publishable_key}"}
    assert client.get("/v1/client_config", headers=pk).json()["appearance"]["variables"]["colorAction"] == "#E4007C"
    for bad in ({"colorAction": "red;} body{display:none"}, {"notAToken": "#fff"}):
        r = client.put("/v1/config", headers=sk(), json={"appearance": {"variables": bad}})
        assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_appearance"
