"""The app-level WAF (waf.py): client IP, hygiene, rate limits, the LLM budget, security headers, access logs."""
import json
import logging
import warnings

import pytest

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fastapi.testclient import TestClient

from wismo import resolver, waf
from wismo.api import create_app
from wismo.shared import MemoryBackend
from wismo.waf import WafConfig, client_ip, parse_rates


@pytest.fixture()
def dist(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>Cierto</title>", encoding="utf-8")
    (tmp_path / "404.html").write_text("<!doctype html><title>404</title>", encoding="utf-8")
    return tmp_path


def make(dist, base_url="http://testserver", **limits):
    cfg = WafConfig(**{k: parse_rates(v) if isinstance(v, str) else v for k, v in limits.items()})
    return TestClient(create_app(MemoryBackend(), web_dist=dist, waf=cfg), base_url=base_url)


def test_client_ip_counts_trusted_hops_from_the_right():
    scope = {"headers": [(b"x-forwarded-for", b"6.6.6.6, 203.0.113.9, 10.0.0.2")], "client": ("10.0.0.3", 1)}
    assert client_ip(scope, 1) == "10.0.0.2"          # Caddy / Cloud Run: the address the proxy saw
    assert client_ip(scope, 2) == "203.0.113.9"       # behind a Google external Application Load Balancer
    assert client_ip(scope, 0) == "10.0.0.3"          # no proxy: the socket peer
    assert client_ip(scope, 5) == "6.6.6.6"           # fewer entries than hops: the furthest one
    assert client_ip({"headers": [], "client": ("1.2.3.4", 1)}, 1) == "1.2.3.4"


def test_parse_rates():
    assert parse_rates("20/m, 200/d") == [(20, 60), (200, 86400)]
    assert parse_rates("20/10m") == [(20, 600)] and parse_rates("5/30s") == [(5, 30)] and parse_rates("") == []


def test_general_limit_is_per_ip_and_answers_429_with_retry_after(dist):
    c = make(dist, general="3/m")
    ip = {"x-forwarded-for": "198.51.100.7"}
    assert [c.get("/", headers=ip).status_code for _ in range(3)] == [200, 200, 200]
    r = c.get("/", headers=ip)
    assert r.status_code == 429 and 0 < int(r.headers["retry-after"]) <= 61
    assert r.json()["error"] == {"type": "rate_limit_error", "code": "rate_limited", "message": r.json()["error"]["message"]}
    spoofed = {"x-forwarded-for": "1.1.1.1, 198.51.100.7"}                  # a forged left-most entry changes nothing
    assert c.get("/", headers=spoofed).status_code == 429
    assert c.get("/", headers={"x-forwarded-for": "198.51.100.8"}).status_code == 200
    assert c.get("/healthz", headers=ip).status_code == 200                 # probes are never limited


def test_ask_and_demo_creation_have_their_own_limits(dist):
    c = make(dist, ask="2/m", demo_create="2/10m")
    sids = [c.post("/v1/demo/sessions").status_code for _ in range(3)]
    assert sids == [200, 200, 429]
    sid = c.get("/v1/demo/sessions/0123456789ab").status_code                # reads are not demo creations
    assert sid == 404
    first = make(dist, ask="2/m")
    s = first.post("/v1/demo/sessions").json()["id"]
    codes = [first.post(f"/v1/demo/sessions/{s}/orders/zomato/ask", json={"question": "where"}).status_code
             for _ in range(3)]
    assert codes == [200, 200, 429]
    assert first.get(f"/v1/demo/sessions/{s}/orders/zomato").status_code == 200


def test_body_size_methods_scanners_and_uri_length(dist):
    c = make(dist, max_body=200)
    big = {"question": "x" * 400}
    assert c.post("/v1/demo/sessions/0123456789ab/orders/zomato/ask", json=big).status_code == 413
    chunked = c.post("/v1/demo/sessions/0123456789ab/orders/zomato/ask", content=iter([b"{" + b" " * 300, b"}"]))
    assert chunked.status_code == 413                                       # no Content-Length: counted as it streams
    r = c.request("DELETE", "/v1/demo/sessions")
    assert r.status_code == 405 and "POST" in r.headers["allow"]
    for path in ("/wp-login.php", "/.env", "/.git/config", "/phpmyadmin/", "/cgi-bin/luci", "/v1/x.php", "/backup.sql"):
        r = c.get(path)
        assert r.status_code == 404 and r.text == "Not Found" and r.headers["content-type"].startswith("text/plain"), path
    assert c.get("/?q=" + "a" * 5000).status_code == 414
    assert c.get("/", headers={"x-junk": "a" * 20000}).status_code == 431


def test_security_headers_csp_and_hsts(dist):
    http = make(dist)
    page = http.get("/")
    for name in ("x-content-type-options", "referrer-policy", "permissions-policy", "cross-origin-opener-policy",
                 "content-security-policy", "x-served-by"):
        assert name in page.headers, name
    assert "strict-transport-security" not in page.headers
    assert "upgrade-insecure-requests" not in page.headers["content-security-policy"]   # plain-http localhost
    api = http.get("/healthz")
    assert "content-security-policy" not in api.headers and api.headers["x-content-type-options"] == "nosniff"
    secure = make(dist, base_url="https://testserver").get("/")
    assert secure.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"
    assert secure.headers["content-security-policy"].endswith("; upgrade-insecure-requests")
    assert "frame-ancestors 'self'" in secure.headers["content-security-policy"]


def test_cors_is_open_for_the_sdk_and_closed_for_the_demo(dist):
    c = make(dist)
    pre = {"origin": "https://shop.example", "access-control-request-method": "POST"}
    assert c.options("/v1/orders/x/ask", headers=pre).headers.get("access-control-allow-origin") == "*"
    assert "access-control-allow-origin" not in c.options("/v1/demo/sessions", headers=pre).headers


def test_crawlers_are_welcome_and_empty_user_agents_cannot_write(dist):
    c = make(dist)
    for ua in ("Mozilla/5.0 (compatible; Googlebot/2.1)", "GPTBot/1.1", "ClaudeBot/1.0", "PerplexityBot/1.0",
               "OAI-SearchBot/1.0", "Google-Extended"):
        assert c.get("/", headers={"user-agent": ua}).status_code == 200, ua
    r = c.post("/v1/events", headers={"user-agent": ""}, json={})
    assert r.status_code == 403 and r.json()["error"]["code"] == "user_agent_required"


def test_llm_budget_exhausted_still_answers_with_the_template(dist, monkeypatch):
    calls = []
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(resolver, "_gemini_call", lambda payload, system, schema: calls.append(1) or
                        ({"answer": payload["answer"] + " Thanks."} if "answer" in schema["required"] else
                         {"shopper_message": payload["shopper_message"], "agent_summary": payload["agent_summary"]}))
    monkeypatch.setenv("LLM_DAILY_BUDGET", "0")
    c = make(dist)
    sid = c.post("/v1/demo/sessions").json()["id"]
    a = c.post(f"/v1/demo/sessions/{sid}/orders/zomato/ask", json={"question": "where is it"})
    assert a.status_code == 200 and a.json()["rephrased"] is False and calls == []
    monkeypatch.setenv("LLM_DAILY_BUDGET", "1000")
    monkeypatch.setenv("LLM_IP_DAILY", "1")
    c = make(dist)
    sid = c.post("/v1/demo/sessions", headers={"x-forwarded-for": "192.0.2.1"}).json()["id"]   # another IP's budget
    ask = lambda ip: c.post(f"/v1/demo/sessions/{sid}/orders/zomato/ask", json={"question": "where is it"},  # noqa: E731
                            headers={"x-forwarded-for": ip}).json()
    before = len(calls)
    assert [ask("203.0.113.5")["rephrased"], ask("203.0.113.5")["rephrased"], ask("203.0.113.6")["rephrased"]] ==         [True, False, True]                                                 # one model call per IP per day
    assert len(calls) - before == 2


def test_access_log_is_one_json_line_without_query_or_body(dist, monkeypatch, caplog):
    monkeypatch.setattr(waf, "_JSON", True)
    caplog.set_level(logging.INFO, logger="wismo.access")
    c = make(dist)
    c.get("/v1/orders/x/view?client_secret=cs_test_SECRET", headers={"user-agent": "curl/8"})
    line = json.loads([r.getMessage() for r in caplog.records if r.name == "wismo.access"][-1])
    assert line["httpRequest"]["requestUrl"] == "/v1/orders/x/view" and "SECRET" not in json.dumps(line)
    assert line["httpRequest"]["status"] == 401 and line["severity"] == "INFO" and line["instance"]


def test_static_files_skip_the_shared_counters(dist):
    c = make(dist, general="2/m")
    for path in ("/assets/app-1.js", "/site/photo/a.jpg", "/og/home.png", "/favicon.svg", "/sdk/cierto.js") * 2:
        assert c.get(path).status_code != 429, path
    assert [c.get("/").status_code for _ in range(3)] == [200, 200, 429]    # pages and the API still count
