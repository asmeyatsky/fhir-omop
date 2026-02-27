"""
Tenant Entity

Architectural Intent:
- Aggregate root for hospital/organization tenants
- Multi-tenancy scoping for all data operations
- Each hospital in the chain = one tenant
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime


@dataclass(frozen=True)
class TenantSettings:
    """Configurable settings per tenant."""
    max_pipelines_concurrent: int = 5
    data_retention_days: int = 2555  # ~7 years per Saudi regulation
    allowed_fhir_servers: tuple[str, ...] = ()


@dataclass(frozen=True)
class Tenant:
    """Aggregate root: a hospital/organization within the chain."""
    id: str
    name: str
    hospital_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    nphies_facility_id: str | None = None
    settings: TenantSettings = TenantSettings()

    @staticmethod
    def create(
        id: str,
        name: str,
        hospital_name: str,
        nphies_facility_id: str | None = None,
    ) -> Tenant:
        if not name.strip():
            raise ValueError("Tenant name cannot be empty")
        if not hospital_name.strip():
            raise ValueError("Hospital name cannot be empty")
        now = datetime.now(UTC)
        return Tenant(
            id=id,
            name=name.strip(),
            hospital_name=hospital_name.strip(),
            is_active=True,
            created_at=now,
            updated_at=now,
            nphies_facility_id=nphies_facility_id,
        )

    def deactivate(self) -> Tenant:
        return replace(self, is_active=False, updated_at=datetime.now(UTC))

    def activate(self) -> Tenant:
        return replace(self, is_active=True, updated_at=datetime.now(UTC))

    def update_settings(self, settings: TenantSettings) -> Tenant:
        return replace(self, settings=settings, updated_at=datetime.now(UTC))
