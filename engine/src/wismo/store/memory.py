"""In-memory EventStore: same contract as Postgres, for the replay harness and fast tests.

It does not enforce tenant isolation at the database level; that guarantee is tested
against the Postgres adapter.
"""
from collections import defaultdict
from datetime import datetime, timezone

from ..events import Event, StoredEvent
from .base import AppendResult, IdempotencyConflict


class MemoryEventStore:
    def __init__(self, received_at=None):
        self._by_order: dict[tuple[str, str], list[StoredEvent]] = defaultdict(list)
        self._hashes: dict[tuple[str, str], str] = {}
        self._seq = 0
        self._received_at = received_at or (lambda: datetime.now(timezone.utc))

    def append(self, event: Event) -> AppendResult:
        key = (event.tenant_id, event.event_id)
        digest = event.payload_hash()
        if key in self._hashes:
            if self._hashes[key] != digest:
                raise IdempotencyConflict(f"event_id {event.event_id!r} reused with different content")
            return AppendResult.DUPLICATE
        self._hashes[key] = digest
        self._seq += 1
        self._by_order[(event.tenant_id, event.order_ref)].append(
            StoredEvent(seq=self._seq, received_at=self._received_at(), event=event))
        return AppendResult.INSERTED

    def events_for_order(self, tenant_id: str, order_ref: str) -> list[StoredEvent]:
        return sorted(self._by_order[(tenant_id, order_ref)],
                      key=lambda s: (s.event.occurred_at, s.received_at, s.seq))
