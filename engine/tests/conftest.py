import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from wismo.events import Event
from wismo.store import local
from wismo.store.postgres import PostgresEventStore

# The suite hammers one app from one address; tests/test_waf.py builds apps with their own limits.
os.environ.setdefault("WAF_RATE_LIMITS", "off")

IST = timezone(timedelta(hours=5, minutes=30))
TENANT_A = "tenant-a"
TENANT_B = "tenant-b"


@pytest.fixture(scope="session")
def admin_uri(tmp_path_factory):
    uri = local.start(tmp_path_factory.mktemp("pgdata"))
    local.migrate(uri)
    local.ensure_tenant(uri, TENANT_A, "Tenant A", "parcel")
    local.ensure_tenant(uri, TENANT_B, "Tenant B", "quick")
    return uri


@pytest.fixture
def store(admin_uri):
    s = PostgresEventStore.connect(admin_uri)
    yield s
    s.close()


@pytest.fixture
def order_ref():
    # The log is append-only, so each test writes to its own order instead of cleaning up.
    return f"ORD-{uuid.uuid4().hex[:10]}"


def make_event(order_ref, *, tenant=TENANT_A, event_id=None, minutes=0, **fields) -> Event:
    base = {
        "event_id": event_id or f"evt-{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant,
        "order_ref": order_ref,
        "type": "shipment.status",
        "status": "in_transit",
        "substatus": "in_transit.hub_scan",
        "occurred_at": datetime(2025, 12, 22, 10, 0, tzinfo=IST) + timedelta(minutes=minutes),
        "asserted_by": "carrier",
        "source_adapter": "test",
    }
    base.update(fields)
    return Event.model_validate(base)
