"""
PostgreSQL Event Bus

Architectural Intent:
- Persists domain events to PostgreSQL for durability and replay
- Implements EventBusPort from domain layer
- Events stored as JSONB for flexible schema evolution
"""
from __future__ import annotations

import json
from dataclasses import asdict

import asyncpg

from src.domain.events.event_base import DomainEvent


class PostgreSQLEventBus:
    """Persistent event bus that stores domain events in PostgreSQL."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def publish(self, events: list) -> None:
        if not events:
            return

        async with self._pool.acquire() as conn:
            for event in events:
                event_type = type(event).__name__
                payload = self._serialize_event(event)
                occurred_at = event.occurred_at if isinstance(event, DomainEvent) else None

                await conn.execute(
                    """
                    INSERT INTO domain_event (aggregate_id, event_type, payload, occurred_at)
                    VALUES ($1, $2, $3, $4)
                    """,
                    event.aggregate_id if isinstance(event, DomainEvent) else "unknown",
                    event_type,
                    json.dumps(payload, default=str),
                    occurred_at,
                )

    @staticmethod
    def _serialize_event(event: object) -> dict:
        if isinstance(event, DomainEvent):
            return asdict(event)
        return {"raw": str(event)}
