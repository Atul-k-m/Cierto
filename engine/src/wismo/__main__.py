"""CLI.

  python -m wismo replay <scenario.json> [--days N] [--postgres]   run a scenario through the engine and print the timeline
  python -m wismo serve [--host H] [--port N] [--build | --no-build]
                                                      API, SDK bundle and web app on one port (--build rebuilds both;
                                                      --no-build never builds: production)
  python -m wismo coverage                            replay the complaint corpus and write the coverage report
"""
import argparse
from datetime import timedelta
from pathlib import Path

from .scenario import Scenario, describe, format_timeline


def _replay(args) -> None:
    import uuid

    from .runner import run_scenario
    from .store import local
    from .store.memory import MemoryEventStore
    from .store.postgres import PostgresEventStore

    scenario = Scenario.load(args.scenario)
    if args.postgres:
        # A run-unique order ref: the log is append-only, so each demo run gets its own order.
        scenario = scenario.model_copy(update={"order_ref": f"{scenario.order_ref}-{uuid.uuid4().hex[:6]}"})
        admin_uri = local.start(args.pgdata or local.DEFAULT_DATA_DIR)
        local.migrate(admin_uri)
        local.ensure_tenant(admin_uri, scenario.tenant.id, scenario.tenant.name, scenario.tenant.vertical)
        store = PostgresEventStore.connect(admin_uri)
    else:
        store = MemoryEventStore()
    try:
        last = scenario.arrivals()[-1][0]
        run = run_scenario(scenario, store, until=last + timedelta(days=args.days))
        stored = store.events_for_order(scenario.tenant.id, scenario.order_ref)
        projection = run.engine.projection(scenario.tenant.id, scenario.order_ref)
    finally:
        if args.postgres:
            store.close()

    print(f"{scenario.id}: {scenario.title}")
    print(f"complaints: {', '.join(scenario.complaints)}  ·  {scenario.note}\n")
    print(format_timeline(
        [s.event.occurred_at for s in stored],
        [(s.event.asserted_by.value,
          f"▲ {s.event.data['rule']}: {s.event.data['message']}" if s.event.type.value == "engine.finding"
          else describe(s.event)) for s in stored],
    ))
    print(f"\nnow: {run.engine.clock.now():%a %d %b %H:%M}  ·  state: {projection.reconciled_state}"
          f"  ·  proof: {projection.proof_state.value}" + (f" ({projection.verified_by})" if projection.verified_by else ""))


def _load_env() -> None:
    """Read engine/.env (KEY=value lines) into the environment, without overriding what is already set."""
    import os

    env = Path(__file__).resolve().parents[2] / ".env"
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def _serve(args) -> None:
    """Uvicorn behind a load balancer: proxy headers from FORWARDED_ALLOW_IPS (only when TRUSTED_PROXY_HOPS > 0,
    so a direct client can't spoof its scheme or address), a graceful drain on SIGTERM, JSON logs if asked."""
    import json
    import os
    import subprocess

    import uvicorn

    from .waf import log_config

    _load_env()
    root = Path(__file__).resolve().parents[3]
    # The browser SDK first (served at /sdk/cierto.js), then the web app that may embed it.
    for app in (root / "packages" / "cierto-js", root / "apps" / "web"):
        if not args.no_build and (args.build or not (app / "dist").is_dir()):
            if not (app / "node_modules").is_dir():
                subprocess.run("npm install --no-audit --no-fund", cwd=app, shell=True, check=True)
            subprocess.run("npm run build", cwd=app, shell=True, check=True)
    port = args.port or int(os.environ.get("PORT") or 8787)
    hops = int(os.environ.get("TRUSTED_PROXY_HOPS", "1") or 0)
    logging_config = log_config(os.environ.get("LOG_FORMAT"))
    host = "localhost" if args.host in ("127.0.0.1", "0.0.0.0") else args.host
    banner = f"Cierto on http://{host}:{port}  ·  SDK at /sdk/cierto.js  ·  dev keys at /v1/dev/keys"
    print(json.dumps({"severity": "INFO", "message": banner}) if os.environ.get("LOG_FORMAT") == "json" else banner,
          flush=True)
    uvicorn.run(
        "wismo.api:app", host=args.host, port=port,
        proxy_headers=hops > 0, forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS") or "127.0.0.1",
        timeout_graceful_shutdown=int(os.environ.get("GRACEFUL_SHUTDOWN_SECONDS", 8)),
        timeout_keep_alive=int(os.environ.get("KEEP_ALIVE_SECONDS", 75)),   # longer than the proxy's idle timeout
        server_header=False, access_log=False,
        log_config=logging_config or uvicorn.config.LOGGING_CONFIG, log_level=None if logging_config else "warning",
    )


def _coverage(args) -> None:
    from .coverage.harness import main as coverage_main
    coverage_main(args.complaints, args.out_md, args.out_json)


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(prog="wismo")
    sub = parser.add_subparsers(dest="command", required=True)
    rp = sub.add_parser("replay", help="run a scenario through the engine and print its timeline")
    rp.add_argument("scenario", type=Path)
    rp.add_argument("--days", type=float, default=3, help="keep the clock running this many days after the last event")
    rp.add_argument("--postgres", action="store_true", help="write to the local Postgres log instead of memory")
    rp.add_argument("--pgdata", type=Path, default=None, help="local Postgres data directory (default: engine/.pgdata)")
    rp.set_defaults(fn=_replay)
    sv = sub.add_parser("serve", help="serve the API and the built web app on one port")
    sv.add_argument("--host", default="127.0.0.1", help="interface to bind (the container uses 0.0.0.0)")
    sv.add_argument("--port", type=int, default=None, help="port (default: $PORT, else 8787)")
    builds = sv.add_mutually_exclusive_group()
    builds.add_argument("--build", action="store_true", help="rebuild the browser SDK and the web app first")
    builds.add_argument("--no-build", action="store_true", help="never build (production: the image has the builds)")
    sv.set_defaults(fn=_serve)
    cv = sub.add_parser("coverage", help="replay the complaint corpus and write the coverage report")
    cv.add_argument("--complaints", type=Path, default=root / "data" / "complaints.json")
    cv.add_argument("--out-md", type=Path, default=root / "docs" / "reports" / "phase1-coverage.md")
    cv.add_argument("--out-json", type=Path, default=root / "data" / "coverage.json")
    cv.set_defaults(fn=_coverage)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
