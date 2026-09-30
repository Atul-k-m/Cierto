"""Apple App Store reviews from the public customer-reviews RSS JSON feed.

The feed returns at most 10 pages x 50 of the most recent reviews per storefront, so the
window for high-volume apps (Zomato) is only a few weeks. There is no per-review
permalink; rows link to the app's review listing and carry Apple's review id.
The feed is flaky (pages intermittently come back empty or 5xx), so each page is
retried a few times with a growing pause before we accept it as the end.
"""
from __future__ import annotations

import re
import time

from ..http import Blocked, Polite
from ..store import make_row

FEED = "https://itunes.apple.com/{cc}/rss/customerreviews/page={page}/id={app}/sortby=mostrecent/json"


def _page(http: Polite, url: str, tries: int = 4) -> tuple[list, int | None]:
    last_err = None
    for i in range(tries):
        try:
            j = http.get(url, check_robots=False).json()
            feed = j.get("feed") or {}
            entries = feed.get("entry") or []
            if isinstance(entries, dict):
                entries = [entries]
            last = None
            for l in feed.get("link") or []:
                a = l.get("attributes") or {}
                if a.get("rel") == "last":
                    m = re.search(r"page=(\d+)", a.get("href", ""))
                    last = int(m.group(1)) if m else None
            entries = [e for e in entries if "im:rating" in e]
            if entries:
                return entries, last
        except Blocked:
            raise
        except Exception as e:
            last_err = e
        time.sleep(3 * (i + 1))
    if last_err:
        raise last_err
    return [], None


def collect(brand: dict, cfg: dict, http: Polite) -> tuple[list[dict], str]:
    app, cc, pages = cfg["app_id"], cfg.get("country", "in"), int(cfg.get("pages", 10))
    http.sleep_s = brand["politeness"].get("api_sleep_s", 1.5)
    rows, fetched, empty, last_page = {}, 0, [], None
    for page in range(1, pages + 1):
        if last_page and page > last_page:
            break
        try:
            entries, last = _page(http, FEED.format(cc=cc, page=page, app=app))
        except Blocked:
            raise
        except Exception:
            if page == 1:
                raise
            empty.append(page)
            continue
        last_page = last_page or last
        if not entries:
            empty.append(page)
            continue
        fetched += 1
        for e in entries:
            rid = f"as:{e['id']['label']}"
            title = (e.get("title") or {}).get("label", "")
            body = (e.get("content") or {}).get("label", "")
            # The title often carries the complaint ("Order never came"); classify both.
            text = f"{title}. {body}" if title and body and title.strip() not in body else (body or title)
            rows[rid] = make_row(
                id=rid, brand=brand["key"], source="app_store",
                date=(e.get("updated") or {}).get("label", "")[:10] or None,
                rating=int(e["im:rating"]["label"]), text=text,
                url=f"https://apps.apple.com/{cc}/app/id{app}?see-all=reviews",
                lang=None, title=title, app_version=(e.get("im:version") or {}).get("label"),
                pull=["mostrecent"],
            )
    detail = f"app_id={app}, storefront={cc}, pages with data={fetched}, feed last page={last_page}"
    if empty:
        detail += f", empty/failed pages after retries={empty}"
    return list(rows.values()), detail
