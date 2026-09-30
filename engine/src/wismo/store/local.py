"""Local embedded Postgres (pgserver) for demos and tests: no Docker, no install (ADR-001)."""
import os
from importlib.resources import files
from pathlib import Path

import pgserver
import psycopg

DEFAULT_DATA_DIR = Path(os.environ.get("WISMO_PGDATA", Path(__file__).resolve().parents[3] / ".pgdata"))


def start(data_dir: Path = DEFAULT_DATA_DIR) -> str:
    """Start (or reuse) the embedded server and return a superuser URI."""
    server = pgserver.get_server(str(data_dir), cleanup_mode="stop")
    return server.get_uri()


def migrate(admin_uri: str) -> None:
    schema = files("wismo.store").joinpath("schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(admin_uri, autocommit=True) as conn:
        conn.execute(schema)


def ensure_tenant(admin_uri: str, tenant_id: str, name: str, vertical: str) -> None:
    """Tenants are provisioned by an operator, not by the app role."""
    with psycopg.connect(admin_uri, autocommit=True) as conn:
        conn.execute(
            "INSERT INTO tenant (id, name, vertical) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
            (tenant_id, name, vertical),
        )
