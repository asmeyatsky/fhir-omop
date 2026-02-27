"""
Audit Log Port

Architectural Intent:
- Interface for audit log persistence
- Defined in domain layer, implemented in infrastructure
- Supports append-only semantics (ISO 27789)
"""
from __future__ import annotations

from typing import Protocol

from src.domain.entities.audit_entry import AuditEntry


class AuditLogPort(Protocol):
    async def record(self, entry: AuditEntry) -> None:
        """Append an audit entry. Must be append-only (no updates/deletes)."""
        ...

    async def get_by_id(self, id: str) -> AuditEntry | None:
        """Retrieve a single audit entry by ID."""
        ...

    async def query(
        self,
        tenant_id: str | None = None,
        actor_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit entries with optional filters."""
        ...

    async def count(
        self,
        tenant_id: str | None = None,
        actor_id: str | None = None,
        event_type: str | None = None,
    ) -> int:
        """Count audit entries matching filters."""
        ...
