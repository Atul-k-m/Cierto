"""Stateless instances: sessions are op logs in a shared store, so two apps (two caches, one store) are one service.

Every test runs against the in-memory store and against Redis (fakeredis), with two or three independent app
instances standing in for replicas behind a round-robin load balancer.
"""
import itertools
import warnings

import pytest

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fastapi.testclient import TestClient

from wismo import resolver
from wismo.api import create_app
from wismo.sdk import TENANTS, TEST_CUSTOMER
from wismo.sessions import Reply, Sessions
from wismo.shared import MemoryBackend, RedisBackend


def _redis_backend():
    fakeredis = pytest.importorskip("fakeredis")
    backend = RedisBackend("redis://unused:6379/0")
    backend.r = fakeredis.FakeRedis(server=fakeredis.FakeServer(), decode_responses=True)
    return backend


@pytest.fixture(params=["memory", "redis"])
def backend(request):
    return MemoryBackend() if request.param == "memory" else _redis_backend()


@pytest.fixture()
def instances(backend, tmp_path):
    """Three replicas: independent apps (own caches), one shared store."""
    (tmp_path / "index.html").write_text("<!doctype html>", encoding="utf-8")
    return [TestClient(create_app(backend, web_dist=tmp_path)) for _ in range(3)]


def test_two_instances_give_identical_results_for_the_same_op_sequence(instances):
    a, b, c = instances
    sid = a.post("/v1/demo/sessions").json()["id"]
    b.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "claimed"})
    a.post(f"/v1/demo/sessions/{sid}/orders/zomato/actions", json={"action": "talk_to_person"})
    b.post(f"/v1/demo/sessions/{sid}/orders/smytten-delivered/actions",
           json={"action": "report_not_received", "locale": "hi-Latn-IN"})
    a.post(f"/v1/demo/sessions/{sid}/orders/zomato/approve", json={"approved_by": "ops@zomato.example"})
    b.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "next_day"})

    reads = [f"/v1/demo/sessions/{sid}", f"/v1/demo/sessions/{sid}/webhooks",
             f"/v1/demo/sessions/{sid}/orders/zomato/case", f"/v1/demo/sessions/{sid}/orders/smytten-delivered/case"]
    for path in reads:
        seen = [x.get(path).json() for x in (a, b, c)]   # c has never seen this session: it replays the whole log
        assert seen[0] == seen[1] == seen[2], path
    hooks = a.get(f"/v1/demo/sessions/{sid}/webhooks").json()["data"]
    assert len(hooks) >= 6 and len({h["id"] for h in hooks}) == len(hooks)          # ids: seeded, unique, identical
    case = b.get(f"/v1/demo/sessions/{sid}/orders/smytten-delivered/case").json()
    assert case["resolution"]["remedy"]["id"].startswith("rem_") and case["state"] == "delivery_disputed"
    assert c.get(f"/v1/demo/sessions/{sid}/orders/smytten-delivered").json()["view"]["refund"]["stage"] == "initiated"
    # The same ops on a second session give the same decisions, with this session's own webhook ids.
    other = b.post("/v1/demo/sessions").json()["id"]
    assert {h["id"] for h in b.get(f"/v1/demo/sessions/{other}/webhooks").json()["data"]}.isdisjoint(
        {h["id"] for h in hooks})


def test_unknown_or_expired_sessions_keep_the_404_contract(instances, backend):
    a, b, _ = instances
    assert a.get("/v1/demo/sessions/0123456789ab").status_code == 404
    assert a.get("/v1/demo/sessions/not-a-session-id").json() == {"detail": "session not found; start a new one"}
    sid = a.post("/v1/demo/sessions").json()["id"]
    assert b.get(f"/v1/demo/sessions/{sid}").status_code == 200
    backend.log_drop(f"demo:{sid}")                                                   # what an idle TTL does
    for x in (a, b):
        r = x.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "claimed"})
        assert r.status_code == 404 and r.json()["detail"] == "session not found; start a new one"


def test_model_output_is_recorded_once_and_replayed_everywhere(instances, monkeypatch):
    """A rewording is written into the op; the other instance reads it back instead of calling (and paying) again."""
    phrases, calls = itertools.cycle(["Sorted.", "On it.", "Thanks for waiting."]), []

    def fake_gemini(payload, system, schema):
        calls.append(payload)
        if "answer" in schema["required"]:
            return {"answer": payload["answer"]}
        return {"shopper_message": f"{payload['shopper_message']} {next(phrases)}", "agent_summary": payload["agent_summary"]}
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(resolver, "_gemini_call", fake_gemini)
    a, b, c = instances
    sid = a.post("/v1/demo/sessions").json()["id"]
    a.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "claimed"})
    live = a.post(f"/v1/demo/sessions/{sid}/orders/zomato/actions", json={"action": "report_not_received"}).json()
    made = len(calls)
    assert made >= 1 and live["view"]["resolution"]["shopper_message"].endswith((".", "!"))
    for x in (b, c):
        replayed = x.get(f"/v1/demo/sessions/{sid}/orders/zomato").json()
        assert replayed["view"]["resolution"] == live["view"]["resolution"]
        assert x.get(f"/v1/demo/sessions/{sid}/orders/zomato/case").json()["resolution"]["llm"]["rephrased"] is True
    assert len(calls) == made                                                          # no call during replay


def test_a_lost_race_rebuilds_from_the_log_and_plans_again(backend):
    """Two replicas plan on the same version; the loser is rebuilt from the log and its op re-planned on top."""
    def apply(name, state, op):
        return (state or []) + [op["n"]], None
    one, two = Sessions(backend, apply, ttl=60), Sessions(backend, apply, ttl=60)
    one.create("race", {"n": 0}, lambda s, _: s)
    two.read("race", lambda s: s)                                   # both caches hold version 1
    raced = []

    def plan(state):
        if not raced:                                               # while "two" plans, "one" commits first
            raced.append(one.write("race", lambda s: {"n": 1}, lambda s, _: list(s)))
        return {"n": len(state)}
    assert two.write("race", plan, lambda s, _: list(s)) == [0, 1, 2]
    assert one.read("race", list) == [0, 1, 2] and raced == [[0, 1]]
    assert one.write("race", lambda s: Reply("nothing to do"), lambda s, _: s) == "nothing to do"


def test_live_sessions_are_capped(backend):
    def apply(name, state, op):
        return op, None
    mgr = Sessions(backend, apply, ttl=60, pool="demo", cap=3)
    for i in range(5):
        mgr.create(f"demo:s{i}", {"i": i}, lambda s, _: s)
    mgr.clear()
    alive = []
    for i in range(5):
        try:
            mgr.read(f"demo:s{i}", lambda s: s)
            alive.append(i)
        except LookupError:
            pass
    assert alive == [2, 3, 4]                                        # the least recently used went first


def _sk(t="smytten"):
    return {"Authorization": f"Bearer {TENANTS[t].secret_key}"}


def test_sdk_sandbox_state_is_shared_across_instances(instances):
    a, b, c = instances
    cs = a.post("/v1/customer_sessions", headers=_sk(), json={"order_id": "ord_test_unproven",
                                                              "customer_ref": TEST_CUSTOMER["ref"]}).json()["client_secret"]
    browser = {"Authorization": f"Bearer {TENANTS['smytten'].publishable_key}", "Cierto-Client-Secret": cs}
    assert b.get("/v1/orders/ord_test_unproven/view", headers=browser).status_code == 200   # minted on a, honoured on b
    order = {"order_id": "SMY-LB-1", "customer_ref": "cus_1", "amount_inr": 499, "eta": {"due_by": "2030-01-01T10:00:00+05:30"}}
    first = a.post("/v1/orders", headers={**_sk(), "Idempotency-Key": "lb-1"}, json=order)
    again = b.post("/v1/orders", headers={**_sk(), "Idempotency-Key": "lb-1"}, json=order)
    assert first.status_code == 201 and again.headers["Idempotent-Replayed"] == "true" and again.json() == first.json()
    assert c.put("/v1/config", headers=_sk(), json={"policy": {"auto_refund_cap_inr": 2500}}).json()["version"] == 2
    assert a.get("/v1/config", headers=_sk()).json()["policy"]["auto_refund_cap_inr"] == 2500
    b.post("/v1/orders/ord_test_unproven/actions", headers=browser, json={"action": "report_not_received"})
    assert c.post("/v1/dev/advance", headers=_sk(), json={"hours": 25}).status_code == 200
    views = [x.get("/v1/orders/ord_test_unproven/view", headers=_sk()).json()["view"] for x in (a, b, c)]
    assert {v["refund"]["stage"] for v in views} == {"initiated"}
    logs = [x.get("/v1/dev/webhook_log", headers=_sk()).json()["data"] for x in (a, b, c)]
    assert logs[0] == logs[1] == logs[2] and logs[0][0]["type"] == "remedy.executed"
    reset = b.post("/v1/dev/reset", headers=_sk()).json()
    assert reset["reset"] is True
    assert a.get("/v1/dev/webhook_log", headers=_sk()).json()["data"] == []            # a fresh log everywhere
    assert c.get("/v1/config", headers=_sk()).json()["policy"]["auto_refund_cap_inr"] == 2500   # config carried over
    assert a.get("/v1/orders/ord_test_unproven/view", headers=browser).status_code == 200      # and sessions


def test_webhook_sends_happen_once_after_commit(instances, monkeypatch):
    sent = []
    monkeypatch.setattr("wismo.webhooks.WebhookLog._send", lambda self, entry: sent.append(entry["id"]))
    a, b, _ = instances
    a.put("/v1/config", headers=_sk("zomato"), json={"webhook_url": "https://hooks.example/cierto"})
    b.post("/v1/orders/ord_test_unproven/actions", headers=_sk("zomato"), json={"action": "report_not_received"})
    for x in (a, b):
        x.get("/v1/dev/webhook_log", headers=_sk("zomato"))                             # replays send nothing
    import time
    time.sleep(0.2)
    ids = [w["id"] for w in a.get("/v1/dev/webhook_log", headers=_sk("zomato")).json()["data"]]
    assert sorted(sent) == sorted(ids) and len(sent) == len(set(sent)) >= 3


def test_a_poll_costs_one_redis_command(tmp_path):
    """Upstash bills per command: a caught-up read of a session is a single HLEN."""
    backend, calls = _redis_backend(), []
    real = backend.r

    class Spy:
        def __getattr__(self, name):
            calls.append(name)
            return getattr(real, name)
    backend.r = Spy()
    c = TestClient(create_app(backend, web_dist=tmp_path))
    sid = c.post("/v1/demo/sessions").json()["id"]
    c.get(f"/v1/demo/sessions/{sid}")
    calls.clear()
    c.get(f"/v1/demo/sessions/{sid}")
    assert calls == ["hlen"]
