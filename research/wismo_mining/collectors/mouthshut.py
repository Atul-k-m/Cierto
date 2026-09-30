"""MouthShut. Its robots.txt disallows ClaudeBot site-wide and signals ai-train=no, and it
answers automated clients with HTTP 403. This framework is run by an AI agent, so we
honour the ClaudeBot rule: read robots.txt, and stop if that rule is present. Otherwise
try the listing page once; anything but a clean 200 is recorded as a skip."""
from __future__ import annotations

import re

from ..http import Blocked, Polite


def collect(brand: dict, cfg: dict, http: Polite) -> tuple[list[dict], str]:
    robots = http.get("https://www.mouthshut.com/robots.txt", check_robots=False).text
    if re.search(r"User-agent:\s*ClaudeBot\s*\n\s*Disallow:\s*/\s*$", robots, re.I | re.M):
        raise Blocked("robots.txt disallows ClaudeBot site-wide (and Content-Signal ai-train=no); not fetched")
    http.get(cfg["url"])  # raises Blocked on 403
    raise Blocked("listing served, but no parser is maintained for this site")
