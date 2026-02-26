"""
Domain Event Base

Architectural Intent:
- Base class for all domain events
- Events are immutable records of something that happened in the domain
- Collected on aggregates, dispatched by application layer
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class DomainEvent:
    """Base domain event."""
    aggregate_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
