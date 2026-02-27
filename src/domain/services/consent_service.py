"""
Consent Service (PDPL)

Architectural Intent:
- Enforces PDPL consent rules before data processing
- Checks if patient has active consent for given purpose and resource type
"""
from __future__ import annotations

from src.domain.entities.consent import Consent, ConsentPurpose


class ConsentViolationError(Exception):
    """Raised when processing is attempted without valid consent."""

    def __init__(self, patient_id: str, purpose: ConsentPurpose, resource_type: str):
        self.patient_id = patient_id
        self.purpose = purpose
        self.resource_type = resource_type
        super().__init__(
            f"No valid consent for patient '{patient_id}' "
            f"for purpose '{purpose.value}' on resource '{resource_type}'"
        )


class ConsentService:
    """Checks and enforces PDPL consent requirements."""

    def __init__(self, consent_repo) -> None:
        self._repo = consent_repo

    async def check_consent(
        self,
        patient_id: str,
        tenant_id: str,
        purpose: ConsentPurpose,
        resource_type: str,
    ) -> bool:
        """Check if patient has valid consent for the given purpose and resource."""
        consents = await self._repo.get_active_consents(patient_id, tenant_id)
        for consent in consents:
            if consent.purpose == purpose and consent.covers_resource(resource_type):
                return True
        return False

    async def enforce_consent(
        self,
        patient_id: str,
        tenant_id: str,
        purpose: ConsentPurpose,
        resource_type: str,
    ) -> None:
        """Raise ConsentViolationError if no valid consent exists."""
        has_consent = await self.check_consent(
            patient_id, tenant_id, purpose, resource_type
        )
        if not has_consent:
            raise ConsentViolationError(patient_id, purpose, resource_type)

    async def get_patient_consents(
        self, patient_id: str, tenant_id: str
    ) -> list[Consent]:
        """Get all active consents for a patient."""
        return await self._repo.get_active_consents(patient_id, tenant_id)
