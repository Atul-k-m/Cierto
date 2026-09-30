"""Vercel entrypoint (FastAPI preset): the same app `python -m wismo serve` runs.

Loaded from the source tree, not an installed package, so the demo scenarios and the web build resolve
relative to the repo exactly as they do locally. Deploying: docs/deploy.md, "Free: Vercel + Upstash".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "src"))

from wismo.api import app  # noqa: E402,F401
