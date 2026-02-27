"""
Tenant Repository Port

Architectural Intent:
- Interface for tenant persistence
- Defined in domain layer, implemented in infrastructure
"""
from __future__ import annotations

from typing import Protocol

from src.domain.entities.tenant import Tenant


class TenantRepositoryPort(Protocol):
    async def save(self, tenant: Tenant) -> None: ...
    async def get_by_id(self, id: str) -> Tenant | None: ...
    async def list_all(self) -> list[Tenant]: ...
    async def delete(self, id: str) -> None: ...
