"""consumercomplaints.in brand listing pages, plus the complaint page for any excerpt the
listing truncates. robots.txt allows these paths; we fetch slowly with an honest UA.

A brand listing interleaves two newest-first lists: full complaints (own page, linked
title) and short complaints posted straight onto the brand page (no page of their own,
text given in full). Rows older than `min_date` are dropped; paging stops after two
consecutive pages with nothing in the window, or at `max_pages`.
"""
from __future__ import annotations

import html as htmllib
import re
from datetime import datetime

from ..http import Polite
from ..store import make_row

BASE = "https://www.consumercomplaints.in"
BOX = re.compile(r'<div id="c(\d+)" class="complaint-box">(.*?)(?=<div id="c\d+" class="complaint-box">|$)', re.S)
DATE = re.compile(r'author-box__date">([^<]+)<')
TITLE_LINK = re.compile(r'<a href="([^"]+)"\s+id="cmcc\d+"\s+class="complaint-box__link"\s*>(.*?)</a>', re.S)
TITLE_SPAN = re.compile(r'<span class="like-a" id="cmcc\d+">(?:<meta[^>]*>)?(.*?)</span>', re.S)
TEXT = re.compile(r'complaint-box__more-txt"><div[^>]*>(.*?)</div>', re.S)
BODY = re.compile(r'itemprop="reviewBody">(.*?)</div>', re.S)


def _clean(s: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = htmllib.unescape(s)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", s)).strip()


def _date(s: str) -> str | None:
    try:
        return datetime.strptime(s.strip(), "%b %d, %Y").date().isoformat()
    except ValueError:
        return None


def collect(brand: dict, cfg: dict, http: Polite) -> tuple[list[dict], str]:
    slug, max_pages = cfg["slug"], int(cfg.get("max_pages", 12))
    min_date = str(cfg.get("min_date", "2000-01-01"))
    fetch_details = cfg.get("fetch_details", True)
    rows, seen, pages, details, empty_streak, dropped_old = [], set(), 0, 0, 0, 0
    for page in range(1, max_pages + 1):
        page_url = f"{BASE}/{slug}" + (f"/page/{page}" if page > 1 else "")
        h = http.get(page_url).text
        pages += 1
        boxes = BOX.findall(h)
        if not boxes:
            break
        in_window = 0
        for cid, box in boxes:
            if cid in seen:
                continue
            seen.add(cid)
            d = DATE.search(box)
            date = _date(d.group(1)) if d else None
            if not date or date < min_date:
                dropped_old += 1
                continue
            in_window += 1
            link, span, x = TITLE_LINK.search(box), TITLE_SPAN.search(box), TEXT.search(box)
            if link:
                href, title, own_page = link.group(1), _clean(link.group(2)), True
            else:
                href, title, own_page = None, _clean(span.group(1)) if span else "", False
            url = BASE + href if href else f"{page_url}#cl{cid}"
            rows.append(dict(cid=cid, date=date, title=title, body=_clean(x.group(1)) if x else "",
                             url=url, own_page=own_page, page=page))
        empty_streak = 0 if in_window else empty_streak + 1
        if empty_streak >= 2:
            break
    # Listing excerpts of full complaints are cut at ~450 chars; fetch those pages.
    for r in rows:
        if fetch_details and r["own_page"] and len(r["body"]) >= 380:
            try:
                m = BODY.search(http.get(r["url"]).text)
                if m:
                    r["body"], r["full"] = _clean(m.group(1)), True
                    details += 1
            except Exception:
                pass
    out = [make_row(id=f"cc:{r['cid']}", brand=brand["key"], source="consumercomplaints",
                    date=r["date"], rating=None,
                    text=f"{r['title']}. {r['body']}" if r["title"] else r["body"],
                    url=r["url"], lang=None, title=r["title"],
                    truncated=r["own_page"] and len(r["body"]) >= 380 and not r.get("full"),
                    short_form=not r["own_page"], pull=["newest"])
           for r in rows if (r["title"] or r["body"])]
    return out, (f"slug={slug}, listing pages={pages}, detail pages={details}, "
                 f"min_date={min_date}, older rows dropped={dropped_old}")
