"""The built web app (apps/web/dist), served by the API process: one origin, one port.

The contract with the web build:
  /                       index.html
  /demos                  demos/index.html (any prerendered <route>/index.html), no redirect
  /demos/                 301 -> /demos (query kept); /demos/index.html and /index.html also 301 to the canonical URL
  /robots.txt, /docs/x.md files as they are (robots.txt, sitemap.xml, llms*.txt, markdown twins, site.webmanifest, …)
  anything else           404.html with status 404 (/v1/* and /sdk/* get a JSON 404). No soft-404 fallback.

Text files (html xml txt md webmanifest json) may contain ``__SITE_URL__``: it becomes SITE_URL, or the
request's external origin (scheme from X-Forwarded-Proto via uvicorn's proxy headers; host from
X-Forwarded-Host behind a trusted proxy, else Host). Rendered bodies are cached per (path, origin, encoding).

Compression: assets/* may ship .br/.gz siblings from the build (served with Content-Encoding and Vary);
other compressible files are gzipped here once and cached. Caching: hashed assets/* are immutable for a
year; html and the templated text files are no-cache with an ETag (304 on If-None-Match); photos, og
images and root icons a week. GET and HEAD only.
"""
import gzip
import hashlib
import json
import os
import re
import threading
from collections import OrderedDict
from pathlib import Path

TYPES = {
    ".html": "text/html; charset=utf-8", ".xml": "application/xml; charset=utf-8",
    ".txt": "text/plain; charset=utf-8", ".md": "text/markdown; charset=utf-8",
    ".webmanifest": "application/manifest+json", ".json": "application/json",
    ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".map": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".webp": "image/webp", ".avif": "image/avif", ".gif": "image/gif", ".ico": "image/x-icon",
    ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf", ".mp4": "video/mp4",
    ".webm": "video/webm", ".pdf": "application/pdf", ".wasm": "application/wasm",
}
TEMPLATED = {".html", ".xml", ".txt", ".md", ".webmanifest", ".json"}
COMPRESSIBLE = TEMPLATED | {".js", ".mjs", ".css", ".map", ".svg", ".ico"}
IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".ico", ".svg"}
TOKEN = b"__SITE_URL__"
MIN_GZIP = 256
_HOST = re.compile(r"^(\[[0-9a-fA-F:.]+\]|[A-Za-z0-9.-]{1,253})(:\d{1,5})?$")


def cache_control(rel: str, ext: str) -> str:
    if rel.startswith("assets/"):
        return "public, max-age=31536000, immutable"
    if ext in TEMPLATED:
        return "no-cache"
    if rel.startswith(("site/photo/", "og/")) or ("/" not in rel and ext in IMAGES):
        return "public, max-age=604800"
    return "public, max-age=3600"


def _codings(scope) -> set[str]:
    raw = next((v.decode("latin-1") for k, v in scope["headers"] if k == b"accept-encoding"), "")
    out = set()
    for part in raw.split(","):
        name, _, params = part.strip().partition(";")
        q = params.strip()
        if name and not (q.startswith("q=") and q[2:].strip() in ("0", "0.0", "0.00", "0.000")):
            out.add(name.strip().lower())
    return out


def _etag_matches(scope, etag: str) -> bool:
    raw = next((v.decode("latin-1") for k, v in scope["headers"] if k == b"if-none-match"), None)
    if raw is None:
        return False
    want = etag.removeprefix("W/")
    return any(t.strip() == "*" or t.strip().removeprefix("W/") == want for t in raw.split(","))


class WebDist:
    """ASGI app serving the web build under the contract above. Mount it last, at "/"."""

    def __init__(self, directory: Path, site_url: str | None = None, trust_forwarded_host: bool = False,
                 cache_bytes: int = 32 * 1024 * 1024):
        self.root = Path(directory)
        self.site_url = (site_url or "").rstrip("/") or None
        self.trust_forwarded_host = trust_forwarded_host
        self.cache_bytes = cache_bytes
        self._cache: OrderedDict[tuple, tuple[bytes, str]] = OrderedDict()
        self._size = 0
        self._lock = threading.Lock()

    # ---- resolving ----

    def _file(self, rel: str) -> Path | None:
        """dist/<rel> if it is a file, else dist/<rel>/index.html; never outside dist."""
        base = self.root / rel if rel else self.root
        for f in (base, base / "index.html") if rel else (base / "index.html",):
            if f.is_file():
                real = f.resolve()
                if real == self.root.resolve() or self.root.resolve() in real.parents:
                    return f
        return None

    def resolve(self, path: str) -> tuple[str, object]:
        """("file", Path) | ("redirect", "/canonical") | ("missing", None)."""
        if "\\" in path or "\x00" in path:
            return "missing", None
        parts = [p for p in path.split("/") if p]
        if any(p in (".", "..") or p.startswith("~") for p in parts):
            return "missing", None
        canonical = "/" + "/".join(parts)
        if parts and parts[-1] == "index.html":   # /index.html, /demos/index.html -> / and /demos
            target = "/" + "/".join(parts[:-1])
            return ("redirect", target) if self._file("/".join(parts)) else ("missing", None)
        if path != canonical:   # trailing (or doubled) slashes
            return ("redirect", canonical) if self._file("/".join(parts)) else ("missing", None)
        f = self._file("/".join(parts))
        return ("file", f) if f else ("missing", None)

    def origin(self, scope) -> str:
        if self.site_url:
            return self.site_url
        headers = {k: v.decode("latin-1") for k, v in scope["headers"] if k in (b"host", b"x-forwarded-host")}
        host = headers.get(b"host", "")
        if self.trust_forwarded_host and headers.get(b"x-forwarded-host"):
            host = headers[b"x-forwarded-host"].split(",")[-1].strip()
        if not _HOST.match(host or ""):
            host = "localhost"
        return f"{scope.get('scheme', 'http')}://{host}"

    # ---- rendering (cached) ----

    def _cached(self, key: tuple, make) -> tuple[bytes, str]:
        with self._lock:
            hit = self._cache.get(key)
            if hit is not None:
                self._cache.move_to_end(key)
                return hit
        body = make()
        value = (body, hashlib.sha256(body).hexdigest()[:20])
        with self._lock:
            if key not in self._cache:
                self._cache[key] = value
                self._size += len(body)
                while self._size > self.cache_bytes and len(self._cache) > 1:
                    _, (old, _) = self._cache.popitem(last=False)
                    self._size -= len(old)
        return value

    def _text(self, f: Path, st, origin_of) -> tuple[bytes, str | None]:
        """The file's bytes with __SITE_URL__ replaced, and the origin used (None if it has no token)."""
        raw, _ = self._cached(("raw", str(f), st.st_mtime_ns, st.st_size), f.read_bytes)
        if TOKEN not in raw:
            return raw, None
        origin = origin_of()
        body, _ = self._cached(("tpl", str(f), st.st_mtime_ns, st.st_size, origin),
                               lambda: raw.replace(TOKEN, origin.encode()))
        return body, origin

    # ---- ASGI ----

    async def __call__(self, scope, receive, send):
        path, method = scope["path"], scope["method"]
        if path in ("/v1", "/sdk") or path.startswith(("/v1/", "/sdk/")):
            return await _send(send, 404, [(b"content-type", b"application/json")], b'{"detail":"Not Found"}', method)
        if method not in ("GET", "HEAD"):
            body = json.dumps({"detail": "Method Not Allowed"}).encode()
            return await _send(send, 405, [(b"content-type", b"application/json"), (b"allow", b"GET, HEAD")],
                               body, method)
        kind, target = self.resolve(path)
        if kind == "redirect":
            query = scope.get("query_string", b"")
            location = target.encode() + (b"?" + query if query else b"")
            return await _send(send, 301, [(b"location", location), (b"cache-control", b"public, max-age=3600"),
                                           (b"content-type", b"text/plain; charset=utf-8")], b"", method)
        if kind == "missing":
            # A real 404 page; a build without 404.html (the old SPA layout) gets its index.html, still as a 404.
            page = next((f for f in (self.root / "404.html", self.root / "index.html") if f.is_file()), None)
            if page is None:
                return await _send(send, 404, [(b"content-type", b"text/plain; charset=utf-8")], b"Not Found", method)
            return await self._serve(scope, send, page, 404)
        return await self._serve(scope, send, target, 200)

    async def _serve(self, scope, send, f: Path, status: int):
        method, st = scope["method"], f.stat()
        rel = f.relative_to(self.root).as_posix()
        ext = f.suffix.lower()
        cc = cache_control(rel, ext) if status == 200 else "no-cache"
        headers = [(b"content-type", TYPES.get(ext, "application/octet-stream").encode()), (b"cache-control", cc.encode())]
        if cc.startswith("public"):   # a CDN in front (Vercel's edge) may keep it too; plain proxies ignore this header
            headers.append((b"cdn-cache-control", cc.encode()))
        if ext in COMPRESSIBLE:
            headers.append((b"vary", b"Accept-Encoding"))
        accept, source, length = _codings(scope), f, None
        if ext in TEMPLATED:
            text, origin = self._text(f, st, lambda: self.origin(scope))
            enc = "gzip" if "gzip" in accept and len(text) >= MIN_GZIP else None
            body, digest = self._cached(("enc", str(f), st.st_mtime_ns, st.st_size, origin, enc),
                                        lambda: gzip.compress(text, 6, mtime=0) if enc else text)
            etag = f'"{digest}{"-" + enc if enc else ""}"'
        else:
            enc = None
            if rel.startswith("assets/") and ext in COMPRESSIBLE:   # the build's precompressed siblings
                for coding, suffix in (("br", ".br"), ("gzip", ".gz")):
                    sibling = f.with_name(f.name + suffix)
                    if coding in accept and sibling.is_file():
                        enc, source = coding, sibling
                        break
            if enc is None and ext in COMPRESSIBLE and "gzip" in accept and st.st_size >= MIN_GZIP:
                enc = "gzip"
                body, digest = self._cached(("gz", str(f), st.st_mtime_ns, st.st_size),
                                            lambda: gzip.compress(f.read_bytes(), 6, mtime=0))
                etag = f'"{digest}-gzip"'
            else:
                sst = source.stat()
                body, length = None, sst.st_size   # read below, unless it's a 304 or a HEAD
                etag = f'"{sst.st_mtime_ns:x}-{sst.st_size:x}{"-" + enc if enc else ""}"'
        headers += [(b"etag", etag.encode())] + ([(b"content-encoding", enc.encode())] if enc else [])
        if status == 200 and _etag_matches(scope, etag):
            return await _send(send, 304, [h for h in headers if h[0] != b"content-type"], b"", method)
        if body is None:
            body = source.read_bytes() if method == "GET" else b""
        return await _send(send, status, headers, body, method, length)


async def _send(send, status: int, headers: list, body: bytes, method: str, length: int | None = None):
    if status != 304:
        headers = [*headers, (b"content-length", str(len(body) if length is None else length).encode())]
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": b"" if method == "HEAD" or status == 304 else body})


def from_env(default: Path, directory: Path | None = None) -> WebDist:
    """WEB_DIST (or the older WISMO_WEB_DIST) overrides where the build is, unless ``directory`` is given;
    SITE_URL fixes the origin (on Vercel it defaults to the production domain); X-Forwarded-Host counts only
    behind a trusted proxy (TRUSTED_PROXY_HOPS > 0)."""
    directory = Path(directory or os.environ.get("WEB_DIST") or os.environ.get("WISMO_WEB_DIST") or default)
    hops = os.environ.get("TRUSTED_PROXY_HOPS", "1")
    site = os.environ.get("SITE_URL") or (f"https://{os.environ['VERCEL_PROJECT_PRODUCTION_URL']}"
                                          if os.environ.get("VERCEL_PROJECT_PRODUCTION_URL") else None)
    return WebDist(directory, site, trust_forwarded_host=hops.strip() not in ("", "0"))
