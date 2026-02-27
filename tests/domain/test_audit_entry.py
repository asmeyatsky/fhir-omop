"""Tests for AuditEntry entity."""
from src.domain.entities.audit_entry import AuditAction, AuditEntry, AuditEventType


class TestAuditEntry:
    def test_create_entry(self):
        entry = AuditEntry.create(
            id="audit-001",
            event_type=AuditEventType.AUTH,
            action=AuditAction.LOGIN_SUCCESS,
            actor_id="u-001",
            actor_email="admin@kfshrc.sa",
            actor_role="admin",
            tenant_id="t-001",
            http_method="POST",
            http_path="/api/v1/auth/login",
            http_status=200,
            ip_address="10.0.0.1",
        )
        assert entry.id == "audit-001"
        assert entry.event_type == AuditEventType.AUTH
        assert entry.action == AuditAction.LOGIN_SUCCESS
        assert entry.actor_id == "u-001"
        assert entry.checksum is not None
        assert len(entry.checksum) == 64  # SHA-256 hex digest

    def test_verify_integrity_passes(self):
        entry = AuditEntry.create(
            id="audit-002",
            event_type=AuditEventType.DATA_ACCESS,
            action=AuditAction.READ,
            actor_id="u-001",
            tenant_id="t-001",
            http_method="GET",
            http_path="/api/v1/sources",
            http_status=200,
        )
        assert entry.verify_integrity() is True

    def test_tampered_entry_fails_integrity(self):
        entry = AuditEntry.create(
            id="audit-003",
            event_type=AuditEventType.DATA_MODIFICATION,
            action=AuditAction.CREATE,
            actor_id="u-001",
            tenant_id="t-001",
        )
        # Simulate tampering by creating a new entry with modified data but same checksum
        tampered = AuditEntry(
            id=entry.id,
            timestamp=entry.timestamp,
            event_type=entry.event_type,
            action=entry.action,
            actor_id="u-999",  # tampered actor
            actor_email=entry.actor_email,
            actor_role=entry.actor_role,
            tenant_id=entry.tenant_id,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            http_method=entry.http_method,
            http_path=entry.http_path,
            http_status=entry.http_status,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            details=entry.details,
            checksum=entry.checksum,  # original checksum
        )
        assert tampered.verify_integrity() is False

    def test_frozen(self):
        entry = AuditEntry.create(
            id="audit-004",
            event_type=AuditEventType.SYSTEM,
            action=AuditAction.READ,
        )
        import pytest
        with pytest.raises(AttributeError):
            entry.actor_id = "changed"  # type: ignore[misc]

    def test_create_with_details(self):
        entry = AuditEntry.create(
            id="audit-005",
            event_type=AuditEventType.PIPELINE,
            action=AuditAction.PIPELINE_START,
            details={"pipeline_id": "p-001", "duration_ms": 123.45},
        )
        assert entry.details == {"pipeline_id": "p-001", "duration_ms": 123.45}

    def test_all_event_types(self):
        assert len(AuditEventType) == 7

    def test_all_actions(self):
        assert len(AuditAction) >= 18
