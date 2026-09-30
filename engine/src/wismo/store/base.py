"""EventStore port (ADR-001: ports and adapters)."""
from enum import StrEnum
from typing import Protocol

from ..events import Event, StoredEvent


class AppendResult(StrEnum):
    INSERTED = "inserted"
    DUPLICATE = "duplicate"   # same event_id and same content: a retry, safely ignored


class IdempotencyConflict(Exception):
    """An event_id was reused with different content."""


class EventStore(Protocol):
    def append(self, event: Event) -> AppendResult: ...

    def events_for_order(self, tenant_id: str, order_ref: str) -> list[StoredEvent]:
        """Events for one order, in the order they happened (occurred_at), not the order they arrived."""
        ...
