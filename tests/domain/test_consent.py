"""Tests for Consent Entity and Consent Service."""
import pytest
from datetime import UTC, datetime, timedelta

from src.domain.entities.consent import (
    Consent,
    ConsentPurpose,
    ConsentScope,
    ConsentStatus,
)
from src.domain.services.consent_service import ConsentService, ConsentViolationError
from src.infrastructure.repositories.in_memory import InMemoryConsentRepository


class TestConsentEntity:
    def test_grant_consent(self):
        consent = Consent.grant(
            id="c-001",
            patient_id="p-001",
            tenant_id="t-001",
            purpose=ConsentPurpose.TREATMENT,
            scope=ConsentScope.ALL_DATA,
            granted_by="u-001",
        )
        assert consent.status == ConsentStatus.ACTIVE
        assert consent.is_valid is True
        assert consent.patient_id == "p-001"

    def test_revoke_consent(self):
        consent = Consent.grant(
            id="c-002",
            patient_id="p-001",
            tenant_id="t-001",
            purpose=ConsentPurpose.RESEARCH,
            scope=ConsentScope.CLINICAL_ONLY,
            granted_by="u-001",
        )
        revoked = consent.revoke(revoked_by="u-002")
        assert revoked.status == ConsentStatus.REVOKED
        assert revoked.is_valid is False
        assert revoked.revoked_by == "u-002"

    def test_expired_consent_invalid(self):
        consent = Consent.grant(
            id="c-003",
            patient_id="p-001",
            tenant_id="t-001",
            purpose=ConsentPurpose.ANALYTICS,
            scope=ConsentScope.ALL_DATA,
            granted_by="u-001",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        assert consent.is_valid is False

    def test_future_expiry_valid(self):
        consent = Consent.grant(
            id="c-004",
            patient_id="p-001",
            tenant_id="t-001",
            purpose=ConsentPurpose.TREATMENT,
            scope=ConsentScope.ALL_DATA,
            granted_by="u-001",
            expires_at=datetime.now(UTC) + timedelta(days=365),
        )
        assert consent.is_valid is True

    def test_covers_all_data(self):
        consent = Consent.grant(
            id="c-005",
            patient_id="p-001",
            tenant_id="t-001",
            purpose=ConsentPurpose.TREATMENT,
            scope=ConsentScope.ALL_DATA,
            granted_by="u-001",
        )
        assert consent.covers_resource("Patient") is True
        assert consent.covers_resource("Condition") is True
        assert consent.covers_resource("Observation") is True

    def test_covers_clinical_only(self):
        consent = Consent.grant(
            id="c-006",
            patient_id="p-001",
            tenant_id="t-001",
            purpose=ConsentPurpose.RESEARCH,
            scope=ConsentScope.CLINICAL_ONLY,
            granted_by="u-001",
        )
        assert consent.covers_resource("Condition") is True
        assert consent.covers_resource("Observation") is True
        assert consent.covers_resource("Patient") is False

    def test_covers_demographics_only(self):
        consent = Consent.grant(
            id="c-007",
            patient_id="p-001",
            tenant_id="t-001",
            purpose=ConsentPurpose.ANALYTICS,
            scope=ConsentScope.DEMOGRAPHICS_ONLY,
            granted_by="u-001",
        )
        assert consent.covers_resource("Patient") is True
        assert consent.covers_resource("Condition") is False

    def test_covers_specific_resources(self):
        consent = Consent.grant(
            id="c-008",
            patient_id="p-001",
            tenant_id="t-001",
            purpose=ConsentPurpose.RESEARCH,
            scope=ConsentScope.SPECIFIC_RESOURCES,
            granted_by="u-001",
            resource_types=("Condition", "Observation"),
        )
        assert consent.covers_resource("Condition") is True
        assert consent.covers_resource("Observation") is True
        assert consent.covers_resource("Patient") is False

    def test_empty_patient_id_raises(self):
        with pytest.raises(ValueError, match="Patient ID"):
            Consent.grant(
                id="c-009", patient_id="", tenant_id="t-001",
                purpose=ConsentPurpose.TREATMENT, scope=ConsentScope.ALL_DATA,
                granted_by="u-001",
            )

    def test_frozen(self):
        consent = Consent.grant(
            id="c-010", patient_id="p-001", tenant_id="t-001",
            purpose=ConsentPurpose.TREATMENT, scope=ConsentScope.ALL_DATA,
            granted_by="u-001",
        )
        with pytest.raises(AttributeError):
            consent.status = ConsentStatus.REVOKED  # type: ignore[misc]


class TestConsentService:
    @pytest.fixture
    def repo(self):
        return InMemoryConsentRepository()

    @pytest.fixture
    def service(self, repo):
        return ConsentService(consent_repo=repo)

    @pytest.mark.asyncio
    async def test_check_consent_granted(self, repo, service):
        consent = Consent.grant(
            id="c-100", patient_id="p-001", tenant_id="t-001",
            purpose=ConsentPurpose.TREATMENT, scope=ConsentScope.ALL_DATA,
            granted_by="u-001",
        )
        await repo.save(consent)
        result = await service.check_consent(
            "p-001", "t-001", ConsentPurpose.TREATMENT, "Patient"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_check_consent_not_granted(self, service):
        result = await service.check_consent(
            "p-999", "t-001", ConsentPurpose.RESEARCH, "Patient"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_enforce_consent_passes(self, repo, service):
        consent = Consent.grant(
            id="c-101", patient_id="p-001", tenant_id="t-001",
            purpose=ConsentPurpose.TREATMENT, scope=ConsentScope.ALL_DATA,
            granted_by="u-001",
        )
        await repo.save(consent)
        # Should not raise
        await service.enforce_consent(
            "p-001", "t-001", ConsentPurpose.TREATMENT, "Patient"
        )

    @pytest.mark.asyncio
    async def test_enforce_consent_fails(self, service):
        with pytest.raises(ConsentViolationError):
            await service.enforce_consent(
                "p-999", "t-001", ConsentPurpose.RESEARCH, "Patient"
            )

    @pytest.mark.asyncio
    async def test_revoked_consent_not_found(self, repo, service):
        consent = Consent.grant(
            id="c-102", patient_id="p-001", tenant_id="t-001",
            purpose=ConsentPurpose.TREATMENT, scope=ConsentScope.ALL_DATA,
            granted_by="u-001",
        )
        revoked = consent.revoke("u-002")
        await repo.save(revoked)
        result = await service.check_consent(
            "p-001", "t-001", ConsentPurpose.TREATMENT, "Patient"
        )
        assert result is False
