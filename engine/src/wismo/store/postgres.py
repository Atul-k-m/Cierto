"""Postgres EventStore with row-level security per tenant."""
import psycopg
from psycopg.types.json import Jsonb

from ..events import Event, StoredEvent
from .base import AppendResult, IdempotencyConflict


class PostgresEventStore:
    """Connects as the non-owner ``wismo_app`` role so row-level security applies."""

    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    @classmethod
    def connect(cls, uri: str) -> "PostgresEventStore":
        conn = psycopg.connect(uri, autocommit=True)
        conn.execute("SET ROLE wismo_app")
        return cls(conn)

    def close(self) -> None:
        self._conn.close()

    def _as_tenant(self, tenant_id: str) -> None:
        # Transaction-local, so a pooled connection never carries one tenant into another request.
        self._conn.execute("SELECT set_config('app.tenant_id', %s, true)", (tenant_id,))

    def append(self, event: Event) -> AppendResult:
        payload_hash = event.payload_hash()
        with self._conn.transaction():
            self._as_tenant(event.tenant_id)
            row = self._conn.execute(
                """
                INSERT INTO event (tenant_id, event_id, order_ref, shipment_ref, type, status, substatus,
                                   occurred_at, asserted_by, source_adapter, body, payload_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, event_id) DO NOTHING
                RETURNING seq
                """,
                (
                    event.tenant_id, event.event_id, event.order_ref, event.shipment_ref,
                    event.type.value, event.status.value if event.status else None, event.substatus,
                    event.occurred_at, event.asserted_by.value, event.source_adapter,
                    Jsonb(event.model_dump(mode="json")), payload_hash,
                ),
            ).fetchone()
            if row is not None:
                return AppendResult.INSERTED
            (existing_hash,) = self._conn.execute(
                "SELECT payload_hash FROM event WHERE tenant_id = %s AND event_id = %s",
                (event.tenant_id, event.event_id),
            ).fetchone()
        if existing_hash != payload_hash:
            raise IdempotencyConflict(f"event_id {event.event_id!r} reused with different content")
        return AppendResult.DUPLICATE

    def events_for_order(self, tenant_id: str, order_ref: str) -> list[StoredEvent]:
        with self._conn.transaction():
            self._as_tenant(tenant_id)
            rows = self._conn.execute(
                """
                SELECT seq, received_at, body FROM event
                WHERE tenant_id = %s AND order_ref = %s
                ORDER BY occurred_at, received_at, seq
                """,
                (tenant_id, order_ref),
            ).fetchall()
        return [StoredEvent(seq=seq, received_at=received_at, event=Event.model_validate(body))
                for seq, received_at, body in rows]
