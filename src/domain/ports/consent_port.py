"""
Consent Port

Architectural Intent:
- Interface for consent storage and querying
- Defined in domain layer, implemented in infrastructure
"""
from __future__ import annotations

from typing import Protocol

from src.domain.entities.consent import Consent


class ConsentRepositoryPort(Protocol):
    async def save(self, consent: Consent) -> None: ...
    async def get_by_id(self, id: str) -> Consent | None: ...

    async def get_active_consents(
        self, patient_id: str, tenant_id: str
    ) -> list[Consent]: ...

    async def list_by_tenant(
        self, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> list[Consent]: ...

    async def delete(self, id: str) -> None: ...
