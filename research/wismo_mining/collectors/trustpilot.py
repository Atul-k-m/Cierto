"""Trustpilot company review page. Parses the embedded __NEXT_DATA__ JSON when the page
is served; Trustpilot usually answers automated clients with HTTP 403, which we record
as a skip rather than work around."""
from __future__ import annotations

import json
import re

from ..http import Blocked, Polite
from ..store import make_row

NEXT = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)


def collect(brand: dict, cfg: dict, http: Polite) -> tuple[list[dict], str]:
    url = f"https://www.trustpilot.com/review/{cfg['domain']}"
    ok, _ = http.robots_allows(url)
    if not ok:
        raise Blocked("robots.txt: 'User-agent: * / Disallow: /' (only named search bots allowed); "
                      "pages also return HTTP 403 to non-browser clients")
    h = http.get(url).text
    m = NEXT.search(h)
    if not m:
        return [], f"{url}: page served but no review data found"
    data = json.loads(m.group(1))
    revs = (((data.get("props") or {}).get("pageProps") or {}).get("reviews")) or []
    rows = [make_row(id=f"tp:{r['id']}", brand=brand["key"], source="trustpilot",
                     date=(r.get("dates") or {}).get("publishedDate", "")[:10] or None,
                     rating=r.get("rating"), text=f"{r.get('title', '')}. {r.get('text', '')}",
                     url=f"https://www.trustpilot.com/reviews/{r['id']}", lang=r.get("language"),
                     pull=["page1"])
            for r in revs]
    return rows, f"{url}: first page only"
