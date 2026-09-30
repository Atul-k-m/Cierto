"""Standard Webhooks signing and verification (https://www.standardwebhooks.com).

Headers: ``webhook-id``, ``webhook-timestamp`` (unix seconds), ``webhook-signature: v1,<base64>``
(space-separated when a secret is rotating). Signed content: ``{id}.{timestamp}.{raw body}``,
HMAC-SHA256 with the base64-decoded part of a ``whsec_…`` secret. Used both ways: Cierto signs
what it sends, and verifies a host's signed POST /v1/events when the headers are present.
"""
import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
from collections.abc import Mapping

TOLERANCE_SECONDS = 300   # reject stale or future-dated messages (replay protection)


class WebhookVerificationError(Exception):
    pass


def secret_from_seed(seed: str) -> str:
    return "whsec_" + base64.b64encode(hashlib.sha256(seed.encode()).digest()[:24]).decode()


def _key(secret: str) -> bytes:
    return base64.b64decode(secret.removeprefix("whsec_"))


def sign(secret: str, msg_id: str, timestamp: int, body: str | bytes) -> str:
    payload = body.decode() if isinstance(body, bytes) else body
    mac = hmac.new(_key(secret), f"{msg_id}.{timestamp}.{payload}".encode(), hashlib.sha256).digest()
    return "v1," + base64.b64encode(mac).decode()


def headers(secret: str, msg_id: str, body: str, timestamp: int | None = None) -> dict[str, str]:
    ts = int(time.time()) if timestamp is None else timestamp
    return {"webhook-id": msg_id, "webhook-timestamp": str(ts), "webhook-signature": sign(secret, msg_id, ts, body)}


def verify(secret: str, hdrs: Mapping[str, str], body: bytes | str, now: float | None = None) -> None:
    """Raise WebhookVerificationError unless one v1 signature matches and the timestamp is fresh."""
    msg_id, ts, sigs = hdrs.get("webhook-id"), hdrs.get("webhook-timestamp"), hdrs.get("webhook-signature")
    if not (msg_id and ts and sigs):
        raise WebhookVerificationError("missing webhook-id, webhook-timestamp or webhook-signature")
    try:
        stamp = int(ts)
    except ValueError:
        raise WebhookVerificationError("webhook-timestamp is not unix seconds") from None
    if abs((time.time() if now is None else now) - stamp) > TOLERANCE_SECONDS:
        raise WebhookVerificationError("webhook-timestamp is outside the 5-minute tolerance")
    expected = sign(secret, msg_id, stamp, body).split(",", 1)[1]
    for candidate in sigs.split():
        version, _, value = candidate.partition(",")
        if version == "v1" and hmac.compare_digest(value, expected):   # ignore other schemes (no downgrade)
            return
    raise WebhookVerificationError("no matching v1 signature")


class WebhookLog:
    """Outgoing webhooks for one tenant: each is recorded, signed and, if an endpoint is set, sent once.

    Inside a replayable session, ``ids`` (sessions.seeded) and ``stamp`` (created -> unix seconds) make every
    instance record identical entries; ``claim`` (a shared SET NX) makes exactly one instance send each one,
    and ``report`` shares the delivery status. A send re-signs with the current time, as Standard Webhooks
    expects of every attempt."""

    def __init__(self, tenant: str, secret: str, limit: int = 500, ids=None, stamp=None, claim=None, report=None):
        self.tenant, self.secret, self.limit = tenant, secret, limit
        self.url: str | None = None
        self.entries: list[dict] = []
        self.ids = ids or (lambda prefix: prefix + secrets.token_hex(12))
        self.stamp = stamp or (lambda created: int(time.time()))
        self.claim = claim or (lambda msg_id: True)
        self.report = report or (lambda msg_id, status: None)

    def record(self, kind: str, obj: dict, created: str) -> dict:
        from .sessions import after_commit

        msg_id = self.ids("msg_")
        payload = {"id": self.ids("evt_"), "type": kind, "api_version": "2026-09-30",
                   "created": created, "livemode": False, "tenant": self.tenant, "data": {"object": obj}}
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        entry = {"id": msg_id, "type": kind, "created": created,
                 "headers": headers(self.secret, msg_id, body, self.stamp(created)),
                 "body": body, "payload": payload, "delivery": None}
        self.entries.append(entry)
        del self.entries[:-self.limit]
        if self.url:
            entry["delivery"] = {"url": self.url, "status": "pending"}
            after_commit(lambda: self.claim(msg_id) and threading.Thread(target=self._send, args=(entry,),
                                                                          daemon=True).start())
        return entry

    def _send(self, entry: dict) -> None:
        # One attempt, no retries: a proof of concept. Production retries with backoff for 3 days.
        import httpx
        try:
            r = httpx.post(entry["delivery"]["url"], content=entry["body"].encode(), timeout=5.0,
                           headers={**headers(self.secret, entry["id"], entry["body"]), "content-type": "application/json"})
            entry["delivery"]["status"] = r.status_code
        except Exception as exc:
            entry["delivery"]["status"] = f"error: {type(exc).__name__}"
        try:
            self.report(entry["id"], entry["delivery"]["status"])
        except Exception:
            pass
