"""App-level WAF: request hygiene, rate limits, the LLM budget, security headers and access logs.

Cloud Armor costs money, so the first line of defence is this middleware. It runs before routing:

  1. methods: GET HEAD POST PUT OPTIONS, else 405. Path/query/header sizes: 414 / 431.
  2. scanner paths (/wp-, .php, /.env, /.git, phpmyadmin, …): a bare 404 without touching the app.
  3. body size: 413 over MAX_BODY_BYTES (MAX_EVENTS_BODY_BYTES for the /v1/events batch).
  4. rate limits per client IP (fixed windows, shared through Redis when REDIS_URL is set): 429 + Retry-After.
  5. API writes with no User-Agent at all: 403. Crawlers are welcome (search and AI answer engines alike).

Client IP. X-Forwarded-For is a list every hop appends to: "<whatever the client sent>, <client>, <proxy>…".
The left-most entry is whatever the client chose to send, so it is spoofable and worthless for limits.
We count TRUSTED_PROXY_HOPS entries from the right: 1 for Cloud Run's front end or Caddy (each appends
the address it saw), 2 behind a Google external Application Load Balancer. 0 means no proxy: the socket
peer (and then uvicorn is started without proxy headers, so nothing can rewrite it).

The LLM budget (``llm_allowed``) is checked by resolver._llm_call itself, so no caller can skip it.
"""
import asyncio
import hashlib
import json
import logging
import os
import re
import socket
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .shared import MemoryBackend

log = logging.getLogger("wismo.access")

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
       "font-src 'self' data:; connect-src 'self'; frame-src 'self'; frame-ancestors 'self'; base-uri 'self'; "
       "form-action 'self'; object-src 'none'")
SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=(), interest-cohort=()"),
    (b"cross-origin-opener-policy", b"same-origin"),
]
HSTS = (b"strict-transport-security", b"max-age=63072000; includeSubDomains")
METHODS = {"GET", "HEAD", "POST", "PUT", "OPTIONS"}
SCANNERS = re.compile(
    r"(/wp-|/wordpress|\.php\d?$|\.php/|\.aspx?$|\.jsp$|\.cgi$|/cgi-bin|/\.env|/\.git|/\.svn|/\.hg|/\.aws|/\.ssh|"
    r"/\.ds_store|/\.htaccess|/\.htpasswd|phpmyadmin|/pma/|/xmlrpc|/vendor/phpunit|/actuator|/boaform|/server-status|"
    r"/owa/|/ecp/|/hnap1|/solr/|/manager/html|\.(sql|bak|old|swp)$)", re.I)
ASK = re.compile(r"^/v1/(demo/sessions/[^/]+/orders/[^/]+|orders/[^/]+)/ask$")
QUIET = {"/healthz", "/readyz"}   # probes: never limited, never logged
# Immutable or cache-friendly files: cheap to serve, so not worth a shared-counter round trip each.
STATIC = ("/assets/", "/site/", "/og/", "/sdk/", "/favicon", "/apple-touch-icon", "/icon-")
SERVED_BY = os.environ.get("SERVED_BY") or socket.gethostname()


def parse_rates(spec: str) -> list[tuple[int, int]]:
    """"20/m,200/d" -> [(20, 60), (200, 86400)]. Units s m h d, with an optional multiple: "20/10m"."""
    out = []
    for part in filter(None, (p.strip() for p in spec.split(","))):
        count, _, per = part.partition("/")
        m = re.fullmatch(r"(\d*)\s*([smhd]?)", per.strip().lower())
        if not m:
            raise ValueError(f"bad rate {part!r}")
        out.append((int(count), int(m.group(1) or 1) * {"s": 1, "m": 60, "h": 3600, "d": 86400, "": 1}[m.group(2)]))
    return out


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass
class WafConfig:
    rate_limits: bool = True
    general: list = field(default_factory=lambda: parse_rates("300/m"))
    ask: list = field(default_factory=lambda: parse_rates("20/m,200/d"))
    demo_create: list = field(default_factory=lambda: parse_rates("20/10m"))
    sdk_write_ip: list = field(default_factory=lambda: parse_rates("60/m"))
    sdk_write_key: list = field(default_factory=lambda: parse_rates("600/m"))
    max_body: int = 64 * 1024
    max_events_body: int = 1024 * 1024
    max_path: int = 2048
    max_query: int = 4096
    max_headers: int = 16 * 1024
    trusted_hops: int = 1

    @classmethod
    def from_env(cls) -> "WafConfig":
        e = os.environ.get
        return cls(
            rate_limits=e("WAF_RATE_LIMITS", "on").lower() not in ("0", "off", "false", "no"),
            general=parse_rates(e("RATE_LIMIT_GENERAL", "300/m")),
            ask=parse_rates(e("RATE_LIMIT_ASK", "20/m,200/d")),
            demo_create=parse_rates(e("RATE_LIMIT_DEMO_CREATE", "20/10m")),
            sdk_write_ip=parse_rates(e("RATE_LIMIT_SDK_WRITE", "60/m")),
            sdk_write_key=parse_rates(e("RATE_LIMIT_SDK_KEY", "600/m")),
            max_body=_env_int("MAX_BODY_BYTES", 64 * 1024),
            max_events_body=_env_int("MAX_EVENTS_BODY_BYTES", 1024 * 1024),
            trusted_hops=_env_int("TRUSTED_PROXY_HOPS", 1),
        )


# ---- request context (read by the LLM budget) -----------------------------------------------------

@dataclass(frozen=True)
class RequestContext:
    ip: str | None
    backend: object


REQUEST: ContextVar[RequestContext | None] = ContextVar("wismo_request", default=None)
_FALLBACK = MemoryBackend()   # CLI and tests outside a request


def llm_allowed() -> bool:
    """Spend one model call: false once LLM_DAILY_BUDGET calls were made today (UTC) across all instances,
    or LLM_IP_DAILY by this client. Fails closed: if the counters can't be read, no model call."""
    ctx = REQUEST.get()
    backend = ctx.backend if ctx else _FALLBACK
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    keys = [(f"llm:{day}", 2 * 86400)] + ([(f"llmip:{day}:{ctx.ip}", 86400)] if ctx and ctx.ip else [])
    try:
        counts = backend.hit(keys)
    except Exception:
        return False
    return counts[0] <= _env_int("LLM_DAILY_BUDGET", 1500) and \
        (len(counts) == 1 or counts[1] <= _env_int("LLM_IP_DAILY", 100))


# ---- helpers --------------------------------------------------------------------------------------

def client_ip(scope, hops: int) -> str:
    """The TRUSTED_PROXY_HOPS-th X-Forwarded-For entry from the right; the socket peer for 0 hops or no header."""
    if hops > 0:
        xff = ",".join(v.decode("latin-1") for k, v in scope["headers"] if k == b"x-forwarded-for")
        hosts = [h.strip() for h in xff.split(",") if h.strip()]
        if hosts:
            return hosts[-hops] if len(hosts) >= hops else hosts[0]
    peer = scope.get("client")
    return peer[0] if peer else "unknown"


def external_https(scope) -> bool:
    """uvicorn's proxy-headers middleware has already applied X-Forwarded-Proto to the scheme."""
    return scope.get("scheme") == "https"


def _json_response(status: int, body: dict, extra: list | None = None) -> tuple[int, list, bytes]:
    raw = json.dumps(body, separators=(",", ":")).encode()
    return status, [(b"content-type", b"application/json"), (b"content-length", str(len(raw)).encode()),
                    (b"cache-control", b"no-store"), *(extra or [])], raw


def _error(status: int, code: str, message: str, extra: list | None = None) -> tuple[int, list, bytes]:
    kind = "rate_limit_error" if status == 429 else "invalid_request_error"
    return _json_response(status, {"error": {"type": kind, "code": code, "message": message}}, extra)


class Firewall:
    """ASGI middleware: screen, limit, then pass through, adding security headers and one access-log line."""

    def __init__(self, app, backend, config: WafConfig | None = None):
        self.app, self._backend = app, backend   # a backend, or a callable returning the app's current one
        self.config = config or WafConfig.from_env()
        self.served_by = SERVED_BY.encode("latin-1", "replace")[:64]
        self.trace_project = os.environ.get("GOOGLE_CLOUD_PROJECT")

    @property
    def backend(self):
        return self._backend() if callable(self._backend) else self._backend

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        start, cfg = time.perf_counter(), self.config
        ip = client_ip(scope, cfg.trusted_hops)
        https = external_https(scope)
        state = {"status": 500, "bytes": 0, "blocked": None}

        async def send_wrapped(message):
            if message["type"] == "http.response.start":
                state["status"] = message["status"]
                headers = [h for h in message.get("headers", [])]
                names = {k.lower() for k, _ in headers}
                headers += [h for h in SECURITY_HEADERS if h[0] not in names]
                headers.append((b"x-served-by", self.served_by))
                if https:
                    headers.append(HSTS)
                ctype = next((v for k, v in headers if k.lower() == b"content-type"), b"")
                if ctype.startswith(b"text/html") and b"content-security-policy" not in names \
                        and scope["path"] != "/v1/docs":
                    csp = CSP + ("; upgrade-insecure-requests" if https else "")
                    headers.append((b"content-security-policy", csp.encode()))
                message = {**message, "headers": headers}
            elif message["type"] == "http.response.body":
                state["bytes"] += len(message.get("body", b""))
            await send(message)

        token = REQUEST.set(RequestContext(ip, self.backend))
        try:
            blocked = await self._screen(scope, ip)
            if blocked is None and scope["method"] in ("POST", "PUT"):
                blocked, receive = await self._buffer_body(scope, receive)
            if blocked is not None:
                state["blocked"] = blocked[3] if len(blocked) > 3 else "blocked"
                status, headers, body = blocked[:3]
                await send_wrapped({"type": "http.response.start", "status": status, "headers": headers})
                await send_wrapped({"type": "http.response.body", "body": b"" if scope["method"] == "HEAD" else body})
                return
            await self.app(scope, receive, send_wrapped)
        finally:
            REQUEST.reset(token)
            if scope["path"] not in QUIET:
                self._log(scope, ip, state, time.perf_counter() - start)

    # ---- screening ----

    async def _screen(self, scope, ip: str):
        cfg, method, path = self.config, scope["method"], scope["path"]
        if method not in METHODS:
            return (*_error(405, "method_not_allowed", f"{method} is not allowed.",
                            [(b"allow", b"GET, HEAD, POST, PUT, OPTIONS")]), "method")
        if len(scope.get("raw_path") or path) > cfg.max_path or len(scope.get("query_string", b"")) > cfg.max_query:
            return (*_error(414, "uri_too_long", "The request URI is too long."), "uri")
        if sum(len(k) + len(v) for k, v in scope["headers"]) > cfg.max_headers:
            return (*_error(431, "headers_too_large", "The request headers are too large."), "headers")
        if SCANNERS.search(path):
            return 404, [(b"content-type", b"text/plain; charset=utf-8"), (b"content-length", b"9"),
                         (b"cache-control", b"no-store")], b"Not Found", "scanner"
        if method in ("POST", "PUT"):
            length = next((v for k, v in scope["headers"] if k == b"content-length"), None)
            if length is not None:
                try:
                    n = int(length)
                except ValueError:
                    return (*_error(400, "bad_content_length", "Content-Length is not a number."), "length")
                if n > self._body_limit(path):
                    return (*_error(413, "body_too_large", f"The body is over {self._body_limit(path)} bytes."), "body")
        if cfg.rate_limits and path not in QUIET and not (method in ("GET", "HEAD") and path.startswith(STATIC)):
            limited = await self._limit(scope, ip)
            if limited is not None:
                return limited
        if method in ("POST", "PUT") and path.startswith("/v1/") and not self._header(scope, b"user-agent").strip():
            return (*_error(403, "user_agent_required", "Send a User-Agent header with API writes."), "user_agent")
        return None

    def _body_limit(self, path: str) -> int:
        return self.config.max_events_body if path == "/v1/events" else self.config.max_body

    @staticmethod
    def _header(scope, name: bytes) -> str:
        return next((v.decode("latin-1") for k, v in scope["headers"] if k == name), "")

    async def _buffer_body(self, scope, receive):
        """Read the body up front (bounded), so a chunked upload can't slip past the size limit."""
        limit, chunks, size = self._body_limit(scope["path"]), [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return None, _replay([message], receive)
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > limit:
                return (*_error(413, "body_too_large", f"The body is over {limit} bytes."), "body"), receive
            chunks.append(chunk)
            if not message.get("more_body"):
                break
        return None, _replay([{"type": "http.request", "body": b"".join(chunks), "more_body": False}], receive)

    def _rules(self, scope, ip: str) -> list[tuple[str, str, int, int]]:
        """(rule, bucket, limit, window seconds) for this request."""
        cfg, method, path = self.config, scope["method"], scope["path"]
        rules = [("all", ip, n, w) for n, w in cfg.general]
        if method == "POST" and ASK.match(path):
            rules += [("ask", ip, n, w) for n, w in cfg.ask]
        if method == "POST" and path == "/v1/demo/sessions":
            rules += [("demo", ip, n, w) for n, w in cfg.demo_create]
        if method in ("POST", "PUT") and path.startswith("/v1/") and not path.startswith("/v1/demo/"):
            rules += [("sdkw", ip, n, w) for n, w in cfg.sdk_write_ip]
            key = self._header(scope, b"authorization").partition(" ")[2].strip()
            if key:
                bucket = hashlib.sha256(key.encode()).hexdigest()[:16]
                rules += [("sdkk", bucket, n, w) for n, w in cfg.sdk_write_key]
        return rules

    async def _limit(self, scope, ip: str):
        rules, now = self._rules(scope, ip), time.time()
        keys = [(f"rl:{name}:{w}:{bucket}:{int(now // w)}", w + 1) for name, bucket, _, w in rules]
        try:
            if isinstance(self.backend, MemoryBackend):
                counts = self.backend.hit(keys)
            else:
                counts = await asyncio.to_thread(self.backend.hit, keys)
        except Exception:
            return None   # fail open: the limits protect the service, they must not take it down
        over = [(w, name) for (name, _, n, w), c in zip(rules, counts) if c > n]
        if not over:
            return None
        retry = max(int(w - now % w) + 1 for w, _ in over)
        return (*_error(429, "rate_limited", f"Too many requests; retry in {retry} s.",
                        [(b"retry-after", str(retry).encode())]), "rate:" + ",".join(sorted({n for _, n in over})))

    # ---- access log ----

    def _log(self, scope, ip: str, state: dict, seconds: float) -> None:
        if not log.isEnabledFor(logging.INFO):
            return
        status = state["status"]
        entry = {
            "severity": "ERROR" if status >= 500 else "WARNING" if status >= 400 and state["blocked"] else "INFO",
            "message": f"{scope['method']} {scope['path']} {status}",
            "httpRequest": {"requestMethod": scope["method"], "requestUrl": scope["path"], "status": status,
                            "responseSize": str(state["bytes"]), "remoteIp": ip, "latency": f"{seconds:.4f}s",
                            "userAgent": self._header(scope, b"user-agent")[:200],
                            "protocol": "HTTP/" + scope.get("http_version", "1.1")},
            "instance": SERVED_BY,
        }
        if state["blocked"]:
            entry["waf"] = state["blocked"]
        trace = self._header(scope, b"x-cloud-trace-context").split("/")[0]
        if trace and self.trace_project:
            entry["logging.googleapis.com/trace"] = f"projects/{self.trace_project}/traces/{trace}"
        log.info(json.dumps(entry, separators=(",", ":")) if _JSON else
                 f'{ip} "{scope["method"]} {scope["path"]}" {status} {state["bytes"]} {seconds * 1000:.1f}ms'
                 + (f' waf={state["blocked"]}' if state["blocked"] else ""))


def _replay(messages: list, then):
    """A receive() that hands over the buffered body, then defers to the server's (for the disconnect)."""
    async def receive():
        return messages.pop(0) if messages else await then()
    return receive


# ---- logging --------------------------------------------------------------------------------------

_JSON = False


class JsonFormatter(logging.Formatter):
    """One JSON object per line (Cloud Logging reads severity, message and httpRequest from it)."""

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        if msg.startswith("{"):
            return msg
        out = {"severity": record.levelname, "message": msg,
               "logger": record.name, "time": datetime.fromtimestamp(record.created, timezone.utc).isoformat()}
        if record.exc_info:
            out["stack_trace"] = self.formatException(record.exc_info)
        return json.dumps(out, separators=(",", ":"))


def log_config(fmt: str | None) -> dict | None:
    """dictConfig for uvicorn and the access log. LOG_FORMAT=json: JSON lines on stdout; text: one line per
    request; unset: uvicorn's defaults and no access log (local dev)."""
    global _JSON
    fmt = (fmt or "").lower()
    if fmt not in ("json", "text"):
        return None
    _JSON = fmt == "json"
    formatter = {"()": JsonFormatter} if _JSON else {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}
    return {
        "version": 1, "disable_existing_loggers": False,
        "formatters": {"main": formatter},
        "handlers": {"stdout": {"class": "logging.StreamHandler", "formatter": "main", "stream": "ext://sys.stdout"}},
        "loggers": {
            "uvicorn": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": [], "level": "WARNING", "propagate": False},
            "wismo": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
        },
    }
