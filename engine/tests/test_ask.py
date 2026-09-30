"""Grounded answers (ask), the six WISMO-cause demo orders, the demo console endpoints, and the Cierto rename."""
import re
import warnings
from datetime import datetime, timedelta

import pytest

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fastapi.testclient import TestClient

from wismo.api import SDK_DIST, SESSIONS, app, reset_state
from wismo.ask import classify, faithful, rephrase
from wismo.commitments import derive
from wismo.detectors import rider_stalled
from wismo.events import Event
from wismo.profiles import PARCEL, QUICK
from wismo.projection import project
from wismo.resolver import _clock, _day, _when
from wismo.sdk import DEFAULT_POLICIES, TENANTS, TEST_CUSTOMER

IST = datetime.fromisoformat("2025-12-24T14:00:00+05:30").tzinfo
SIX = {"rider_stalled": "swish-stalled", "traffic_delay": "zomato-traffic", "batched": "zomato-batched",
       "address_mismatch": "smytten-address", "courier_silent": "smytten-silent"}


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def demo(client):
    sid = client.post("/v1/demo/sessions").json()["id"]
    client.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "claimed"})
    return sid


def ask(client, sid, key, question, locale="en-IN"):
    r = client.post(f"/v1/demo/sessions/{sid}/orders/{key}/ask", json={"question": question, "locale": locale})
    assert r.status_code == 200, r.text
    return r.json()


def view(client, sid, key, locale="en-IN"):
    return client.get(f"/v1/demo/sessions/{sid}/orders/{key}?locale={locale}").json()["view"]


# ---- intent rules ---------------------------------------------------------------------------------

@pytest.mark.parametrize("question,intent", [
    ("where is my order??", "where"),
    ("tracking not updated for 3 days???", "where"),
    ("order kab aayega?", "when"),
    ("when will it arrive", "when"),
    ("it's been 15 min, still not here", "late"),
    ("bahut der ho gayi", "late"),
    ("where is my refund", "refund"),
    ("paise kab wapas aayenge", "refund"),
    ("it says delivered but i didnt get anything", "not_received"),
    ("order nahi mila", "not_received"),
    ("delivery guy called me, he cant find my house", "address"),
    ("please cancel my order", "cancel"),
    ("i want to talk to a human", "human"),
    ("customer care se baat karni hai", "human"),
    ("hello?", "where"),
])
def test_intent_rules(question, intent):
    assert classify(question) == intent


# ---- the six causes, at the "claimed" beat --------------------------------------------------------

def test_session_summary_lists_each_cause_with_its_orders(client):
    s = client.post("/v1/demo/sessions").json()
    causes = {c["id"]: c for c in s["causes"]}
    for cause, key in SIX.items():
        assert key in causes[cause]["orders"]
    assert set(causes["delivered_not_received"]["orders"]) == {"smytten-delivered", "zomato", "swish"}
    assert causes["rider_stalled"]["label"] == "Rider stuck"
    by_key = {o["key"]: o for o in s["orders"]}
    for key in ("swish", "zomato", "smytten-late", "smytten-refund", "smytten-ok"):   # existing keys still work
        assert key in by_key
    for cause, key in SIX.items():
        assert by_key[key]["cause"] == cause
        assert any(src.startswith("docs/research/wismo-") for src in by_key[key]["sources"])


def test_rider_stalled_names_the_rider_the_minutes_and_the_spot(client, demo):
    v = view(client, demo, "swish-stalled")
    assert (v["state"], v["tone"], v["reasons"]) == ("on_the_way", "check", ["rider_stalled"])
    assert v["cause"]["id"] == "rider_stalled"
    assert v["cause"]["text"] == "Anubhav has been stopped for 4 minutes near Agara junction"
    a = ask(client, demo, "swish-stalled", "where is my order?? it's been 15 min")
    assert a["cause"] == "rider_stalled" and a["stale"] is False
    assert "Anubhav has been stopped for 4 minutes near Agara junction" in a["answer"]
    assert "Rider GPS" in [s["name"] for s in a["sources"]]
    feed = client.get(f"/v1/demo/sessions/{demo}").json()["feed"]
    assert any(f["rule"] == "rider_stalled" and f["order"] == "swish-stalled" for f in feed)
    hi = ask(client, demo, "swish-stalled", "order kahan hai?", "hi-Latn-IN")
    assert "Agara junction ke paas 4 minute se ruke hue hain" in hi["answer"]


def test_rider_stall_threshold_is_per_vertical():
    base = datetime(2025, 12, 24, 13, 58, tzinfo=IST)
    events = [Event(event_id="p", tenant_id="t", order_ref="o", type="order.placed", occurred_at=base - timedelta(minutes=10),
                    asserted_by="merchant", source_adapter="t", data={"amount_inr": 100})]
    events += [Event(event_id=f"g{i}", tenant_id="t", order_ref="o", type="rider.location",
                     occurred_at=base + timedelta(minutes=i), asserted_by="rider", source_adapter="t",
                     data={"lat": 12.9237 + i * 1e-5, "lng": 77.648, "near": "Agara junction"}) for i in range(6)]
    now = base + timedelta(minutes=5)
    for profile, fires in ((QUICK, True), (PARCEL, False)):
        p = project(events, now, profile)
        assert p.rider_stopped_for == timedelta(minutes=5)
        assert (rider_stalled(p, derive(p, profile, now), profile, now) is not None) is fires


def test_traffic_delay_shows_now_expected_and_latest_by(client, demo):
    v = view(client, demo, "zomato-traffic")
    assert v["cause"]["id"] == "traffic_delay" and "Traffic on Hosur Road added 9 minutes" in v["cause"]["text"]
    assert (v["eta"]["expected"], v["eta"]["latest_by"]) == ("2025-12-24T14:04:00+05:30", "2025-12-24T14:10:00+05:30")
    assert (v["eta"]["reason"], v["eta"]["delay_minutes"], v["eta"]["state"]) == ("traffic", 9, "open")
    assert [h["due"] for h in v["eta"]["history"]] == ["2025-12-24T13:55:00+05:30"]
    a = ask(client, demo, "zomato-traffic", "when will it arrive")
    assert a["intent"] == "when" and a["answer"].startswith("Now expected by 2:04 pm, and no later than 2:10 pm.")
    assert a["promise"] == {"now": "2025-12-24T14:04:00+05:30", "latest_by": "2025-12-24T14:10:00+05:30", "fallback": None}
    late = ask(client, demo, "zomato-traffic", "order kab aayega? bahut late ho gaya", "hi-Latn-IN")
    assert late["intent"] == "late" and "traffic ki wajah se 9 minute" in late["answer"]


def test_batched_explains_the_drop_first_without_the_other_order(client, demo):
    v = view(client, demo, "zomato-batched")
    assert v["cause"]["id"] == "batched"
    assert "one other order first, 600 m from you" in v["cause"]["text"]
    a = ask(client, demo, "zomato-batched", "why is the rider going the other way?")
    assert "one other order first, 600 m from you" in a["answer"] and "2:10 pm" in a["answer"]
    assert "ZMT-7729381091" not in str(a) + str(v)                     # the other shopper's order stays private
    client.post(f"/v1/demo/sessions/{demo}/advance", json={"minutes": 5})
    assert (view(client, demo, "zomato-batched")["cause"] or {}).get("id") != "batched"   # the other drop is done


def test_address_mismatch_offers_a_fix_and_the_fix_settles_it(client, demo):
    v = view(client, demo, "smytten-address")
    assert (v["state"], v["tone"]) == ("out_for_delivery", "check")
    assert v["actions"][0] == {"id": "fix_address", "primary": True}
    assert "1.2 km from the address you typed" in v["cause"]["text"] and "by 3:00 pm" in v["cause"]["text"]
    a = ask(client, demo, "smytten-address", "delivery guy called me, he cant find my house")
    assert a["intent"] == "address" and a["cause"] == "address_mismatch"
    assert {"id": "fix_address", "primary": True, "label": "Confirm the right spot"} in a["actions"]
    fixed = client.post(f"/v1/demo/sessions/{demo}/orders/smytten-address/actions",
                        json={"action": "fix_address", "landmark": "Opp. Blue Ridge gate 2"}).json()["view"]
    assert fixed["cause"] is None and fixed["tone"] == "calm"
    assert "fix_address" not in [x["id"] for x in fixed["actions"]]
    assert "landmark: Opp. Blue Ridge gate 2" in fixed["resolution"]["steps"][0]["text"]
    again = ask(client, demo, "smytten-address", "rider cant find my house")
    assert again["answer"].startswith("You confirmed the delivery spot on Wed 24 Dec, 2:02 pm")


def test_courier_silent_names_last_scan_and_the_auto_remedy_deadline(client, demo):
    a = ask(client, demo, "smytten-silent", "tracking not updated for 3 days???")
    assert a["cause"] == "courier_silent" and a["stale"] is True
    assert a["answer"].startswith("Delhivery hasn't scanned your parcel since Sun 21 Dec, 10:40 am, at the Bhiwandi hub.")
    assert "If it isn't delivered by Thu 25 Dec, 1:40 pm, your ₹549 refund goes out automatically" in a["answer"]
    assert a["promise"]["fallback"]["at"] == "2025-12-24T13:40:00+05:30".replace("24T", "25T")
    assert a["promise"]["now"] is None and a["promise"]["latest_by"] == "2025-12-23T23:59:00+05:30"
    client.post(f"/v1/demo/sessions/{demo}/advance", json={"beat": "next_day"})   # nothing came: the refund went out
    later = ask(client, demo, "smytten-silent", "refund?")
    assert later["answer"].startswith("We started your ₹549 refund on Thu 25 Dec")
    assert later["promise"]["fallback"] is None


def test_delivered_not_received_names_missing_proof_and_the_report_window(client, demo):
    a = ask(client, demo, "zomato", "it says delivered but i didnt get anything")
    assert a["intent"] == "not_received" and a["cause"] == "delivered_not_received"
    assert "no OTP was used and no photo was taken" in a["answer"] and "by 2:42 pm" in a["answer"]
    assert [x["id"] for x in a["actions"]] == ["confirm_received", "report_not_received"]


# ---- grounding ------------------------------------------------------------------------------------

def _datetimes(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _datetimes(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _datetimes(v)
    elif isinstance(obj, str) and re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", obj):
        yield datetime.fromisoformat(obj)


def test_answers_state_no_time_or_date_that_is_not_in_the_data(client):
    questions = ["where is my order", "when will it come", "why is it late", "refund kab milega",
                 "i didnt get it", "rider cant find my house", "cancel it", "talk to a person"]
    sid = client.post("/v1/demo/sessions").json()["id"]
    session = SESSIONS[sid]
    for beat in ("riding", "claimed", "ten_min", "next_day"):
        client.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": beat})
        for key, o in session.orders.items():
            events = session.engine.events(o["tenant"], o["order_ref"])
            known = {e.occurred_at for e in events} | set(_datetimes([e.data for e in events]))
            known |= set(_datetimes(view(client, sid, key)))
            times = {_clock(d) for d in known}
            days = {_day(d) for d in known} | {_when(d).split(",")[0] for d in known}
            for q in questions:
                for locale in ("en-IN", "hi-Latn-IN"):
                    text = ask(client, sid, key, q, locale)["answer"]
                    for t in re.findall(r"\b\d{1,2}:\d{2} [ap]m\b", text):
                        assert t in times, (beat, key, q, t, text)
                    for d in re.findall(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d{1,2} [A-Z][a-z]{2}\b", text):
                        assert d in days, (beat, key, q, d, text)


def test_stale_tracking_is_called_out(client):
    sid = client.post("/v1/demo/sessions").json()["id"]
    client.post(f"/v1/demo/sessions/{sid}/advance", json={"beat": "next_day"})
    a = ask(client, sid, "smytten-address", "where is it")              # out for delivery since yesterday, silent
    assert a["stale"] is True and "Heads-up: the latest update from Delhivery tracking was 27 hours ago" in a["answer"]
    fresh = client.post("/v1/demo/sessions").json()["id"]
    client.post(f"/v1/demo/sessions/{fresh}/advance", json={"beat": "claimed"})
    assert ask(client, fresh, "zomato-traffic", "where is it")["stale"] is False   # pings every 2 minutes


def test_answer_has_exactly_the_documented_shape(client, demo):
    a = ask(client, demo, "smytten-silent", "where is my parcel")
    assert set(a) == {"object", "intent", "answer", "cause", "promise", "sources", "stale", "actions", "rephrased"}
    assert set(a["promise"]) == {"now", "latest_by", "fallback"} and set(a["promise"]["fallback"]) == {"at", "text"}
    assert all(set(s) == {"name", "age_seconds"} and s["age_seconds"] >= 0 for s in a["sources"])
    assert all(set(x) == {"id", "primary", "label"} for x in a["actions"])
    assert a["object"] == "order_answer" and a["rephrased"] is False
    bad = client.post(f"/v1/demo/sessions/{demo}/orders/zomato/ask", json={"question": ""})
    assert bad.status_code == 422


# ---- the optional LLM rewrite ---------------------------------------------------------------------

ANSWER = ("Now expected by 2:04 pm, and no later than 2:10 pm. Traffic on Hosur Road added 9 minutes; "
          "Rahul is 1.3 km away.")


@pytest.mark.parametrize("rewrite,ok", [
    ("Rahul is 1.3 km away. Traffic on Hosur Road added 9 minutes, so it's now expected by 2:04 pm, "
     "and no later than 2:10 pm.", True),
    ("Now expected by 2:05 pm, and no later than 2:10 pm. Traffic on Hosur Road added 9 minutes; Rahul is 1.3 km away.", False),
    ("Now expected by 2:04 pm. Traffic on Hosur Road added 9 minutes; Rahul is 1.3 km away.", False),     # dropped 2:10
    ("Now expected today by 2:04 pm, no later than 2:10 pm. Traffic added 9 minutes; Rahul is 1.3 km away.", False),
    ("Now expected by 2:04 pm, no later than 2:10 pm. Traffic added 9 minutes; Rahul is 1.3 km away, 3 stops.", False),
])
def test_faithful_rejects_any_changed_number_time_or_day(rewrite, ok):
    assert faithful(ANSWER, rewrite) is ok


def test_rephrase_keeps_the_template_unless_the_rewrite_is_faithful(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    body = {"intent": "when", "answer": ANSWER, "rephrased": False}
    assert rephrase(body, {}, "kab?", "en-IN") is body                        # no key: templates only
    good = "Rahul is 1.3 km away. Traffic on Hosur Road added 9 minutes: now expected by 2:04 pm, no later than 2:10 pm."
    out = rephrase(body, {}, "kab?", "en-IN", call=lambda payload: {"answer": good})
    assert out["answer"] == good and out["rephrased"] is True
    seen = {}
    rephrase(body, {"cause": "traffic_delay"}, "kab?", "en-IN", call=lambda payload: seen.update(payload) or {"answer": good})
    assert seen["facts"] == {"cause": "traffic_delay"} and seen["answer"] == ANSWER   # facts go as data
    for call in (lambda p: {"answer": "It'll be there by 2:30 pm."}, lambda p: 1 / 0):
        assert rephrase(body, {}, "kab?", "en-IN", call=call) == body


# ---- the SDK endpoint -----------------------------------------------------------------------------

@pytest.fixture()
def fresh_tenants():
    reset_state()


def test_sdk_ask_with_a_publishable_key_and_client_secret(client, fresh_tenants):
    t = TENANTS["zomato"]
    sk = {"Authorization": f"Bearer {t.secret_key}"}
    assert t.publishable_key.startswith("pk_test_cierto_zomato_") and t.secret_key.startswith("sk_test_cierto_zomato_")
    cs = client.post("/v1/customer_sessions", headers=sk,
                     json={"order_id": "ord_test_qc_late", "customer_ref": TEST_CUSTOMER["ref"]}).json()["client_secret"]
    h = {"Authorization": f"Bearer {t.publishable_key}", "Cierto-Client-Secret": cs}
    a = client.post("/v1/orders/ord_test_qc_late/ask", headers=h, json={"question": "khana kab aayega?",
                                                                         "locale": "hi-Latn-IN"}).json()
    assert a["intent"] == "when" and a["cause"] == "courier_silent" and a["stale"] is True
    assert "min late hai" in a["answer"]
    old = {"Authorization": f"Bearer {t.publishable_key}", "Pakka-Client-Secret": cs}   # pre-rename header
    assert client.post("/v1/orders/ord_test_qc_late/ask", headers=old, json={"question": "where"}).status_code == 200
    wrong = client.post("/v1/orders/ord_test_unproven/ask", headers=h, json={"question": "where"})
    assert wrong.status_code == 403 and wrong.json()["error"]["code"] == "client_secret_wrong_order"
    empty = client.post("/v1/orders/ord_test_qc_late/ask", headers=sk, json={"question": ""})
    assert empty.status_code == 400 and empty.json()["error"]["code"] == "invalid_parameters"
    missing = client.post("/v1/orders/nope/ask", headers=sk, json={"question": "where"})
    assert missing.status_code == 404


def test_new_event_types_are_validated_on_ingest(client, fresh_tenants):
    sk = {"Authorization": f"Bearer {TENANTS['zomato'].secret_key}"}
    base = {"order_ref": "ZMT-EV-1", "occurred_at": "2025-09-30T13:00:00+05:30", "source_adapter": "test"}
    batch = {"events": [
        {**base, "event_id": "ok-1", "type": "order.placed", "asserted_by": "merchant", "data": {"amount_inr": 300}},
        {**base, "event_id": "ok-2", "type": "eta.revised", "asserted_by": "merchant",
         "data": {"reason": "traffic", "expected_by": "2026-09-30T13:30:00+05:30", "latest_by": "2026-09-30T13:40:00+05:30"}},
        {**base, "event_id": "ok-3", "type": "rider.location", "asserted_by": "rider", "data": {"lat": 12.9, "lng": 77.6}},
        {**base, "event_id": "bad-1", "type": "eta.revised", "asserted_by": "merchant", "data": {"expected_by": "13:30"}},
        {**base, "event_id": "bad-2", "type": "rider.location", "asserted_by": "rider", "data": {"near": "Agara"}},
        {**base, "event_id": "bad-3", "type": "address.check", "asserted_by": "merchant", "data": {}},
        {**base, "event_id": "bad-4", "type": "dispatch.stop_sequence", "asserted_by": "merchant", "data": {"stops": []}},
    ]}
    r = client.post("/v1/events", headers=sk, json=batch).json()
    assert r["accepted"] == 3 and [x["event_id"] for x in r["rejected"]] == ["bad-1", "bad-2", "bad-3", "bad-4"]
    future = {**base, "order_ref": "ZMT-EV-2", "event_id": "later", "type": "order.placed", "asserted_by": "merchant",
              "occurred_at": "2099-01-01T10:00:00+05:30", "data": {"amount_inr": 1}}
    assert client.post("/v1/events", headers=sk, json=future).status_code == 202   # stored; it happens when it happens


# ---- demo console: case, webhooks, approve --------------------------------------------------------

def test_case_endpoint_and_the_demo_approval_loop(client, demo):
    assert client.post(f"/v1/demo/sessions/{demo}/orders/zomato/approve", json={}).status_code == 409   # nothing yet
    r = client.post(f"/v1/demo/sessions/{demo}/orders/zomato/actions", json={"action": "talk_to_person"}).json()
    assert r["view"]["resolution"]["needs_approval"] is True        # a person confirms the policy's proposal
    case = client.get(f"/v1/demo/sessions/{demo}/orders/zomato/case").json()
    assert set(case) == {"object", "order", "case_id", "state", "tone", "cause", "holder", "issue", "clocks", "proof",
                         "timeline", "resolution", "webhooks", "policy"}
    assert case["resolution"]["status"] == "proposed" and case["resolution"]["trust"]["score"] >= 0.6
    assert case["policy"] == {"source": "resolution", "values": DEFAULT_POLICIES["zomato"].model_dump()}
    assert case["proof"]["otp"] == "not_used" and case["case_id"].startswith("#")
    assert {"at", "type", "asserted_by", "source", "text"} == set(case["timeline"][0])
    assert case["timeline"][-1]["type"] == "engine.resolution" and case["timeline"][-1]["source"] == "cierto.resolver"
    ok = client.post(f"/v1/demo/sessions/{demo}/orders/zomato/approve", json={"approved_by": "ops@zomato.example"})
    assert ok.status_code == 200 and ok.json()["view"]["refund"]["stage"] == "initiated"
    assert client.post(f"/v1/demo/sessions/{demo}/orders/zomato/approve", json={}).status_code == 409
    mine = [w["type"] for w in client.get(f"/v1/demo/sessions/{demo}/webhooks?order=zomato").json()["data"]]
    assert mine == ["remedy.executed", "remedy.approved", "remedy.proposed", "case.opened"]
    everything = client.get(f"/v1/demo/sessions/{demo}/webhooks").json()["data"]
    assert len(everything) > len(mine)                                 # smytten-silent's scripted report is there too
    after = client.get(f"/v1/demo/sessions/{demo}/orders/zomato/case").json()
    assert after["resolution"]["approved_by"] == "ops@zomato.example" and len(after["webhooks"]) == 4
    quiet = client.get(f"/v1/demo/sessions/{demo}/orders/smytten-ok/case").json()
    assert quiet["resolution"] is None and quiet["policy"]["source"] == "host_default" and quiet["webhooks"] == []
    assert client.get(f"/v1/demo/sessions/{demo}/orders/nope/case").status_code == 404


# ---- the rename -----------------------------------------------------------------------------------

@pytest.mark.skipif(not (SDK_DIST / "cierto.js").is_file(), reason="SDK not built")
def test_sdk_bundle_is_cierto_and_pakka_js_is_an_alias(client):
    new, old = client.get("/sdk/cierto.js"), client.get("/sdk/pakka.js")
    assert new.status_code == old.status_code == 200 and new.content == old.content
    assert b"Cierto" in new.content and b"cierto-order" in new.content
    assert client.get("/sdk/cierto.mjs").content == client.get("/sdk/pakka.mjs").content
    assert client.get("/sdk/react.mjs").status_code == 200


def test_api_title_is_cierto(client):
    assert client.get("/openapi.json").json()["info"]["title"] == "Cierto API"
