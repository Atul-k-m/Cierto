"""State that every instance behind the load balancer must agree on: session op logs and counters.

Two backends with one contract. ``MemoryBackend`` (the default) is right for one instance: dev,
tests, Cloud Run with max-instances=1. ``RedisBackend`` (when ``REDIS_URL`` is set; redis:// or
rediss://, e.g. Upstash) is shared, so any instance can serve any request: no sticky sessions.

A log is a Redis hash whose fields are "1", "2", …: HSETNX on field n+1 is the compare-and-set
that orders concurrent writers without Lua or WATCH, so it runs on any Redis-compatible service.
Counters are fixed windows (SET NX EX + INCR). Everything expires; nothing needs a janitor.
"""
import os
import threading
import time
from collections import OrderedDict


class StoreUnavailable(RuntimeError):
    """The shared store did not answer (Redis down or unreachable)."""


class MemoryBackend:
    kind = "memory"

    def __init__(self, max_counters: int = 200_000):
        self._lock = threading.Lock()
        self._logs: OrderedDict[str, list] = OrderedDict()   # key -> [ops, expires_at, pool], least recently used first
        self._pools: dict[str, int] = {}                        # pool -> live-log cap
        self._kv: dict[str, tuple[object, float]] = {}
        self._max_counters = max_counters

    # ---- op logs ----

    def _live(self, key: str) -> list | None:
        entry = self._logs.get(key)
        if entry is not None and entry[1] < time.monotonic():
            del self._logs[key]
            return None
        return entry

    def log_create(self, key: str, op: str, ttl: int, pool: str | None = None, cap: int = 0) -> bool:
        with self._lock:
            if self._live(key) is not None:
                return False
            if pool and cap:
                self._evict(pool, cap - 1)
            self._logs[key] = [[op], time.monotonic() + ttl, pool]
            return True

    def _evict(self, pool: str, keep: int) -> None:
        mine = [k for k, e in self._logs.items() if e[2] == pool]
        now = time.monotonic()
        for k in [k for k in mine if self._logs[k][1] < now]:
            del self._logs[k]
        mine = [k for k in mine if k in self._logs]
        for k in mine[:max(0, len(mine) - keep)]:   # least recently used first
            del self._logs[k]

    def log_append(self, key: str, version: int, op: str, ttl: int) -> bool:
        with self._lock:
            entry = self._live(key)
            if entry is None or len(entry[0]) != version:
                return False
            entry[0].append(op)
            entry[1] = time.monotonic() + ttl
            self._logs.move_to_end(key)
            return True

    def log_read(self, key: str, start: int, ttl: int, pool: str | None = None) -> tuple[int, list[str]]:
        """(ops in the log, the ops after ``start``); refreshes the idle TTL. (0, []) if there is no such log."""
        with self._lock:
            entry = self._live(key)
            if entry is None:
                return 0, []
            entry[1] = time.monotonic() + ttl
            self._logs.move_to_end(key)
            return len(entry[0]), list(entry[0][start:])

    def log_drop(self, key: str) -> None:
        with self._lock:
            self._logs.pop(key, None)

    # ---- counters and small values ----

    def hit(self, keys: list[tuple[str, int]]) -> list[int]:
        """Increment each fixed-window counter (key, window seconds); return the new counts."""
        now, out = time.monotonic(), []
        with self._lock:
            if len(self._kv) > self._max_counters:
                self._kv = {k: v for k, v in self._kv.items() if v[1] > now}
                if len(self._kv) > self._max_counters:   # still flooded: forget everything (fail open) rather than grow
                    self._kv.clear()
            for key, ttl in keys:
                value, exp = self._kv.get(key, (0, 0.0))
                if exp < now:
                    value, exp = 0, now + ttl
                self._kv[key] = (int(value) + 1, exp)
                out.append(int(value) + 1)
        return out

    def claim(self, key: str, ttl: int) -> bool:
        with self._lock:
            value = self._kv.get(key)
            if value is not None and value[1] > time.monotonic():
                return False
            self._kv[key] = (1, time.monotonic() + ttl)
            return True

    def get(self, key: str) -> str | None:
        return self.get_many([key])[0]

    def get_many(self, keys: list[str]) -> list[str | None]:
        now = time.monotonic()
        with self._lock:
            return [str(v[0]) if (v := self._kv.get(k)) and v[1] > now else None for k in keys]

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        with self._lock:
            self._kv[key] = (value, time.monotonic() + (ttl or 10 * 365 * 86400))

    def ping(self) -> bool:
        return True


class RedisBackend:
    kind = "redis"
    TOUCH_EVERY = 60   # seconds between idle-TTL refreshes of one log from one instance (reads are polls)

    def __init__(self, url: str, prefix: str = "cierto:"):
        import redis   # optional dependency: pip install "wismo[redis]"

        self._errors = (redis.RedisError, OSError)
        self.r = redis.Redis.from_url(url, decode_responses=True, socket_timeout=3, socket_connect_timeout=3,
                                      health_check_interval=30, retry_on_timeout=True)
        self.prefix = prefix
        self._touched: dict[str, float] = {}

    def _k(self, key: str) -> str:
        return self.prefix + key

    def _do(self, fn):
        try:
            return fn()
        except self._errors as exc:
            raise StoreUnavailable(f"redis: {type(exc).__name__}") from None

    def log_create(self, key: str, op: str, ttl: int, pool: str | None = None, cap: int = 0) -> bool:
        def run():
            k, now = self._k("log:" + key), time.time()
            p = self.r.pipeline(transaction=False)
            p.hsetnx(k, "1", op)
            p.expire(k, ttl)
            if pool:
                zk = self._k("pool:" + pool)
                p.zadd(zk, {key: now})
                p.zremrangebyscore(zk, "-inf", now - ttl)
                p.zcard(zk)
            res = p.execute()
            if pool and cap and res[-1] > cap:   # over the cap: drop the least recently used logs
                victims = [m for m, _ in self.r.zpopmin(self._k("pool:" + pool), res[-1] - cap) if m != key]
                if victims:
                    self.r.delete(*[self._k("log:" + v) for v in victims])
            return bool(res[0])
        return self._do(run)

    def log_append(self, key: str, version: int, op: str, ttl: int) -> bool:
        def run():
            k = self._k("log:" + key)
            p = self.r.pipeline(transaction=False)
            p.hsetnx(k, str(version + 1), op)
            p.hlen(k)
            p.expire(k, ttl)
            won, length, _ = p.execute()
            if won and length != version + 1:   # the log had expired: our field is all there is; take it back
                self.r.hdel(k, str(version + 1))
                return False
            return bool(won)
        return self._do(run)

    def log_read(self, key: str, start: int, ttl: int, pool: str | None = None) -> tuple[int, list[str]]:
        """One HLEN when this instance is up to date (the common case: a poll); the missing ops only when there
        are some. The idle TTL is refreshed at most every TOUCH_EVERY seconds per log per instance."""
        def run():
            k = self._k("log:" + key)
            if self._due(key):
                p = self.r.pipeline(transaction=False)
                p.hlen(k)
                p.expire(k, ttl)
                if pool:
                    p.zadd(self._k("pool:" + pool), {key: time.time()}, xx=True)
                n = p.execute()[0]
            else:
                n = self.r.hlen(k)
            if not n or n <= start:
                return n, []
            ops = self.r.hmget(k, [str(i) for i in range(start + 1, n + 1)])
            if any(o is None for o in ops):   # expired or replaced between the two reads
                return 0, []
            return n, ops
        return self._do(run)

    def _due(self, key: str) -> bool:
        now = time.monotonic()
        if now - self._touched.get(key, 0.0) < self.TOUCH_EVERY:
            return False
        if len(self._touched) > 10_000:
            self._touched = {k: t for k, t in self._touched.items() if now - t < self.TOUCH_EVERY}
        self._touched[key] = now
        return True

    def log_drop(self, key: str) -> None:
        self._do(lambda: self.r.delete(self._k("log:" + key)))

    def hit(self, keys: list[tuple[str, int]]) -> list[int]:
        def run():
            p = self.r.pipeline(transaction=False)
            for key, ttl in keys:
                p.set(self._k(key), 0, ex=ttl, nx=True)
                p.incr(self._k(key))
            return [int(v) for v in p.execute()[1::2]]
        return self._do(run)

    def claim(self, key: str, ttl: int) -> bool:
        return bool(self._do(lambda: self.r.set(self._k(key), 1, ex=ttl, nx=True)))

    def get(self, key: str) -> str | None:
        return self._do(lambda: self.r.get(self._k(key)))

    def get_many(self, keys: list[str]) -> list[str | None]:
        return self._do(lambda: self.r.mget([self._k(k) for k in keys])) if keys else []

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self._do(lambda: self.r.set(self._k(key), value, ex=ttl))

    def ping(self) -> bool:
        try:
            return bool(self.r.ping())
        except self._errors:
            return False


def open_backend() -> MemoryBackend | RedisBackend:
    """Redis when REDIS_URL (or KV_URL, as Vercel's Upstash integration names it) is set, else memory (one instance only)."""
    url = (os.environ.get("REDIS_URL") or os.environ.get("KV_URL") or "").strip()
    if not url and os.environ.get("VERCEL"):
        import sys
        print("cierto: no REDIS_URL on Vercel; each function instance keeps its own sessions and counters", file=sys.stderr)
    return RedisBackend(url, os.environ.get("REDIS_PREFIX", "cierto:")) if url else MemoryBackend()
