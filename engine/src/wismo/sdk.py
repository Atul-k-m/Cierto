"""Cierto SDK server API (test mode): keys, customer sessions, ingestion, order views, actions,
grounded answers (ask), policy config and simulation, remedies and outgoing webhooks.

Each tenant gets a sandbox. Its clock follows wall time (IST) plus a test-clock offset
(POST /v1/dev/advance), so events a host sends now land now, and a scheduled refund fires when
its time comes. Four test orders, like Stripe's test cards, are seeded into every sandbox from the
demo scenarios, re-based so each sits at its interesting moment on arrival.

A tenant's mutable state (config, customer sessions, idempotent results, webhooks, the sandbox)
is an op log in the shared store (sessions.py), so any instance can serve any request: a client
secret minted on one instance works on the next, an Idempotency-Key replays anywhere. Each op
carries the wall time it ran at, and the clock ticks to it before the op applies, so every instance
folds the same log into the same state. Clock-driven follow-ups (a refund that fires at its
deadline) run on whichever instance ticks first, with templates rather than a model call, and
their webhooks are sent once (a shared claim). POST /v1/dev/reset (or SDK_LOG_MAX_OPS writes)
starts the tenant on a fresh log that carries its config and customer sessions over.

Auth follows Stripe: a secret key (sk_test_cierto_…) for the host's server; a publishable key
(pk_test_cierto_…) plus a 15-minute customer-session client secret (cs_test_…) for the browser,
scoped to one order. Keys are derived from CIERTO_DEV_SEED so the docs' curl examples work as written.
"""
import hashlib
import json
import os
import re
import secrets
import string
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from typing import Callable, Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from . import ask as asking
from .cases import CaseDesk
from .clock import VirtualClock
from .engine import Engine
from .events import AssertedBy, Event, EventType
from .profiles import PROFILES
from .resolver import ACTIONS, IST, Policy, _clock, _day
from .scenario import Scenario
from .sessions import Reply, Sessions, Stale, seeded, tape
from .store.base import AppendResult, IdempotencyConflict
from .store.memory import MemoryEventStore
from .view import build_view
from .webhooks import WebhookLog, WebhookVerificationError, secret_from_seed, verify

SCENARIOS = Path(__file__).resolve().parents[3] / "scenarios" / "demo"
SESSION_TTL = timedelta(minutes=15)
API_VERSION = "2026-09-30"
THEMES = ("smytten", "zomato", "swish", "neutral")
# appearance.variables → the widget's --w-* tokens (colorSurface2 → --w-color-surface-2)
APPEARANCE_VARIABLES = (
    "colorInk", "colorMuted", "colorSurface", "colorSurface2", "colorLine", "colorAction", "colorActionInk",
    "colorActionStrong", "colorOk", "colorOkSoft", "colorCheck", "colorCheckSoft", "colorAlert", "colorAlertSoft",
    "colorFocus", "fontBody", "radiusSurface", "radiusControl",
)
_SAFE_VALUE = re.compile(r"^[^;{}<>\\]{1,120}$")
_RESERVED = {EventType.ENGINE_FINDING, EventType.ENGINE_RESOLUTION, EventType.REMEDY_APPROVED, EventType.REMEDY_EXECUTED}

TENANT_SPECS = {
    "smytten": {"brand": "Smytten", "vertical": "parcel", "delivered": "smytten-delivered.json",
                "policy": Policy(auto_refund_cap_inr=1000, trust_min_for_instant=0.6, investigate_window_hours=24,
                                 reattempt_first=True, food_instant_refund=False)},
    "zomato": {"brand": "Zomato", "vertical": "quick", "delivered": "zomato-delivered.json",
               "policy": Policy(auto_refund_cap_inr=500, trust_min_for_instant=0.6, investigate_window_hours=2,
                                reattempt_first=False, food_instant_refund=True)},
    "swish": {"brand": "Swish", "vertical": "quick", "delivered": "swish-delivered.json",
              "policy": Policy(auto_refund_cap_inr=300, trust_min_for_instant=0.6, investigate_window_hours=1,
                               reattempt_first=False, food_instant_refund=True)},
}
DEFAULT_POLICIES = {k: v["policy"] for k, v in TENANT_SPECS.items()}


def is_dev() -> bool:
    env = os.environ.get("CIERTO_ENV") or os.environ.get("PAKKA_ENV") or "dev"   # PAKKA_ENV: the pre-rename name
    return env.lower() not in ("live", "prod", "production")


def _dev_seed() -> str:
    return os.environ.get("CIERTO_DEV_SEED", "cierto-dev-2026")


def _wall() -> datetime:
    return datetime.now(IST).replace(microsecond=0)


# ---- errors (Stripe-style bodies) -------------------------------------------------------------

class ApiError(Exception):
    def __init__(self, status: int, type_: str, code: str, message: str, **extra):
        super().__init__(message)
        self.status, self.type, self.code, self.message, self.extra = status, type_, code, message, extra


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse({"error": {"type": exc.type, "code": exc.code, "message": exc.message, **exc.extra}},
                        status_code=exc.status)


def _bad(code: str, message: str, **extra) -> ApiError:
    return ApiError(400, "invalid_request_error", code, message, **extra)


# ---- test orders ------------------------------------------------------------------------------

TEST_CUSTOMER = {"ref": "cus_test_4242", "account_age_days": 420, "orders_90d": 7, "remedies_90d": 0}


def _first(events: list[Event], substatus: str | None = None, kind: EventType | None = None) -> Event:
    return next(e for e in events if (substatus and e.substatus == substatus) or (kind and e.type is kind))


@dataclass(frozen=True)
class TestOrder:
    id: str
    description: str
    source: str | None                       # scenario file; None = the tenant's own "marked delivered" scenario
    drop: str | None                         # substatus to cut from the timeline
    target: Callable[[Scenario, list[Event]], datetime]   # the scenario moment that becomes "now"


TEST_ORDERS = (
    TestOrder("ord_test_unproven", "Marked delivered 10 min ago (2 min for food) with no OTP, no photo: the dispute flow",
              None, None,
              lambda sc, ev: ev[-1].occurred_at + timedelta(minutes=10 if sc.tenant.vertical == "parcel" else 2)),
    TestOrder("ord_test_stuck_ofd", "Parcel out for delivery 26 hours with no attempt, wrong phone on the parcel",
              "smytten-delivered.json", "delivered.delivered",
              lambda sc, ev: _first(ev, "out_for_delivery.out_for_delivery").occurred_at + timedelta(hours=26)),
    TestOrder("ord_test_refund_stuck", "Cancelled; refund initiated 12 days ago with a bank reference, never credited",
              "smytten-refund.json", None,
              lambda sc, ev: _first(ev, kind=EventType.REFUND_STATUS).occurred_at + timedelta(days=12)),
    TestOrder("ord_test_qc_late", "Ten-minute meal 17 min past its promise; rider silent since pickup",
              "swish-delivered.json", "delivered.delivered",
              lambda sc, ev: _first(ev, kind=EventType.ORDER_PLACED).occurred_at + timedelta(minutes=29)),
)


def _shown(text: str, due: datetime, at: datetime) -> str:
    """Re-render a promise shown to the customer after its dates moved."""
    if text.startswith("Arrives by"):
        return f"Arrives by {due.astimezone(IST):%a}, {due.astimezone(IST).day} {due.astimezone(IST):%b}"
    if text.startswith("Arriving by"):
        return f"Arriving by {_clock(due)}"
    if text.startswith("Arriving in"):
        return f"Arriving in {round((due - at).total_seconds() / 60)} minutes"
    return text


def seed(spec: TestOrder, tenant: "Tenant", anchor: datetime) -> list[tuple[datetime, Event]]:
    """The spec's scenario, re-keyed to this tenant and order id, shifted so its target moment is ``anchor``."""
    sc = Scenario.load(SCENARIOS / (spec.source or TENANT_SPECS[tenant.id]["delivered"]))
    pairs = [(a, e) for a, e in sc.arrivals() if not (spec.drop and e.substatus == spec.drop)]
    shift = anchor - spec.target(sc, sorted((e for _, e in pairs), key=lambda e: e.occurred_at))
    out = []
    for i, (arrival, e) in enumerate(pairs, start=1):
        data = dict(e.data)
        if e.type is EventType.ORDER_PLACED:
            data.update(customer=dict(TEST_CUSTOMER), vertical=sc.tenant.vertical, test_order=True)
        if e.type is EventType.ETA_PROMISED:
            due = datetime.fromisoformat(data["due_by"]) + shift
            data.update(due_by=due.isoformat(), shown_to_customer=_shown(data.get("shown_to_customer", ""), due,
                                                                         e.occurred_at + shift))
        out.append((arrival + shift, e.model_copy(update={
            "event_id": f"{spec.id}-{i:03d}", "tenant_id": tenant.id, "order_ref": spec.id,
            "occurred_at": e.occurred_at + shift, "data": data})))
    return out


# ---- tenants and their state ------------------------------------------------------------------

def _token(tenant: str, kind: str, n: int = 24) -> str:
    value = int(hashlib.sha256(f"{_dev_seed()}:{tenant}:{kind}".encode()).hexdigest(), 16)
    alphabet = string.digits + string.ascii_letters
    out = ""
    while len(out) < n:
        value, r = divmod(value, 62)
        out += alphabet[r]
    return out


class Tenant:
    """A test tenant's identity: brand, vertical, keys and webhook secret (derived, so every instance agrees)."""

    def __init__(self, tid: str, spec: dict):
        self.id, self.brand, self.vertical = tid, spec["brand"], spec["vertical"]
        # Vendor-prefixed, like sk-ant-…: a leaked key is recognisable (and scannable) as a Cierto key.
        self.publishable_key = f"pk_test_cierto_{tid}_{_token(tid, 'pk')}"
        self.secret_key = f"sk_test_cierto_{tid}_{_token(tid, 'sk')}"
        self.webhook_secret = secret_from_seed(f"{_dev_seed()}:{tid}:whsec")
        self.default_policy: Policy = spec["policy"]


TENANTS = {tid: Tenant(tid, spec) for tid, spec in TENANT_SPECS.items()}
KEYS = {k: t for t in TENANTS.values() for k in (t.publishable_key, t.secret_key)}


class Sandbox:
    """One tenant's engine, log and desk, on a clock that follows wall time plus the test-clock offset."""

    def __init__(self, state: "TenantState", anchor: datetime):
        tenant = state.tenant
        arrivals = sorted((pair for spec in TEST_ORDERS for pair in seed(spec, tenant, anchor)), key=lambda a: a[0])
        self.clock = VirtualClock(arrivals[0][0])
        self.store = MemoryEventStore(received_at=self.clock.now)
        self.engine = Engine(self.store, self.clock, lambda _t: PROFILES[tenant.vertical])
        self.desk = CaseDesk(self.engine, lambda _t: tenant.brand, lambda _t: state.policy,
                             emit=lambda _t, kind, obj: state.webhooks.record(kind, obj, self.clock.now().isoformat()))
        self.orders: list[str] = [spec.id for spec in TEST_ORDERS]
        for at, event in arrivals:
            self.clock.schedule(("arrival", event.event_id), at, lambda e=event: self.engine.ingest(e))
        self.clock.advance_to(anchor)


class TenantState:
    """A tenant's mutable test-mode state, folded from its op log (see ``apply``)."""

    def __init__(self, tenant: Tenant, log: str, base: dict, backend):
        carry = base.get("carry") or {}
        self.tenant, self.log = tenant, log
        self.policy: Policy = Policy.model_validate(carry["policy"]) if carry.get("policy") \
            else tenant.default_policy.model_copy()
        self.appearance = carry.get("appearance") or {"theme": tenant.id, "variables": {}}
        self.config_version = carry.get("config_version", 1)
        self.sessions: dict[str, dict] = dict(carry.get("sessions") or {})
        self.idempotency: dict[str, tuple[str, int, dict]] = {}
        self.offset = timedelta(0)
        self.webhooks = WebhookLog(
            tenant.id, tenant.webhook_secret, ids=seeded(f"{log}:webhooks"),
            stamp=lambda created: int((datetime.fromisoformat(created) - self.offset).timestamp()),
            claim=lambda msg_id: backend.claim(f"whsend:{msg_id}", 86400),
            report=lambda msg_id, status: backend.set(f"whd:{msg_id}", str(status), 86400))
        self.webhooks.url = carry.get("webhook_url")
        self.sandbox = Sandbox(self, datetime.fromisoformat(base["at"]))

    def wall(self) -> datetime:
        """Now, and never before this state's clock: an op's time only moves forward."""
        return max(_wall(), self.sandbox.clock.now() - self.offset)

    def tick(self, at: datetime | None = None) -> None:
        """Advance to wall time (or ``at``). Follow-ups that fall due use templates: tape "off"."""
        with tape("off"):
            self.sandbox.clock.advance_to((at or self.wall()) + self.offset)

    def config(self) -> dict:
        return {"object": "config", "tenant": self.tenant.id, "version": self.config_version,
                "policy": self.policy.model_dump(), "appearance": self.appearance, "webhook_url": self.webhooks.url}

    def carry(self) -> dict:
        """What survives a reset: config and live customer sessions."""
        now = _now_ts()
        return {"policy": self.policy.model_dump(), "appearance": self.appearance,
                "config_version": self.config_version, "webhook_url": self.webhooks.url,
                "sessions": {k: v for k, v in self.sessions.items() if v["expires_ts"] > now}}


def _now_ts() -> float:
    return time.time()


def _base(tid: str, carry: dict | None = None) -> dict:
    return {"op": "base", "tenant": tid, "at": _wall().isoformat(), "carry": carry}


def apply(log: str, st: TenantState | None, op: dict, backend=None) -> tuple[TenantState, tuple[int, dict] | None]:
    """Fold one op into the state. Every op after ``base`` first ticks the clock to the wall time it ran at."""
    if op["op"] == "base":
        return TenantState(TENANTS[op["tenant"]], log, op, backend), None
    at = datetime.fromisoformat(op["at"])
    if st.sandbox.clock.now() > at + st.offset:
        raise Stale(log)   # a read here ticked past this op's time: rebuild from the log alone
    st.tick(at)
    result = _OPS[op["op"]](st, op)
    if op.get("idem"):
        st.idempotency[op["idem"]] = (op["fp"], *result)
    return st, result


def _op_session(st: TenantState, op: dict):
    st.sessions[op["cs"]] = {"order_id": op["order_id"], "customer_ref": op["customer_ref"],
                             "expires_ts": op["expires_ts"]}
    return 200, {"object": "customer_session", "client_secret": op["cs"], "order_id": op["order_id"],
                 "customer_ref": op["customer_ref"],
                 "expires_at": datetime.fromtimestamp(op["expires_ts"], timezone.utc).isoformat(), "livemode": False}


def _op_events(st: TenantState, op: dict):
    t, sb = st.tenant, st.sandbox
    accepted, duplicates, rejected, orders = 0, 0, [], []
    for i, item in enumerate(op["items"]):
        if not isinstance(item, dict):
            rejected.append({"index": i, "code": "invalid_event", "message": "each event must be an object"})
            continue
        item = {"tenant_id": t.id, **item}
        if item["tenant_id"] != t.id:
            rejected.append({"index": i, "event_id": item.get("event_id"), "code": "tenant_mismatch",
                             "message": "tenant_id must match the key's tenant (or be omitted)"})
            continue
        try:
            event = Event.model_validate(item)
        except ValidationError as exc:
            rejected.append({"index": i, "event_id": item.get("event_id"), "code": "invalid_event",
                             "message": "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
                                                  for e in exc.errors()[:3])})
            continue
        if problem := _check_host_event(event):
            rejected.append({"index": i, "event_id": event.event_id, "code": "invalid_event", "message": problem})
            continue
        try:
            result = sb.desk.ingest(event)
        except IdempotencyConflict as exc:
            rejected.append({"index": i, "event_id": event.event_id, "code": "event_conflict", "message": str(exc)})
            continue
        accepted += result is AppendResult.INSERTED
        duplicates += result is AppendResult.DUPLICATE
        if event.order_ref not in orders:
            orders.append(event.order_ref)
        if event.order_ref not in sb.orders:
            sb.orders.append(event.order_ref)
    return 202, {"object": "event_batch", "accepted": accepted, "duplicates": duplicates, "rejected": rejected,
                 "orders": orders}


def _op_order(st: TenantState, op: dict):
    t, sb = st.tenant, st.sandbox
    o = OrderIn.model_validate(op["body"])
    now = sb.clock.now()
    created = not _events(st, o.order_id)
    customer = o.customer.model_dump(exclude_none=True) if o.customer else {}
    if o.customer_ref:
        customer["ref"] = o.customer_ref
    data = {"amount_inr": o.amount_inr, "payment": o.payment, "items": o.items, **(o.extras or {})}
    data.update({k: v for k, v in {"title": o.title, "vertical": o.vertical, "customer": customer or None,
                                   "account_phone_last4": o.account_phone_last4}.items() if v})
    placed_at = o.placed_at or now
    events = [_versioned(t, o.order_id, "order.placed", EventType.ORDER_PLACED, placed_at, data)]
    if o.eta:
        quick = (o.vertical or t.vertical) == "quick"
        shown = o.eta.shown_to_customer or (f"Arriving by {_clock(o.eta.due_by)}" if quick
                                            else f"Arrives by {_day(o.eta.due_by)}")
        events.append(_versioned(t, o.order_id, "eta", EventType.ETA_PROMISED, placed_at,
                                 {"due_by": o.eta.due_by.isoformat(), "shown_to_customer": shown,
                                  "kind": "checkout" if created else "revision"}))
    for e in events:
        sb.desk.ingest(e)
    if o.order_id not in sb.orders:
        sb.orders.append(o.order_id)
    return (201 if created else 200), {"object": "order", "id": o.order_id, "created": created,
                                       "view": _view(st, o.order_id)}


def _op_act(st: TenantState, op: dict):
    st.sandbox.desk.act(st.tenant.id, op["order_id"], op["action"], op["detail"], op["locale"])
    return 200, _envelope(st, op["order_id"], _view(st, op["order_id"], op["locale"]))


def _op_approve(st: TenantState, op: dict):
    return 200, st.sandbox.desk.approve(st.tenant.id, op["remedy_id"], op["approved_by"])


def _op_config(st: TenantState, op: dict):
    st.policy = Policy.model_validate(op["policy"])
    st.appearance = op["appearance"]
    if "webhook_url" in op:
        st.webhooks.url = op["webhook_url"] or None
    st.config_version += 1
    return 200, st.config()


def _op_advance(st: TenantState, op: dict):
    st.offset += timedelta(minutes=op["minutes"], hours=op["hours"])
    st.tick(datetime.fromisoformat(op["at"]))
    return 200, {"object": "test_clock", "tenant": st.tenant.id, "now": st.sandbox.clock.now().isoformat(),
                 "offset_minutes": round(st.offset.total_seconds() / 60, 2)}


_OPS = {"session": _op_session, "events": _op_events, "order": _op_order, "act": _op_act, "approve": _op_approve,
        "config": _op_config, "advance": _op_advance}


def sessions(backend) -> Sessions:
    """The per-app manager of tenant logs (SDK_TTL_SECONDS idle, default a day)."""
    return Sessions(backend, partial(apply, backend=backend), ttl=int(os.environ.get("SDK_TTL_SECONDS", 86400)),
                    cache_size=16)


def _log_name(backend, tid: str) -> str:
    return f"sdk:{tid}:{backend.get(f'sdkgen:{tid}') or 0}"


def _rotate(app, t: Tenant, name: str, carry: dict) -> None:
    """Start the tenant on a new, empty log that carries ``carry``; stragglers on the old one are dropped."""
    mgr = app.state.sdk
    gen = int(name.rsplit(":", 1)[1]) + 1
    mgr.backend.log_create(f"sdk:{t.id}:{gen}", json.dumps(_base(t.id, carry), separators=(",", ":")), mgr.ttl)
    mgr.backend.set(f"sdkgen:{t.id}", str(gen))   # whether this instance created it or a racing one did


def _read_sync(app, t: Tenant, fn: Callable[[TenantState], object], tick: bool):
    mgr = app.state.sdk

    def run(st: TenantState):
        if tick:
            st.tick()
        return fn(st)
    return mgr.read(_log_name(mgr.backend, t.id), run, create=lambda: _base(t.id))


def _write_sync(app, t: Tenant, plan: Callable[[TenantState], dict | Reply]):
    mgr = app.state.sdk
    name = _log_name(mgr.backend, t.id)

    def planned(st: TenantState):
        st.tick()
        return plan(st)
    out = mgr.write(name, planned, lambda st, result: JSONResponse(result[1], result[0]), create=lambda: _base(t.id))
    if mgr.version(name) >= int(os.environ.get("SDK_LOG_MAX_OPS", 2000)):   # a busy shared sandbox starts over
        _rotate(app, t, name, mgr.read(name, lambda st: st.carry()))
    return out


async def _read(request: Request, t: Tenant, fn: Callable[[TenantState], object], tick: bool = True):
    """``fn(state)`` on the tenant's caught-up state, ticked to now, in a worker thread (store and engine block)."""
    return await run_in_threadpool(_read_sync, request.app, t, fn, tick)


async def _write(request: Request, t: Tenant, plan: Callable[[TenantState], dict | Reply]) -> JSONResponse:
    """Plan an op against the current state (errors raise before anything changes), then apply and log it."""
    return await run_in_threadpool(_write_sync, request.app, t, plan)


# ---- auth and helpers -------------------------------------------------------------------------

def _key(request: Request) -> str:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise ApiError(401, "authentication_error", "missing_api_key", "Send your key as 'Authorization: Bearer <key>'.")
    return token.strip()


def _secret(request: Request) -> Tenant:
    key = _key(request)
    t = KEYS.get(key)
    if t is None:
        raise ApiError(401, "authentication_error", "invalid_api_key", "Unknown API key. Dev keys: GET /v1/dev/keys.")
    if not key.startswith("sk_"):
        raise ApiError(403, "permission_error", "secret_key_required",
                       "This endpoint needs your secret key (sk_test_cierto_…); keep it on your server.")
    return t


def _client(request: Request) -> tuple[Tenant, str | None]:
    """A secret key, or a publishable key plus a customer-session client secret (checked by ``_check_session``)."""
    key = _key(request)
    t = KEYS.get(key)
    if t is None:
        raise ApiError(401, "authentication_error", "invalid_api_key", "Unknown API key.")
    if key.startswith("sk_"):
        return t, None
    cs = (request.headers.get("cierto-client-secret") or request.headers.get("pakka-client-secret")
          or request.query_params.get("client_secret"))
    if not cs:
        raise ApiError(401, "authentication_error", "client_secret_required",
                       "Publishable keys need a customer session: send 'Cierto-Client-Secret: cs_test_…'.")
    return t, cs


def _check_session(st: TenantState, cs: str | None, order_id: str) -> None:
    if cs is None:
        return
    session = st.sessions.get(cs)
    if session is None:
        raise ApiError(401, "authentication_error", "invalid_client_secret", "Unknown client secret.")
    if _now_ts() > session["expires_ts"]:
        raise ApiError(401, "authentication_error", "client_secret_expired",
                       "The customer session expired; fetch a new client secret from your server.")
    if session["order_id"] != order_id:
        raise ApiError(403, "permission_error", "client_secret_wrong_order",
                       "This client secret is scoped to a different order.")


def _json(raw: bytes):
    try:
        return json.loads((raw or b"{}").decode("utf-8"))
    except UnicodeDecodeError:
        raise _bad("invalid_json", "Body must be UTF-8 encoded JSON.") from None
    except json.JSONDecodeError as exc:
        raise _bad("invalid_json", f"Body is not valid JSON: {exc.msg}") from None


def _model(raw: bytes, model: type[BaseModel]) -> BaseModel:
    try:
        return model.model_validate(_json(raw))
    except ValidationError as exc:
        raise _bad("invalid_parameters", "; ".join(f"{'.'.join(map(str, e['loc'])) or 'body'}: {e['msg']}"
                                                   for e in exc.errors()[:5])) from None


def _idempotency(st: TenantState, key: str | None, fingerprint: str) -> dict | Reply:
    """Stripe semantics: the first successful result for a key is replayed; a key reused with other params is a 409.
    Returns the fields that make the op record its result under the key, or the replayed response."""
    if key is None:
        return {}
    if saved := st.idempotency.get(key):
        if saved[0] != fingerprint:
            raise ApiError(409, "idempotency_error", "idempotency_key_reused",
                           "Keys for idempotent requests can only be used with the same parameters they were first used with.")
        return Reply(JSONResponse(saved[2], saved[1], headers={"Idempotent-Replayed": "true"}))
    return {"idem": key, "fp": fingerprint}


def _idem_key(request: Request, raw: bytes) -> tuple[str | None, str]:
    key = request.headers.get("idempotency-key")
    if key is not None and (not key or len(key) > 255):
        raise _bad("idempotency_key_invalid", "Idempotency-Key must be 1-255 characters.")
    return key, hashlib.sha256(f"{request.method} {request.url.path}\n".encode() + raw).hexdigest()


def _op(st: TenantState, kind: str, idem: dict | Reply, **fields) -> dict | Reply:
    if isinstance(idem, Reply):
        return idem
    return {"op": kind, "at": st.wall().isoformat(), **idem, **fields}


def _events(st: TenantState, order_id: str) -> list[Event]:
    return st.sandbox.engine.events(st.tenant.id, order_id)


def _need_order(st: TenantState, order_id: str) -> list[Event]:
    events = _events(st, order_id)
    if not events:
        raise ApiError(404, "invalid_request_error", "order_not_found",
                       f"No order {order_id!r} for {st.tenant.brand}. Send it with POST /v1/orders or POST /v1/events, "
                       f"or use a test order: {', '.join(s.id for s in TEST_ORDERS)}.")
    return events


def _envelope(st: TenantState, order_id: str, view: dict) -> dict:
    t = st.tenant
    return {"object": "order_view", "order": {"id": order_id, "key": order_id, "tenant": t.id, "brand": t.brand,
                                              "livemode": False}, "view": view}


def _view(st: TenantState, order_id: str, locale: str = "en-IN") -> dict:
    view = build_view(st.sandbox.engine, st.tenant.id, order_id, st.tenant.brand, locale)
    if view is None:
        _need_order(st, order_id)
    return view


def _check_host_event(e: Event) -> str | None:
    """Facts a host or carrier may assert. Engine and remedy events are Cierto's own."""
    if e.type in _RESERVED or e.asserted_by is AssertedBy.ENGINE:
        return f"{e.type} events and asserted_by=engine are written by Cierto, not ingested"
    d = e.data
    if e.type is EventType.ETA_PROMISED:
        try:
            if datetime.fromisoformat(str(d["due_by"])).tzinfo is None:
                return "eta.promised data.due_by needs a timezone"
        except (KeyError, ValueError):
            return "eta.promised needs data.due_by as an ISO 8601 timestamp"
    if e.type is EventType.ETA_REVISED:
        for name in ("expected_by", "latest_by"):
            if name == "latest_by" and name not in d:
                continue
            try:
                if datetime.fromisoformat(str(d[name])).tzinfo is None:
                    return f"eta.revised data.{name} needs a timezone"
            except (KeyError, ValueError):
                return f"eta.revised needs data.{name} as an ISO 8601 timestamp"
    if e.type is EventType.RIDER_LOCATION and not all(isinstance(d.get(k), (int, float)) for k in ("lat", "lng")):
        return "rider.location needs numeric data.lat and data.lng"
    if e.type is EventType.DISPATCH_STOP_SEQUENCE and not (isinstance(d.get("stops"), list) and d["stops"]):
        return "dispatch.stop_sequence needs data.stops: [{order_ref, distance_to_you_m?}, …]"
    if e.type is EventType.ADDRESS_CHECK and not isinstance(d.get("distance_m"), (int, float)):
        return "address.check needs a numeric data.distance_m (map pin to typed address, in metres)"
    if e.type is EventType.REFUND_STATUS and d.get("stage") not in ("initiated", "processed", "credited"):
        return "refund.status needs data.stage: initiated | processed | credited"
    if "amount_inr" in d and not isinstance(d["amount_inr"], (int, float)):
        return "data.amount_inr must be a number"
    return None


# ---- request models ---------------------------------------------------------------------------

class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SessionIn(_In):
    order_id: str = Field(min_length=1, max_length=128)
    customer_ref: str = Field(min_length=1, max_length=128)


class CustomerSignals(_In):
    ref: str | None = None
    account_age_days: int | None = Field(None, ge=0)
    orders_90d: int | None = Field(None, ge=0)
    remedies_90d: int | None = Field(None, ge=0)


class EtaIn(_In):
    due_by: AwareDatetime
    shown_to_customer: str | None = None


class OrderIn(_In):
    order_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:\-]+$")
    customer_ref: str | None = None
    customer: CustomerSignals | None = None
    amount_inr: float = Field(ge=0)
    payment: str = "prepaid_upi"
    items: list[str] = Field(default_factory=list, max_length=50)
    title: str | None = None
    placed_at: AwareDatetime | None = None
    vertical: Literal["parcel", "quick"] | None = None
    account_phone_last4: str | None = Field(None, pattern=r"^\d{4}$")
    eta: EtaIn | None = None
    extras: dict[Literal["restaurant", "kitchen", "rider", "area"], str] | None = None


class ActionIn(_In):
    action: str
    locale: Literal["en-IN", "hi-Latn-IN"] = "en-IN"
    items: list[str] | None = None
    photo: bool | None = None
    landmark: str | None = Field(None, max_length=200)


class AskIn(_In):
    question: str = Field(min_length=1, max_length=500)
    locale: Literal["en-IN", "hi-Latn-IN"] = "en-IN"


class AppearanceIn(_In):
    theme: Literal["smytten", "zomato", "swish", "neutral"] | None = None
    variables: dict[str, str] | None = None


class ConfigIn(_In):
    policy: dict | None = None
    appearance: AppearanceIn | None = None
    webhook_url: str | None = None


class SimulateIn(_In):
    order_id: str | None = None
    action: str = "report_not_received"
    policy: dict = Field(default_factory=dict)
    customer: CustomerSignals | None = None


class ApproveIn(_In):
    approved_by: str = Field("host", min_length=1, max_length=120)


class AdvanceIn(_In):
    minutes: float = 0
    hours: float = 0


# ---- routes -----------------------------------------------------------------------------------

router = APIRouter()


def _dev_only() -> None:
    if not is_dev():
        raise ApiError(404, "invalid_request_error", "not_found", "Dev endpoints exist only in dev mode.")


@router.get("/v1/dev/keys")
async def dev_keys() -> dict:
    _dev_only()
    return {"object": "list", "mode": "test", "api_version": API_VERSION,
            "note": "Test-mode keys for local development. Derived from CIERTO_DEV_SEED; never use them in production.",
            "data": [{"tenant": t.id, "brand": t.brand, "vertical": t.vertical, "publishable_key": t.publishable_key,
                      "secret_key": t.secret_key, "webhook_secret": t.webhook_secret,
                      "test_orders": [{"id": s.id, "description": s.description} for s in TEST_ORDERS],
                      "test_customer_ref": TEST_CUSTOMER["ref"]} for t in TENANTS.values()]}


@router.post("/v1/dev/advance")
async def dev_advance(request: Request) -> JSONResponse:
    _dev_only()
    t = _secret(request)
    body = _model(await request.body(), AdvanceIn)
    if body.minutes < 0 or body.hours < 0:
        raise _bad("invalid_parameters", "The test clock only moves forward.")
    return await _write(request, t, lambda st: _op(st, "advance", {}, minutes=body.minutes, hours=body.hours))


@router.post("/v1/dev/reset")
async def dev_reset(request: Request) -> dict:
    _dev_only()
    t = _secret(request)

    def run():
        mgr = request.app.state.sdk
        name = _log_name(mgr.backend, t.id)
        _rotate(request.app, t, name, mgr.read(name, lambda st: st.carry(), create=lambda: _base(t.id)))
        return _read_sync(request.app, t, lambda st: {
            "object": "sandbox", "tenant": t.id, "reset": True, "now": st.sandbox.clock.now().isoformat(),
            "test_orders": [s.id for s in TEST_ORDERS]}, tick=True)
    return await run_in_threadpool(run)


@router.get("/v1/dev/webhook_log")
async def dev_webhook_log(request: Request, tenant: str | None = None, limit: int = 50) -> dict:
    """Signed outgoing webhooks, newest first. In dev mode ?tenant= works without a key, for the demo site."""
    _dev_only()
    if request.headers.get("authorization"):
        t = _secret(request)
    elif tenant in TENANTS:
        t = TENANTS[tenant]
    else:
        raise ApiError(401, "authentication_error", "missing_api_key", "Send your secret key, or ?tenant=smytten|zomato|swish.")

    def run(st: TenantState) -> list[dict]:
        entries = [dict(e, delivery=dict(e["delivery"]) if e["delivery"] else None)
                   for e in list(reversed(st.webhooks.entries))[:max(1, min(limit, 500))]]
        sent = [e for e in entries if e["delivery"]]
        # Delivery happens on whichever instance sent it; the status is shared through the store.
        statuses = request.app.state.backend.get_many([f"whd:{e['id']}" for e in sent]) if sent else []
        for e, status in zip(sent, statuses):
            if status is not None:
                e["delivery"]["status"] = int(status) if status.isdigit() else status
        return entries
    entries = await _read(request, t, run)
    return {"object": "list", "tenant": t.id, "signing": "Standard Webhooks v1 (HMAC-SHA256 over id.timestamp.body)",
            "data": entries}


@router.post("/v1/customer_sessions")
async def create_customer_session(request: Request) -> JSONResponse:
    t = _secret(request)
    raw = await request.body()
    key, fp = _idem_key(request, raw)

    def plan(st: TenantState):
        idem = _idempotency(st, key, fp)
        if isinstance(idem, Reply):
            return idem
        body = _model(raw, SessionIn)
        events = _need_order(st, body.order_id)
        placed = next((e.data for e in reversed(events) if e.type is EventType.ORDER_PLACED), {})
        known = (placed.get("customer") or {}).get("ref")
        if known and known != body.customer_ref:
            raise ApiError(403, "permission_error", "customer_mismatch",
                           f"Order {body.order_id!r} belongs to a different customer_ref.")
        return _op(st, "session", idem, cs="cs_test_" + secrets.token_urlsafe(24), order_id=body.order_id,
                   customer_ref=body.customer_ref, expires_ts=round(_now_ts() + SESSION_TTL.total_seconds(), 3))
    return await _write(request, t, plan)


@router.post("/v1/events")
async def ingest_events(request: Request) -> JSONResponse:
    t = _secret(request)
    raw = await request.body()
    if request.headers.get("webhook-signature"):
        try:
            verify(t.webhook_secret, request.headers, raw)
        except WebhookVerificationError as exc:
            raise ApiError(401, "authentication_error", "signature_invalid", str(exc)) from None
    key, fp = _idem_key(request, raw)

    def plan(st: TenantState):
        idem = _idempotency(st, key, fp)
        if isinstance(idem, Reply):
            return idem
        body = _json(raw)
        items = body["events"] if isinstance(body, dict) and "events" in body else [body]
        if not isinstance(items, list) or not items:
            raise _bad("invalid_parameters", "Send one event, or {\"events\": [...]} with 1-100 events.")
        if len(items) > 100:
            raise _bad("batch_too_large", "At most 100 events per request.")
        return _op(st, "events", idem, items=items)
    return await _write(request, t, plan)


@router.post("/v1/orders")
async def upsert_order(request: Request) -> JSONResponse:
    t = _secret(request)
    raw = await request.body()
    key, fp = _idem_key(request, raw)

    def plan(st: TenantState):
        idem = _idempotency(st, key, fp)
        if isinstance(idem, Reply):
            return idem
        _model(raw, OrderIn)   # validate here; the op carries the body and the fold validates it again
        return _op(st, "order", idem, body=_json(raw))
    return await _write(request, t, plan)


def _versioned(t: Tenant, order_id: str, name: str, kind: EventType, at: datetime, data: dict) -> Event:
    """Upserts append a new version only when the content changed (same content → same event_id → duplicate)."""
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:12]
    return Event(event_id=f"{order_id}:{name}:{digest}", tenant_id=t.id, order_ref=order_id, type=kind,
                 occurred_at=at, asserted_by=AssertedBy.MERCHANT, source_adapter="api.orders", data=data)


@router.get("/v1/orders")
async def list_orders(request: Request) -> dict:
    t = _secret(request)

    def run(st: TenantState) -> dict:
        data = []
        for oid in st.sandbox.orders:
            v = build_view(st.sandbox.engine, t.id, oid, t.brand)
            if v:
                data.append({"id": oid, "test": oid.startswith("ord_test_"), "state": v["state"], "tone": v["tone"],
                             "proof": v["proof"]["state"], "vertical": v["vertical"], "amount_inr": v["amount_inr"],
                             "decision": v["resolution"]["decision"] if v["resolution"] else None})
        return {"object": "list", "data": data}
    return await _read(request, t, run)


@router.get("/v1/orders/{order_id}/view")
async def order_view(order_id: str, request: Request, locale: Literal["en-IN", "hi-Latn-IN"] = "en-IN") -> dict:
    t, cs = _client(request)

    def run(st: TenantState) -> dict:
        _check_session(st, cs, order_id)
        return _envelope(st, order_id, _view(st, order_id, locale))
    return await _read(request, t, run)


@router.post("/v1/orders/{order_id}/actions")
async def order_action(order_id: str, request: Request) -> JSONResponse:
    t, cs = _client(request)
    raw = await request.body()

    def plan(st: TenantState):
        _check_session(st, cs, order_id)
        body = _model(raw, ActionIn)
        _need_order(st, order_id)
        if body.action not in ACTIONS:
            raise _bad("invalid_action", f"unknown action {body.action!r}; expected one of {', '.join(ACTIONS)}",
                       allowed=list(ACTIONS))
        return _op(st, "act", {}, order_id=order_id, action=body.action, locale=body.locale,
                   detail={"items": body.items, "photo": body.photo, "landmark": body.landmark})
    return await _write(request, t, plan)


@router.post("/v1/orders/{order_id}/ask")
async def order_ask(order_id: str, request: Request) -> dict:
    """A grounded answer to the shopper's question: composed only from the order's view and projection."""
    t, cs = _client(request)
    raw = await request.body()

    def run(st: TenantState):
        _check_session(st, cs, order_id)
        body = _model(raw, AskIn)
        _need_order(st, order_id)
        return body, asking.compose(st.sandbox.engine, t.id, order_id, t.brand, body.question, body.locale)
    body, (answer, facts) = await _read(request, t, run)
    # The optional model call runs outside the lock, in a worker thread (it can take seconds).
    return await run_in_threadpool(asking.rephrase, answer, facts, body.question, body.locale)


@router.get("/v1/orders/{order_id}/events")
async def order_events(order_id: str, request: Request) -> dict:
    """The audit log: every fact, who asserted it, and every decision Cierto took."""
    t = _secret(request)

    def run(st: TenantState) -> dict:
        _need_order(st, order_id)
        now = st.sandbox.clock.now()
        return {"object": "list", "order_id": order_id, "data": [
            {"seq": s.seq, **s.event.model_dump(mode="json", exclude_none=True)}
            for s in st.sandbox.store.events_for_order(t.id, order_id) if s.event.occurred_at <= now]}
    return await _read(request, t, run)


@router.get("/v1/config")
async def get_config(request: Request) -> dict:
    return await _read(request, _secret(request), lambda st: st.config(), tick=False)


@router.put("/v1/config")
async def put_config(request: Request) -> JSONResponse:
    t = _secret(request)
    body = _model(await request.body(), ConfigIn)

    def plan(st: TenantState):
        policy = st.policy
        if body.policy is not None:
            try:
                policy = Policy.model_validate({**st.policy.model_dump(), **body.policy})
            except ValidationError as exc:
                raise _bad("invalid_policy", "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
                                                       for e in exc.errors()[:5])) from None
        appearance = dict(st.appearance)
        if body.appearance:
            if body.appearance.theme:
                appearance["theme"] = body.appearance.theme
            if body.appearance.variables is not None:
                _check_variables(body.appearance.variables)
                appearance["variables"] = dict(body.appearance.variables)
        if body.webhook_url is not None and body.webhook_url and not re.match(r"^https?://", body.webhook_url):
            raise _bad("invalid_webhook_url", "webhook_url must be an http(s) URL, or \"\" to stop sending.")
        url = {} if body.webhook_url is None else {"webhook_url": body.webhook_url}
        return _op(st, "config", {}, policy=policy.model_dump(), appearance=appearance, **url)
    return await _write(request, t, plan)


def _check_variables(variables: dict[str, str]) -> None:
    for name, value in variables.items():
        if name not in APPEARANCE_VARIABLES:
            raise _bad("invalid_appearance", f"Unknown appearance variable {name!r}.", allowed=list(APPEARANCE_VARIABLES))
        if not _SAFE_VALUE.match(value):
            raise _bad("invalid_appearance", f"Value for {name!r} must be a plain CSS value (no ; {{ }} < > \\).")


@router.get("/v1/client_config")
async def client_config(request: Request) -> dict:
    """What the browser SDK may read with a publishable key: brand and appearance defaults."""
    key = _key(request)
    t = KEYS.get(key)
    if t is None:
        raise ApiError(401, "authentication_error", "invalid_api_key", "Unknown API key.")
    appearance = await _read(request, t, lambda st: st.appearance, tick=False)
    return {"object": "client_config", "tenant": t.id, "brand": t.brand, "vertical": t.vertical,
            "appearance": appearance, "locales": ["en-IN", "hi-Latn-IN"], "livemode": False}


@router.post("/v1/config/simulate")
async def simulate(request: Request) -> dict:
    """Run the resolver under a proposed policy against one order, or every order in the sandbox. Writes nothing."""
    t = _secret(request)
    body = _model(await request.body(), SimulateIn)
    if body.action not in ACTIONS:
        raise _bad("invalid_action", f"Unknown action {body.action!r}.", allowed=list(ACTIONS))
    customer = body.customer.model_dump(exclude_none=True) if body.customer else None

    def run(st: TenantState) -> dict:
        try:
            proposed = Policy.model_validate({**st.policy.model_dump(), **body.policy})
        except ValidationError as exc:
            raise _bad("invalid_policy", "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
                                                   for e in exc.errors()[:5])) from None
        sb = st.sandbox
        ids = [body.order_id] if body.order_id else list(sb.orders)
        if body.order_id:
            _need_order(st, body.order_id)
        results, totals = [], {"current": 0.0, "proposed": 0.0}
        for oid in ids:
            before = sb.desk.simulate(t.id, oid, body.action, st.policy, customer)
            after = sb.desk.simulate(t.id, oid, body.action, proposed, customer)
            a, b = before.view(), after.view()
            for label, res in (("current", before), ("proposed", after)):
                if res.remedy["kind"] in ("refund", "partial_refund") and not res.needs_approval:
                    totals[label] += res.remedy["amount_inr"] or 0
            results.append({
                "order_id": oid,
                "changed": [k for k in ("decision", "needs_approval", "remedy") if a[k] != b[k]],
                "current": {"resolution": a, "approval_reason": before.approval_reason,
                            "trust": before.trust.to_dict() if before.trust else None},
                "proposed": {"resolution": b, "approval_reason": after.approval_reason,
                             "trust": after.trust.to_dict() if after.trust else None},
            })
        return {"object": "simulation", "action": body.action,
                "policy": {"current": st.policy.model_dump(), "proposed": proposed.model_dump()},
                "summary": {"orders": len(results), "changed": sum(bool(r["changed"]) for r in results),
                            "auto_refund_inr": totals},
                "data": results}
    return await _read(request, t, run)


@router.get("/v1/remedies/{remedy_id}")
async def get_remedy(remedy_id: str, request: Request) -> dict:
    t = _secret(request)
    obj = await _read(request, t, lambda st: st.sandbox.desk.remedy(t.id, remedy_id))
    if obj is None:
        raise ApiError(404, "invalid_request_error", "remedy_not_found", f"No remedy {remedy_id!r}.")
    return obj


@router.post("/v1/remedies/{remedy_id}/approve")
async def approve_remedy(remedy_id: str, request: Request) -> JSONResponse:
    t = _secret(request)
    raw = await request.body()
    key, fp = _idem_key(request, raw)

    def plan(st: TenantState):
        idem = _idempotency(st, key, fp)
        if isinstance(idem, Reply):
            return idem
        body = _model(raw, ApproveIn)
        desk = st.sandbox.desk
        order_ref = desk.remedies.get((t.id, remedy_id))
        if not order_ref:
            raise ApiError(404, "invalid_request_error", "remedy_not_found", f"No remedy {remedy_id!r}.")
        state = desk.state(t.id, order_ref)
        if not state or state["remedy"].get("id") != remedy_id:
            raise ApiError(409, "invalid_request_error", "remedy_not_approvable",
                           "this remedy was superseded by a later decision")
        if state["status"] != "proposed":
            raise ApiError(409, "invalid_request_error", "remedy_not_approvable", f"remedy is already {state['status']}")
        return _op(st, "approve", idem, remedy_id=remedy_id, approved_by=body.approved_by)
    return await _write(request, t, plan)
