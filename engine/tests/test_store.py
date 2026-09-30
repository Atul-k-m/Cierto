import psycopg
import pytest

from conftest import TENANT_A, TENANT_B, make_event
from wismo.store import AppendResult, IdempotencyConflict


def test_append_and_read_back(store, order_ref):
    event = make_event(order_ref, status="delivered", substatus="delivered.delivered", proof={"otp_verified": False})
    assert store.append(event) is AppendResult.INSERTED
    [stored] = store.events_for_order(TENANT_A, order_ref)
    assert stored.event == event


def test_timeline_follows_occurred_at_not_arrival(store, order_ref):
    later = make_event(order_ref, minutes=60, status="out_for_delivery", substatus="out_for_delivery.out_for_delivery")
    earlier = make_event(order_ref, minutes=0, status="in_transit", substatus="in_transit.at_destination_hub")
    store.append(later)     # arrives first
    store.append(earlier)   # a late carrier push
    assert [s.event.substatus for s in store.events_for_order(TENANT_A, order_ref)] == [
        "in_transit.at_destination_hub", "out_for_delivery.out_for_delivery",
    ]


def test_retry_is_a_no_op(store, order_ref):
    event = make_event(order_ref, event_id="retry-1")
    assert store.append(event) is AppendResult.INSERTED
    assert store.append(event) is AppendResult.DUPLICATE
    assert len(store.events_for_order(TENANT_A, order_ref)) == 1


def test_reused_event_id_with_new_content_is_rejected(store, order_ref):
    store.append(make_event(order_ref, event_id="reuse-1", minutes=0))
    with pytest.raises(IdempotencyConflict):
        store.append(make_event(order_ref, event_id="reuse-1", minutes=5))


def test_same_event_id_is_independent_per_tenant(store, order_ref):
    assert store.append(make_event(order_ref, tenant=TENANT_A, event_id="shared-1")) is AppendResult.INSERTED
    assert store.append(make_event(order_ref, tenant=TENANT_B, event_id="shared-1")) is AppendResult.INSERTED


def test_tenants_cannot_see_each_other(store, order_ref):
    store.append(make_event(order_ref, tenant=TENANT_A))
    assert store.events_for_order(TENANT_B, order_ref) == []
    assert len(store.events_for_order(TENANT_A, order_ref)) == 1


def test_cannot_write_into_another_tenant(admin_uri, order_ref):
    event = make_event(order_ref, tenant=TENANT_B)
    with psycopg.connect(admin_uri, autocommit=True) as conn:
        conn.execute("SET ROLE wismo_app")
        with pytest.raises(psycopg.errors.InsufficientPrivilege), conn.transaction():
            conn.execute("SELECT set_config('app.tenant_id', %s, true)", (TENANT_A,))
            conn.execute(
                "INSERT INTO event (tenant_id, event_id, order_ref, type, occurred_at, asserted_by,"
                " source_adapter, body, payload_hash) VALUES (%s, 'x', %s, 'order.placed', now(), 'merchant',"
                " 'test', '{}', 'h')",
                (event.tenant_id, order_ref),
            )


def test_no_tenant_context_sees_nothing(admin_uri, store, order_ref):
    store.append(make_event(order_ref))
    with psycopg.connect(admin_uri, autocommit=True) as conn:
        conn.execute("SET ROLE wismo_app")
        assert conn.execute("SELECT count(*) FROM event").fetchone() == (0,)


@pytest.mark.parametrize("statement", [
    "UPDATE event SET order_ref = 'tampered' WHERE order_ref = %(order_ref)s",
    "DELETE FROM event WHERE order_ref = %(order_ref)s",
    "TRUNCATE event",
])
def test_log_is_append_only_even_for_owner(admin_uri, store, order_ref, statement):
    store.append(make_event(order_ref))
    with psycopg.connect(admin_uri, autocommit=True) as conn:   # superuser: bypasses RLS, not the triggers
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            conn.execute(statement, {"order_ref": order_ref})
