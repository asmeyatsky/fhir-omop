"""
Consent Entity (PDPL)

Architectural Intent:
- Saudi PDPL (Personal Data Protection Law) consent tracking
- Tracks patient consent for data processing purposes
- Consent can be granted, revoked, or expired
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum


class ConsentStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ConsentPurpose(str, Enum):
    """Data processing purposes per PDPL."""
    TREATMENT = "treatment"
    RESEARCH = "research"
    ANALYTICS = "analytics"
    PUBLIC_HEALTH = "public_health"
    QUALITY_IMPROVEMENT = "quality_improvement"


class ConsentScope(str, Enum):
    """Scope of data covered by consent."""
    ALL_DATA = "all_data"
    CLINICAL_ONLY = "clinical_only"
    DEMOGRAPHICS_ONLY = "demographics_only"
    SPECIFIC_RESOURCES = "specific_resources"


@dataclass(frozen=True)
class Consent:
    """Patient consent record for PDPL compliance."""
    id: str
    patient_id: str
    tenant_id: str
    purpose: ConsentPurpose
    scope: ConsentScope
    status: ConsentStatus
    granted_by: str  # User who recorded the consent
    granted_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    revoked_by: str | None
    resource_types: tuple[str, ...] | None  # For SPECIFIC_RESOURCES scope
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def grant(
        id: str,
        patient_id: str,
        tenant_id: str,
        purpose: ConsentPurpose,
        scope: ConsentScope,
        granted_by: str,
        expires_at: datetime | None = None,
        resource_types: tuple[str, ...] | None = None,
        notes: str | None = None,
    ) -> Consent:
        if not patient_id.strip():
            raise ValueError("Patient ID cannot be empty")
        now = datetime.now(UTC)
        return Consent(
            id=id,
            patient_id=patient_id.strip(),
            tenant_id=tenant_id,
            purpose=purpose,
            scope=scope,
            status=ConsentStatus.ACTIVE,
            granted_by=granted_by,
            granted_at=now,
            expires_at=expires_at,
            revoked_at=None,
            revoked_by=None,
            resource_types=resource_types,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

    def revoke(self, revoked_by: str) -> Consent:
        return replace(
            self,
            status=ConsentStatus.REVOKED,
            revoked_at=datetime.now(UTC),
            revoked_by=revoked_by,
            updated_at=datetime.now(UTC),
        )

    @property
    def is_valid(self) -> bool:
        if self.status != ConsentStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return False
        return True

    def covers_resource(self, resource_type: str) -> bool:
        """Check if this consent covers a specific FHIR resource type."""
        if not self.is_valid:
            return False
        if self.scope == ConsentScope.ALL_DATA:
            return True
        if self.scope == ConsentScope.SPECIFIC_RESOURCES:
            return self.resource_types is not None and resource_type in self.resource_types
        if self.scope == ConsentScope.CLINICAL_ONLY:
            return resource_type in ("Condition", "Observation", "Encounter", "Procedure",
                                      "MedicationRequest", "DiagnosticReport")
        if self.scope == ConsentScope.DEMOGRAPHICS_ONLY:
            return resource_type == "Patient"
        return False
