"""Reddit. robots.txt disallows all crawling for every user agent and the JSON endpoints
now redirect anonymous clients to a login page; the API needs OAuth. We check robots.txt
and stop there - recorded as a skip."""
from __future__ import annotations

from urllib.parse import quote_plus

from ..http import Blocked, Polite


def collect(brand: dict, cfg: dict, http: Polite) -> tuple[list[dict], str]:
    url = f"https://www.reddit.com/search.json?q={quote_plus(cfg['query'])}&sort=new"
    ok, why = http.robots_allows(url)
    if not ok:
        raise Blocked(f"{why} (Disallow: / for all agents); API requires OAuth login")
    http.get(url)
    raise Blocked("search endpoint served but not parsed: Reddit's content policy requires API access")
