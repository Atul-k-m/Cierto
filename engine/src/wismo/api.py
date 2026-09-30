"""HTTP API for surfaces (widget, hosts, launcher, site) and the SDK. Demo sessions run on a virtual clock.

Run: python -m wismo serve   (API, SDK bundle and the built web app on one port)

  /healthz /readyz liveness (cheap) and readiness (web build present, session store reachable)
  /v1/demo/*     demo sessions for the host replicas (a shared virtual clock, story beats)
  /v1/*          the Cierto SDK server API (sdk.py): keys, sessions, events, orders, ask, config, remedies
  /sdk/*         the built browser SDK (packages/cierto-js/dist): cierto.js, cierto.mjs, react.mjs
  /              the built web app (web.py): prerendered routes, a real 404

Stateless: a demo session is an op log (create, advance, act, approve) in the shared store
(sessions.py), so any instance behind the load balancer can answer any request. The WAF (waf.py)
wraps everything; CORS is open only on the SDK surfaces (/v1/* except /v1/demo/*, and /sdk/*).
"""
import os
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.gzip import GZipMiddleware

from . import ask as asking
from . import sdk, shared, web
from .cases import ActionError, CaseDesk
from .clock import VirtualClock
from .engine import Engine
from .events import EventType
from .profiles import PROFILES
from .resolver import ACTIONS, current
from .scenario import Scenario
from .sessions import Busy, Exists, Gone, Reply, Sessions, seeded
from .store.memory import MemoryEventStore
from .view import build_view
from .waf import SERVED_BY, Firewall, WafConfig
from .webhooks import WebhookLog, secret_from_seed

SCENARIOS = Path(__file__).resolve().parents[3] / "scenarios" / "demo"

# The six WISMO causes the site lets visitors pick, with the words the site uses for them.
CAUSES = {
    "rider_stalled": "Rider stuck",
    "traffic_delay": "Traffic",
    "batched": "Batched order",
    "address_mismatch": "Bad address",
    "courier_silent": "Courier silent",
    "delivered_not_received": "Delivered, not received",
    "eta_slipping": "Date keeps slipping",
    "refund_overdue": "Refund not credited",
}

PRESETS = {
    "signature": {
        "start": "2025-12-24T13:53:00+05:30",
        "orders": [
            # key, scenario file, host, variant
            ("smytten-delivered", "smytten-delivered.json", "smytten", "orders-row"),
            ("smytten-late", "smytten-late.json", "smytten", "orders-row"),
            ("smytten-refund", "smytten-refund.json", "smytten", "orders-row"),
            ("smytten-ok", "smytten-ok.json", "smytten", "orders-row"),
            ("zomato", "zomato-delivered.json", "zomato", "tracking-card"),
            ("swish", "swish-delivered.json", "swish", "after-delivered"),
            # one order per WISMO cause, each at its interesting moment by the "claimed" beat (2:02 pm)
            ("swish-stalled", "swish-stalled.json", "swish", "tracking-card"),
            ("zomato-traffic", "zomato-traffic.json", "zomato", "tracking-card"),
            ("zomato-batched", "zomato-batched.json", "zomato", "tracking-card"),
            ("smytten-address", "smytten-address.json", "smytten", "orders-row"),
            ("smytten-silent", "smytten-silent.json", "smytten", "orders-row"),
        ],
        "beats": [
            {"id": "lunch", "label": "On their way", "at": "2025-12-24T13:53:00+05:30"},
            {"id": "riding", "label": "Riders out", "at": "2025-12-24T13:59:00+05:30"},
            {"id": "claimed", "label": "Courier marks delivered, no OTP", "at": "2025-12-24T14:02:00+05:30", "primary": True},
            {"id": "ten_min", "label": "10 min later", "at": "2025-12-24T14:12:00+05:30"},
            {"id": "next_day", "label": "Next day", "at": "2025-12-25T14:10:00+05:30"},
            {"id": "two_days", "label": "Two days later", "at": "2025-12-26T14:10:00+05:30"},
        ],
    },
}
BRANDS = {"smytten": "Smytten", "zomato": "Zomato", "swish": "Swish"}


class DemoSession:
    """One visitor's run of a preset. Built only from (sid, preset) and then the ops of its log, so every
    instance that folds the same log holds the same session (ids included)."""

    def __init__(self, sid: str, preset: str):
        spec = PRESETS[preset]
        self.id = sid
        self.preset = preset
        self.beats = spec["beats"]
        self.orders: dict[str, dict] = {}
        verticals, hosts, arrivals, scripts = {}, {}, [], []
        for key, file, host, variant in spec["orders"]:
            sc = Scenario.load(SCENARIOS / file)
            verticals[sc.tenant.id] = sc.tenant.vertical
            hosts[sc.tenant.id] = host
            self.orders[key] = {"key": key, "host": host, "variant": variant, "tenant": sc.tenant.id,
                                "order_ref": sc.order_ref, "brand": BRANDS[host], "sources": sc.complaints,
                                "title": sc.title, "cause": sc.cause}
            arrivals += sc.arrivals()
            scripts += [(at, key, step) for at, step in sc.scripted()]
        arrivals.sort(key=lambda pair: pair[0])
        self.hosts = hosts
        self.clock = VirtualClock(arrivals[0][0])
        self.store = MemoryEventStore(received_at=self.clock.now)
        self.engine = Engine(self.store, self.clock, lambda tenant: PROFILES[verticals[tenant]])
        # The demo's hosts decide under the same default policies as the SDK's test tenants.
        self.webhooks = WebhookLog(f"demo-{self.id}", secret_from_seed(f"demo:{self.id}"), ids=seeded(f"demo:{sid}:webhooks"),
                                   stamp=lambda created: int(datetime.fromisoformat(created).timestamp()))
        self.desk = CaseDesk(self.engine, lambda tenant: BRANDS[hosts[tenant]],
                             lambda tenant: sdk.DEFAULT_POLICIES[hosts[tenant]],
                             emit=lambda tenant, kind, obj: self.webhooks.record(kind, obj, self.clock.now().isoformat()))
        for at, event in arrivals:
            self.clock.schedule(("arrival", event.tenant_id, event.event_id), at, lambda e=event: self.engine.ingest(e))
        # Scripted shopper actions (a scenario's complaint is often the shopper asking): the same path as a tap.
        for i, (at, key, step) in enumerate(scripts):
            self.clock.schedule(("script", key, i), at, lambda k=key, s=step: self._scripted(k, s))
        self.clock.advance_to(datetime.fromisoformat(spec["start"]))

    def _scripted(self, key: str, step: dict) -> None:
        o = self.orders[key]
        detail = {k: v for k, v in step.items() if k not in ("action", "locale")}
        self.desk.act(o["tenant"], o["order_ref"], step["action"], detail, step.get("locale", "en-IN"))

    def summary(self) -> dict:
        now = self.clock.now()
        feed = []
        for o in self.orders.values():
            for s in self.store.events_for_order(o["tenant"], o["order_ref"]):
                e = s.event
                if e.type is EventType.ENGINE_FINDING and e.occurred_at <= now:
                    feed.append({"at": e.occurred_at.isoformat(), "order": o["key"], "host": o["host"],
                                 "rule": e.data["rule"], "kind": e.data["kind"], "holder": e.data["holder"],
                                 "message": e.data["message"]})
        feed.sort(key=lambda f: f["at"], reverse=True)
        views = {k: self.view(k) for k in self.orders}
        causes = {}
        for o in self.orders.values():
            if o["cause"]:
                causes.setdefault(o["cause"], {"id": o["cause"], "label": CAUSES.get(o["cause"], o["cause"]), "orders": []})
                causes[o["cause"]]["orders"].append(o["key"])
        return {
            "id": self.id, "preset": self.preset, "now": now.isoformat(),
            "beats": [{**b, "reached": datetime.fromisoformat(b["at"]) <= now} for b in self.beats],
            "orders": [{**o, "state": v["state"] if v else None, "proof": v["proof"]["state"] if v else None,
                        "tone": v["tone"] if v else None, "live_cause": (v["cause"] or {}).get("id") if v else None}
                       for o, v in ((o, views[o["key"]]) for o in self.orders.values())],
            "causes": list(causes.values()),
            "feed": feed,
        }

    def view(self, key: str, locale: str = "en-IN") -> dict | None:
        o = self.orders[key]
        return build_view(self.engine, o["tenant"], o["order_ref"], o["brand"], locale)

    def act(self, key: str, action: str, locale: str = "en-IN", detail: dict | None = None) -> None:
        """The shopper's action: recorded as a fact, then resolved by the AI resolver under the host's policy."""
        o = self.orders[key]
        try:
            self.desk.act(o["tenant"], o["order_ref"], action, detail, locale)
        except ActionError as exc:
            raise HTTPException(400, str(exc)) from None

    def webhooks_for(self, key: str | None = None) -> list[dict]:
        """Signed webhooks, newest first; only one order's if ``key`` is given."""
        entries = list(reversed(self.webhooks.entries))
        if key is None:
            return entries
        ref = self.orders[key]["order_ref"]
        return [w for w in entries if _order_of(w["payload"]["data"]["object"]) == ref]

    def case(self, key: str) -> dict:
        """The console's view of one order: audit timeline, proof, resolution with its internals, webhooks, policy."""
        o = self.orders[key]
        view = self.view(key)
        events = self.engine.events(o["tenant"], o["order_ref"])
        state = current(events)
        host_policy = sdk.DEFAULT_POLICIES[o["host"]].model_dump()
        return {
            "object": "case",
            "order": o,
            "case_id": state["case_id"] if state else (view["issue"] or {}).get("id") if view else None,
            "state": view["state"] if view else None,
            "tone": view["tone"] if view else None,
            "cause": view["cause"] if view else None,
            "holder": view["holder"] if view else None,
            "issue": view["issue"] if view else None,
            "clocks": view["clocks"] if view else [],
            "proof": view["proof"] if view else None,
            "timeline": [_audit_line(e) for e in sorted(events, key=lambda e: e.occurred_at)],
            "resolution": None if not state else {
                "resolution_id": state["resolution_id"], "version": state["version"], "action": state["action"],
                "decision": state["decision"], "status": state["status"], "remedy": state["remedy"],
                "needs_approval": state["needs_approval"], "approval_reason": state.get("approval_reason"),
                "approved_by": state.get("approved_by"), "trust": state.get("trust"),
                "follow_up": state.get("follow_up"), "steps": state["steps"],
                "shopper_message": state["shopper_message"], "agent_summary": state["agent_summary"],
                "decided_at": state["decided_at"], "llm": state.get("llm"),
            },
            "webhooks": self.webhooks_for(key),
            "policy": {"source": "resolution" if state else "host_default",
                       "values": state["policy"] if state else host_policy},
        }


def _order_of(obj: dict) -> str | None:
    """Which order a webhook's data object is about (remedy/case objects carry order_id; order objects, id)."""
    return obj.get("order_id") or (obj.get("id") if obj.get("object") == "order" else None)


def _audit_line(e) -> dict:
    """One fact or decision for the console: when, what, who said so, from which source, in a line."""
    d = e.data
    text = e.substatus or e.type.value
    match e.type:
        case EventType.ENGINE_FINDING:
            text = f"{d['rule']}: {d['message']}"
        case EventType.ENGINE_RESOLUTION:
            r = d["remedy"]
            text = f"{d['decision']} · {r['kind']}" + (f" ₹{r['amount_inr']}" if r.get("amount_inr") is not None else "") \
                + f" · {d['status']}" + (" · needs approval" if d["needs_approval"] else "")
        case EventType.REMEDY_APPROVED:
            text = f"remedy approved by {d.get('approved_by')}"
        case EventType.REMEDY_EXECUTED:
            text = f"remedy executed · {d.get('outcome')}" + (f" · ref {d['reference']}" if d.get("reference") else "")
        case EventType.RIDER_LOCATION:
            spot = d.get("near") or "{},{}".format(d.get("lat"), d.get("lng"))
            text = f"rider at {spot}" \
                + (f" · {d['distance_to_drop_m']} m to drop" if d.get("distance_to_drop_m") is not None else "")
        case EventType.ETA_PROMISED | EventType.ETA_REVISED:
            text = f"{e.type.value}: {d.get('shown_to_customer') or d.get('expected_by')}" \
                + (f" · {d['reason']} +{d.get('delay_minutes')} min" if d.get("reason") else "")
        case EventType.ADDRESS_CHECK:
            text = f"address check: pin {d.get('distance_m')} m from typed address · confidence {d.get('confidence')}"
        case EventType.DISPATCH_STOP_SEQUENCE:
            text = f"stop sequence: {len(d.get('stops') or [])} stop(s)"
        case EventType.REFUND_STATUS:
            text = f"refund {d.get('stage')} ₹{d.get('amount_inr')}" + (f" · {d['reference']}" if d.get("reference") else "")
        case EventType.CUSTOMER_CONTACTED | EventType.CUSTOMER_RECEIPT_DISPUTED | EventType.CUSTOMER_RECEIPT_CONFIRMED:
            text = e.type.value + (f" · {d['topic']}" if d.get("topic") else "")
    if e.proof:
        p = e.proof
        text += " · " + ", ".join(f"{k}={v}" for k, v in p.model_dump(exclude_none=True).items())
    return {"at": e.occurred_at.isoformat(), "type": e.type.value, "asserted_by": e.asserted_by.value,
            "source": e.source_adapter, "text": text}


# ---- demo sessions as op logs -------------------------------------------------------------------

def apply_demo(name: str, s: DemoSession | None, op: dict) -> tuple[DemoSession, None]:
    """Fold one op into a demo session. Only the virtual clock moves time; nothing reads the wall clock."""
    match op["op"]:
        case "create":
            return DemoSession(op["sid"], op["preset"]), None
        case "advance":
            s.clock.advance_to(datetime.fromisoformat(op["to"]))
        case "act":
            s.act(op["key"], op["action"], op["locale"], op["detail"])
        case "approve":
            o = s.orders[op["key"]]
            try:
                s.desk.approve(o["tenant"], op["remedy_id"], op["approved_by"])
            except (ActionError, KeyError) as exc:
                raise HTTPException(409, str(exc)) from None
        case _:
            raise ValueError(f"unknown demo op {op['op']!r}")
    return s, None


SESSION_TTL = int(os.environ.get("SESSION_TTL_SECONDS", 2 * 3600))
_SID = re.compile(r"^[0-9a-f]{8,32}$")
_GONE = "session not found; start a new one"

router = APIRouter()


def _demo(request: Request) -> Sessions:
    return request.app.state.demo


def _read(request: Request, sid: str, fn):
    """``fn(session)`` on the caught-up session; 404 for an unknown or expired id."""
    if not _SID.match(sid):
        raise HTTPException(404, _GONE)
    try:
        return _demo(request).read(f"demo:{sid}", fn)
    except Gone:
        raise HTTPException(404, _GONE) from None


def _write(request: Request, sid: str, plan, respond):
    if not _SID.match(sid):
        raise HTTPException(404, _GONE)
    try:
        return _demo(request).write(f"demo:{sid}", plan, respond)
    except Gone:
        raise HTTPException(404, _GONE) from None


def _order(s: DemoSession, key: str) -> dict:
    if key not in s.orders:
        raise HTTPException(404, "unknown order")
    return s.orders[key]


@router.get("/healthz", include_in_schema=False)
def healthz() -> dict:
    """Liveness: the process answers. Touches nothing else."""
    return {"status": "ok"}


@router.get("/readyz", include_in_schema=False)
def readyz(request: Request) -> JSONResponse:
    """Readiness: the web build is there (not on Vercel, where the "web" service serves it) and the store answers."""
    backend = request.app.state.backend
    web_ok = (request.app.state.web.root / "index.html").is_file()
    store_ok = backend.ping()
    ok = (web_ok or bool(os.environ.get("VERCEL"))) and store_ok
    return JSONResponse({"status": "ready" if ok else "unready", "web": web_ok,
                         "store": {"kind": backend.kind, "ok": store_ok}, "instance": SERVED_BY},
                        status_code=200 if ok else 503, headers={"cache-control": "no-store"})


@router.post("/v1/demo/sessions")
def create_session(request: Request, preset: str = "signature") -> dict:
    if preset not in PRESETS:
        raise HTTPException(404, f"unknown preset {preset!r}")
    for _ in range(3):
        sid = secrets.token_hex(6)
        try:
            return _demo(request).create(f"demo:{sid}", {"op": "create", "sid": sid, "preset": preset},
                                         lambda s, _: s.summary())
        except Exists:
            continue
    raise HTTPException(503, "could not allocate a session id; try again")


@router.get("/v1/demo/sessions/{sid}")
def get_session(request: Request, sid: str) -> dict:
    return _read(request, sid, lambda s: s.summary())


class Advance(BaseModel):
    beat: str | None = None
    minutes: int | None = Field(None, le=60 * 24 * 30)


@router.post("/v1/demo/sessions/{sid}/advance")
def advance(request: Request, sid: str, body: Advance) -> dict:
    def plan(s: DemoSession):
        if body.beat:
            beat = next((b for b in s.beats if b["id"] == body.beat), None)
            if beat is None:
                raise HTTPException(404, f"unknown beat {body.beat!r}")
            target = datetime.fromisoformat(beat["at"])
        elif body.minutes:
            target = s.clock.now() + timedelta(minutes=body.minutes)
        else:
            raise HTTPException(400, "give a beat or minutes")
        if target <= s.clock.now():
            return Reply(s.summary())
        return {"op": "advance", "to": target.isoformat()}
    return _write(request, sid, plan, lambda s, _: s.summary())


@router.get("/v1/demo/sessions/{sid}/orders/{key}")
def order_view(request: Request, sid: str, key: str, locale: str = "en-IN") -> dict:
    return _read(request, sid, lambda s: {"order": _order(s, key), "view": s.view(key, locale)})


class Action(BaseModel):
    action: str = Field(max_length=64)
    locale: str = Field("en-IN", max_length=16)
    items: list[str] | None = Field(None, max_length=50)
    photo: bool | None = None
    landmark: str | None = Field(None, max_length=200)


@router.post("/v1/demo/sessions/{sid}/orders/{key}/actions")
def order_action(request: Request, sid: str, key: str, body: Action) -> dict:
    def plan(s: DemoSession):
        o = _order(s, key)
        if body.action not in ACTIONS:   # checked here so a bad request never touches the session
            raise HTTPException(400, f"unknown action {body.action!r}; expected one of {', '.join(ACTIONS)}")
        if not s.engine.events(o["tenant"], o["order_ref"]):
            raise HTTPException(400, f"no order {o['order_ref']!r}")
        return {"op": "act", "key": key, "action": body.action, "locale": body.locale,
                "detail": {"items": body.items, "photo": body.photo, "landmark": body.landmark}}
    return _write(request, sid, plan, lambda s, _: {"order": s.orders[key], "view": s.view(key, body.locale)})


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    locale: Literal["en-IN", "hi-Latn-IN"] = "en-IN"


@router.post("/v1/demo/sessions/{sid}/orders/{key}/ask")
def order_ask(request: Request, sid: str, key: str, body: Ask) -> dict:
    """A grounded answer to the shopper's question, composed only from this order's data."""
    def run(s: DemoSession):
        o = _order(s, key)
        return asking.compose(s.engine, o["tenant"], o["order_ref"], o["brand"], body.question, body.locale)
    composed = _read(request, sid, run)
    if composed is None:
        raise HTTPException(404, "the order has no events yet at this point of the story")
    answer, facts = composed
    return asking.rephrase(answer, facts, body.question, body.locale)   # the optional LLM call runs outside the lock


@router.get("/v1/demo/sessions/{sid}/orders/{key}/case")
def order_case(request: Request, sid: str, key: str) -> dict:
    """For a support-console panel: the order's audit timeline, proof, resolution, webhooks and the policy applied."""
    return _read(request, sid, lambda s: (_order(s, key), s.case(key))[1])


@router.get("/v1/demo/sessions/{sid}/webhooks")
def demo_webhooks(request: Request, sid: str, order: str | None = None) -> dict:
    """What the demo's hosts would have received: signed case/remedy webhooks, newest first (?order=<key> filters)."""
    def run(s: DemoSession):
        if order is not None:
            _order(s, order)
        return {"object": "list", "data": s.webhooks_for(order)}
    return _read(request, sid, run)


class Approve(BaseModel):
    approved_by: str = Field("support@host", max_length=120)


@router.post("/v1/demo/sessions/{sid}/orders/{key}/approve")
def demo_approve(request: Request, sid: str, key: str, body: Approve) -> dict:
    """The host's approval loop, for the demo: approve the order's pending remedy."""
    def plan(s: DemoSession):
        o = _order(s, key)
        state = s.desk.state(o["tenant"], o["order_ref"])
        if not state or not state["remedy"].get("id"):
            raise HTTPException(409, "nothing to approve")
        if state["status"] != "proposed":
            raise HTTPException(409, f"remedy is already {state['status']}")
        return {"op": "approve", "key": key, "remedy_id": state["remedy"]["id"], "approved_by": body.approved_by}
    return _write(request, sid, plan, lambda s, _: {"order": s.orders[key], "view": s.view(key)})


ROOT = Path(__file__).resolve().parents[3]
SDK_DIST = Path(os.environ.get("CIERTO_SDK_DIST") or ROOT / "packages" / "cierto-js" / "dist")
SDK_ALIASES = {"pakka.js": "cierto.js", "pakka.mjs": "cierto.mjs"}   # pages written before the rename keep working
WEB_DIST = Path(os.environ.get("WEB_DIST") or os.environ.get("WISMO_WEB_DIST") or ROOT / "apps" / "web" / "dist")


@router.api_route("/sdk/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
def sdk_bundle(path: str) -> FileResponse:
    """The browser SDK: /sdk/cierto.js (UMD, global Cierto), /sdk/cierto.mjs (ESM), /sdk/react.mjs.
    /sdk/pakka.js and /sdk/pakka.mjs return the same bundles."""
    path = SDK_ALIASES.get(path, path)
    file = (SDK_DIST / path).resolve()
    if not path or not file.is_file() or SDK_DIST.resolve() not in file.parents:
        raise HTTPException(404, "not in the SDK bundle; build it with: python -m wismo serve --build")
    return FileResponse(file, headers={"Cache-Control": "public, max-age=300", "Access-Control-Allow-Origin": "*"})


# ---- the app ------------------------------------------------------------------------------------

class ScopedCORS:
    """Open CORS where browsers call with publishable keys (/v1/* and /sdk/*); none on the demo API or the site."""

    def __init__(self, app):
        self.app = app
        self.cors = CORSMiddleware(app, allow_origins=["*"], allow_methods=["GET", "HEAD", "POST", "PUT", "OPTIONS"],
                                   allow_headers=["*"], expose_headers=["Idempotent-Replayed", "Retry-After"])

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "") if scope["type"] == "http" else ""
        if path.startswith("/sdk/") or (path.startswith("/v1/") and not path.startswith("/v1/demo/")):
            return await self.cors(scope, receive, send)
        return await self.app(scope, receive, send)


class ScopedGZip:
    """gzip (over 1 KB) for the API and the SDK bundle; the web app (web.py) compresses and caches its own."""

    def __init__(self, app):
        self.app, self.gzip = app, GZipMiddleware(app, minimum_size=1024)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith(("/v1/", "/sdk/", "/openapi.json")):
            return await self.gzip(scope, receive, send)
        return await self.app(scope, receive, send)


async def _store_unavailable(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse({"detail": "the session store is unavailable; try again"}, status_code=503,
                        headers={"retry-after": "1"})


def _managers(app: FastAPI, backend) -> None:
    app.state.backend = backend
    app.state.demo = Sessions(backend, apply_demo, ttl=SESSION_TTL, pool="demo",
                              cache_size=int(os.environ.get("SESSION_CACHE_SIZE", 128)),
                              cap=int(os.environ.get("SESSION_MAX_LIVE", 5000)))
    app.state.sdk = sdk.sessions(backend)


def create_app(backend=None, web_dist: Path | None = None, waf: WafConfig | None = None) -> FastAPI:
    """One app instance. Instances that share ``backend`` behave as one service (tests build two to prove it)."""
    backend = backend or shared.open_backend()
    app = FastAPI(title="Cierto API", version="0.1.0", docs_url="/v1/docs", redoc_url=None,
                  swagger_ui_oauth2_redirect_url="/v1/docs/oauth2-redirect",
                  description="Cierto: AI WISMO for Indian commerce. Order truth, grounded answers and policy-gated remedies.")
    _managers(app, backend)
    app.state.web = web.from_env(WEB_DIST, web_dist)
    app.add_exception_handler(sdk.ApiError, sdk.api_error_handler)
    for exc in (shared.StoreUnavailable, Busy):
        app.add_exception_handler(exc, _store_unavailable)
    app.include_router(router)
    app.include_router(sdk.router)
    # One origin, one port: the built web app is served by the same process as the API. Keep this mount last.
    app.mount("/", app.state.web, name="web")
    app.add_middleware(ScopedGZip)
    app.add_middleware(ScopedCORS)
    app.add_middleware(Firewall, backend=lambda: app.state.backend, config=waf)   # outermost: runs first
    return app


app = create_app()


class _Live:
    """The module app's demo sessions by id, caught up (for tests and the REPL): ``SESSIONS[sid].engine``."""

    def __getitem__(self, sid: str) -> DemoSession:
        return app.state.demo.read(f"demo:{sid}", lambda s: s)


SESSIONS = _Live()


def reset_state(target: FastAPI | None = None) -> None:
    """Forget every session, tenant log and counter (tests): a fresh in-memory store."""
    _managers(target or app, shared.MemoryBackend())
