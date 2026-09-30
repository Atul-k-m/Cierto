"""Google Play reviews via the `google-play-scraper` package.

Two kinds of pull, tagged in `pull` so the report can keep samples apart:
  newest      - newest reviews, all star ratings (used for "share of all reviews")
  low_<n>     - newest reviews filtered to n stars (deepens the 1-2 star window)
Pages of 200 are fetched one at a time with a pause between them.
"""
from __future__ import annotations

import time

from google_play_scraper import Sort, reviews

from ..store import make_row

PAGE = 200


def _pull(app_id: str, lang: str, country: str, limit: int, score: int | None, pause: float) -> list[dict]:
    out, token = [], None
    while len(out) < limit:
        batch, token = reviews(app_id, lang=lang, country=country, sort=Sort.NEWEST,
                               count=min(PAGE, limit - len(out)), filter_score_with=score,
                               continuation_token=token)
        out.extend(batch)
        if not batch or token is None or getattr(token, "token", None) is None:
            break
        time.sleep(pause)
    return out


def collect(brand: dict, cfg: dict, http=None) -> tuple[list[dict], str]:
    app_id, lang, country = cfg["app_id"], cfg.get("lang", "en"), cfg.get("country", "in")
    pause = brand["politeness"].get("api_sleep_s", 1.5)
    pulls = [("newest", None, int(cfg.get("newest", 5000)))]
    pulls += [(f"low_{s}", int(s), int(n)) for s, n in (cfg.get("low_star") or {}).items()]

    rows: dict[str, dict] = {}
    counts = {}
    for tag, score, limit in pulls:
        got = _pull(app_id, lang, country, limit, score, pause)
        counts[tag] = len(got)
        for r in got:
            rid = f"gp:{r['reviewId']}"
            if rid in rows:
                rows[rid]["pull"].append(tag)
                continue
            text = r.get("content") or ""
            rows[rid] = make_row(
                id=rid, brand=brand["key"], source="google_play",
                date=r["at"].date().isoformat() if r.get("at") else None,
                rating=r.get("score"), text=text,
                url=f"https://play.google.com/store/apps/details?id={app_id}&reviewId={r['reviewId']}",
                lang=None, requested_lang=lang, pull=[tag],
                thumbs_up=r.get("thumbsUpCount"), app_version=r.get("reviewCreatedVersion"),
                has_dev_reply=bool(r.get("replyContent")),
            )
        time.sleep(pause)
    detail = f"app_id={app_id}, lang={lang}, country={country}; pulls: " + \
             ", ".join(f"{k}={v}" for k, v in counts.items())
    return [r for r in rows.values() if r["text"]], detail
