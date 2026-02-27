"""
Audit Entry Entity

Architectural Intent:
- Immutable audit trail per ISO 27789 (health informatics audit trail)
- SHA-256 checksum for tamper evidence
- Captures actor, action, resource, and request context
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class AuditEventType(str, Enum):
    """Categories of auditable events."""
    AUTH = "auth"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    PIPELINE = "pipeline"
    ADMIN = "admin"
    CONSENT = "consent"
    SYSTEM = "system"


class AuditAction(str, Enum):
    """Specific actions within event types."""
    # Auth
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    TOKEN_REFRESH = "token_refresh"
    LOGOUT = "logout"

    # Data access
    READ = "read"
    LIST = "list"
    EXPORT = "export"

    # Data modification
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

    # Pipeline
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    PIPELINE_FAIL = "pipeline_fail"

    # Admin
    USER_CREATE = "user_create"
    USER_DEACTIVATE = "user_deactivate"
    ROLE_CHANGE = "role_change"
    TENANT_CREATE = "tenant_create"

    # Consent
    CONSENT_GRANT = "consent_grant"
    CONSENT_REVOKE = "consent_revoke"


@dataclass(frozen=True)
class AuditEntry:
    """Immutable audit log entry with tamper-evident checksum."""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    action: AuditAction
    actor_id: str | None
    actor_email: str | None
    actor_role: str | None
    tenant_id: str | None
    resource_type: str | None
    resource_id: str | None
    http_method: str | None
    http_path: str | None
    http_status: int | None
    ip_address: str | None
    user_agent: str | None
    details: dict | None
    checksum: str

    @staticmethod
    def create(
        id: str,
        event_type: AuditEventType,
        action: AuditAction,
        actor_id: str | None = None,
        actor_email: str | None = None,
        actor_role: str | None = None,
        tenant_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        http_method: str | None = None,
        http_path: str | None = None,
        http_status: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None,
    ) -> AuditEntry:
        timestamp = datetime.now(UTC)
        checksum = AuditEntry._compute_checksum(
            id=id,
            timestamp=timestamp,
            event_type=event_type,
            action=action,
            actor_id=actor_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            http_method=http_method,
            http_path=http_path,
        )
        return AuditEntry(
            id=id,
            timestamp=timestamp,
            event_type=event_type,
            action=action,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            http_method=http_method,
            http_path=http_path,
            http_status=http_status,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            checksum=checksum,
        )

    @staticmethod
    def _compute_checksum(
        id: str,
        timestamp: datetime,
        event_type: AuditEventType,
        action: AuditAction,
        actor_id: str | None,
        tenant_id: str | None,
        resource_type: str | None,
        resource_id: str | None,
        http_method: str | None,
        http_path: str | None,
    ) -> str:
        """SHA-256 checksum over key fields for tamper evidence."""
        payload = json.dumps(
            {
                "id": id,
                "timestamp": timestamp.isoformat(),
                "event_type": event_type.value,
                "action": action.value,
                "actor_id": actor_id,
                "tenant_id": tenant_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "http_method": http_method,
                "http_path": http_path,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Recompute checksum and compare — detects tampering."""
        expected = self._compute_checksum(
            id=self.id,
            timestamp=self.timestamp,
            event_type=self.event_type,
            action=self.action,
            actor_id=self.actor_id,
            tenant_id=self.tenant_id,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            http_method=self.http_method,
            http_path=self.http_path,
        )
        return self.checksum == expected
