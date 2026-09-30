"""The web build contract (web.py): prerendered routes, canonical URLs, a real 404, __SITE_URL__, compression, caching."""
import gzip
import warnings

import pytest

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fastapi.testclient import TestClient

from wismo.api import create_app
from wismo.shared import MemoryBackend

HTML = "<!doctype html><html><head><link rel=canonical href=\"__SITE_URL__{path}\"></head><body>{body}</body></html>"


@pytest.fixture()
def dist(tmp_path):
    files = {
        "index.html": HTML.format(path="/", body="home " * 100),
        "demos/index.html": HTML.format(path="/demos", body="demos"),
        "case-studies/smytten/index.html": HTML.format(path="/case-studies/smytten", body="smytten"),
        "docs/quickstart/index.html": HTML.format(path="/docs/quickstart", body="quickstart"),
        "docs/quickstart.md": "# Quickstart\n\nSee __SITE_URL__/docs/quickstart\n",
        "404.html": HTML.format(path="/404", body="not found page"),
        "robots.txt": "User-agent: *\nAllow: /\nSitemap: __SITE_URL__/sitemap.xml\n",
        "sitemap.xml": "<?xml version=\"1.0\"?><urlset><url><loc>__SITE_URL__/demos</loc></url></urlset>",
        "llms.txt": "# Cierto\n> __SITE_URL__\n",
        "site.webmanifest": '{"name":"Cierto","start_url":"__SITE_URL__/"}',
        "hosts/smytten.html": "<!doctype html><title>host</title>",
        "favicon.svg": "<svg xmlns=\"http://www.w3.org/2000/svg\"/>",
    }
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    js = b"console.log('cierto');" * 200
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app-abc123.js").write_bytes(js)
    (tmp_path / "assets" / "app-abc123.js.gz").write_bytes(gzip.compress(js))
    (tmp_path / "assets" / "app-abc123.js.br").write_bytes(b"BROTLI-BYTES")
    (tmp_path / "assets" / "plain-def456.css").write_bytes(b"body{color:red}" * 100)
    for rel in ("site/photo/courier.jpg", "og/home.png", "apple-touch-icon.png"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(b"\x89PNG fake image bytes")
    return tmp_path


@pytest.fixture()
def client(dist, monkeypatch):
    monkeypatch.delenv("SITE_URL", raising=False)
    return TestClient(create_app(MemoryBackend(), web_dist=dist), base_url="http://cierto.test")


def test_routes_are_served_without_a_trailing_slash(client):
    home = client.get("/")
    assert home.status_code == 200 and "home" in home.text
    for path, word in (("/demos", "demos"), ("/case-studies/smytten", "smytten"), ("/docs/quickstart", "quickstart")):
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 200 and word in r.text and r.headers["content-type"] == "text/html; charset=utf-8"
    for path, target in (("/demos/", "/demos?x=1&y=2"), ("/docs/quickstart/", "/docs/quickstart?x=1&y=2"),
                         ("/demos/index.html", "/demos?x=1&y=2"), ("/index.html", "/?x=1&y=2")):
        r = client.get(path + "?x=1&y=2", follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == target, path


def test_unknown_paths_are_real_404s_and_api_paths_stay_json(client):
    for path in ("/nope", "/demos/nope", "/assets/missing.js", "/nope/", "/../engine/.env"):
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 404, path
    assert "not found page" in client.get("/nope").text
    for path in ("/v1/not-a-route", "/sdk/not-built.js"):
        r = client.get(path)
        assert r.status_code == 404 and r.headers["content-type"].startswith("application/json")
    assert client.post("/v1/nope").status_code == 404


def test_site_url_is_the_request_origin_or_the_env(client, dist, monkeypatch):
    assert "Sitemap: http://cierto.test/sitemap.xml" in client.get("/robots.txt").text
    behind_proxy = client.get("/robots.txt", headers={"x-forwarded-host": "cierto.dev"})
    assert "http://cierto.dev/sitemap.xml" in behind_proxy.text        # TRUSTED_PROXY_HOPS=1 (default): trusted
    assert 'href="http://cierto.test/demos"' in client.get("/demos").text
    monkeypatch.setenv("SITE_URL", "https://cierto.example/")
    fixed = TestClient(create_app(MemoryBackend(), web_dist=dist))
    for path, needle in (("/robots.txt", "https://cierto.example/sitemap.xml"),
                         ("/sitemap.xml", "<loc>https://cierto.example/demos</loc>"),
                         ("/llms.txt", "> https://cierto.example"), ("/docs/quickstart.md", "https://cierto.example/docs"),
                         ("/site.webmanifest", '"start_url":"https://cierto.example/"')):
        r = fixed.get(path)
        assert needle in r.text and "__SITE_URL__" not in r.text, path


def test_content_types(client):
    types = {"/docs/quickstart.md": "text/markdown; charset=utf-8", "/site.webmanifest": "application/manifest+json",
             "/robots.txt": "text/plain; charset=utf-8", "/sitemap.xml": "application/xml; charset=utf-8",
             "/favicon.svg": "image/svg+xml", "/assets/app-abc123.js": "text/javascript; charset=utf-8",
             "/hosts/smytten.html": "text/html; charset=utf-8"}
    for path, ctype in types.items():
        assert client.get(path).headers["content-type"] == ctype, path


def test_cache_control_and_etags(client):
    cc = {"/assets/app-abc123.js": "public, max-age=31536000, immutable", "/": "no-cache", "/demos": "no-cache",
          "/robots.txt": "no-cache", "/docs/quickstart.md": "no-cache", "/site/photo/courier.jpg": "public, max-age=604800",
          "/og/home.png": "public, max-age=604800", "/apple-touch-icon.png": "public, max-age=604800"}
    for path, value in cc.items():
        assert client.get(path).headers["cache-control"] == value, path
    first = client.get("/demos")
    again = client.get("/demos", headers={"if-none-match": first.headers["etag"]})
    assert again.status_code == 304 and again.content == b""
    weak = client.get("/site/photo/courier.jpg")
    assert client.get("/site/photo/courier.jpg", headers={"if-none-match": "W/" + weak.headers["etag"]}).status_code == 304


def test_precompressed_assets_and_gzip_on_the_fly(client):
    br = client.get("/assets/app-abc123.js", headers={"accept-encoding": "br, gzip"})
    assert br.headers["content-encoding"] == "br" and br.headers["vary"] == "Accept-Encoding"
    assert br.content == b"BROTLI-BYTES"                                   # the build's .br, as is
    gz = client.get("/assets/app-abc123.js", headers={"accept-encoding": "gzip"})
    assert gz.headers["content-encoding"] == "gzip" and gz.content.startswith(b"console.log")
    plain = client.get("/assets/app-abc123.js", headers={"accept-encoding": "identity"})
    assert "content-encoding" not in plain.headers and plain.content.startswith(b"console.log")
    css = client.get("/assets/plain-def456.css", headers={"accept-encoding": "gzip"})
    assert css.headers["content-encoding"] == "gzip"                       # no sibling: gzipped here
    html = client.get("/", headers={"accept-encoding": "gzip"})
    assert html.headers["content-encoding"] == "gzip" and "home" in html.text
    assert client.get("/", headers={"accept-encoding": "gzip"}).headers["etag"] != \
        client.get("/", headers={"accept-encoding": "identity"}).headers["etag"]   # one ETag per representation
    photo = client.get("/site/photo/courier.jpg", headers={"accept-encoding": "gzip"})
    assert "content-encoding" not in photo.headers


def test_web_routes_are_get_and_head_only(client):
    head = client.head("/demos")
    assert head.status_code == 200 and head.content == b"" and int(head.headers["content-length"]) > 0
    for method in ("post", "put"):
        r = getattr(client, method)("/demos")
        assert r.status_code == 405 and r.headers["allow"] == "GET, HEAD"


def test_old_spa_build_without_404_page_still_answers_404(dist, monkeypatch):
    (dist / "404.html").unlink()
    c = TestClient(create_app(MemoryBackend(), web_dist=dist))
    r = c.get("/some/client/route")
    assert r.status_code == 404 and "home" in r.text                       # the SPA shell, honestly as a 404


def test_one_vary_header_and_gzip_for_api_json(client):
    for enc in ("identity", "gzip"):
        assert client.get("/demos", headers={"accept-encoding": enc}).headers.get_list("vary") == ["Accept-Encoding"]
    keys = client.get("/v1/dev/keys", headers={"accept-encoding": "gzip"})
    assert keys.headers["content-encoding"] == "gzip" and keys.json()["object"] == "list"   # API JSON over 1 KB
    assert "content-encoding" not in client.get("/healthz", headers={"accept-encoding": "gzip"}).headers
