"""A polite HTTP client: honest user agent, fixed delay between requests, robots.txt checks.

No login walls, no bot-protection bypasses: a 401/403/429 or a robots.txt disallow is
reported to the caller as a skip reason, never retried around.
"""
from __future__ import annotations

import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests


class Blocked(Exception):
    """The source refused us (robots.txt, 401/403/429, login wall). Record and move on."""


class Polite:
    def __init__(self, user_agent: str, sleep_s: float = 2.5, timeout: float = 30.0):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": user_agent, "Accept-Language": "en-IN,en;q=0.8"})
        self.ua = user_agent
        self.sleep_s = sleep_s
        self.timeout = timeout
        self._last = 0.0
        self._robots: dict[str, RobotFileParser | None] = {}
        self.requests_made = 0

    def _wait(self) -> None:
        dt = time.monotonic() - self._last
        if dt < self.sleep_s:
            time.sleep(self.sleep_s - dt)
        self._last = time.monotonic()

    def robots_allows(self, url: str) -> tuple[bool, str]:
        """Fetch robots.txt with *our* user agent (urllib's default UA gets 403s that
        RobotFileParser would misread as 'disallow all')."""
        u = urlparse(url)
        base = f"{u.scheme}://{u.netloc}"
        if base not in self._robots:
            self._wait()
            try:
                r = self.s.get(base + "/robots.txt", timeout=self.timeout)
                self.requests_made += 1
                if r.status_code >= 400:
                    self._robots[base] = None     # no readable robots.txt: treat as allowed
                else:
                    rp = RobotFileParser()
                    rp.parse(r.text.splitlines())
                    self._robots[base] = rp
            except requests.RequestException:
                self._robots[base] = None
        rp = self._robots[base]
        if rp is None:
            return True, "robots.txt unavailable"
        # Check both our UA and the generic '*' group; honour the stricter answer.
        ok = rp.can_fetch(self.ua, url) and rp.can_fetch("*", url)
        return ok, "robots.txt allows" if ok else "robots.txt disallows this path"

    def get(self, url: str, *, check_robots: bool = True, **kw) -> requests.Response:
        if check_robots:
            ok, why = self.robots_allows(url)
            if not ok:
                raise Blocked(why)
        self._wait()
        r = self.s.get(url, timeout=self.timeout, allow_redirects=True, **kw)
        self.requests_made += 1
        if r.status_code in (401, 403, 429):
            raise Blocked(f"HTTP {r.status_code} (bot protection or rate limit)")
        if any(k in r.url for k in ("/login", "/signin", "error.php")):
            raise Blocked(f"redirected to {r.url} (login wall / error page)")
        r.raise_for_status()
        return r
