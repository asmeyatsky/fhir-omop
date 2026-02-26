"""
Source Connection Entity

Architectural Intent:
- Aggregate root for FHIR source server connections
- Encapsulates connection lifecycle (created → tested → active/failed)
- Business rules: connection must be tested before use in pipelines
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum

from src.domain.events.event_base import DomainEvent
from src.domain.events.pipeline_events import SourceConnectionTestedEvent
from src.domain.value_objects.fhir import AuthMethod, FHIREndpoint, FHIRServerType


class ConnectionStatus(str, Enum):
    CREATED = "created"
    TESTING = "testing"
    ACTIVE = "active"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass(frozen=True)
class SourceConnection:
    """Aggregate root: a configured FHIR source server connection."""
    id: str
    name: str
    endpoint: FHIREndpoint
    status: ConnectionStatus
    created_at: datetime
    last_tested_at: datetime | None = None
    capabilities: tuple[str, ...] = ()
    error_message: str | None = None
    domain_events: tuple[DomainEvent, ...] = field(default=())

    @staticmethod
    def create(
        id: str,
        name: str,
        base_url: str,
        server_type: FHIRServerType,
        auth_method: AuthMethod,
    ) -> SourceConnection:
        """Factory method to create a new source connection."""
        if not name.strip():
            raise ValueError("Connection name cannot be empty")
        if not base_url.strip():
            raise ValueError("Base URL cannot be empty")

        return SourceConnection(
            id=id,
            name=name.strip(),
            endpoint=FHIREndpoint(
                base_url=base_url.strip().rstrip("/"),
                server_type=server_type,
                auth_method=auth_method,
            ),
            status=ConnectionStatus.CREATED,
            created_at=datetime.now(UTC),
        )

    def mark_testing(self) -> SourceConnection:
        return replace(self, status=ConnectionStatus.TESTING)

    def mark_active(self, capabilities: tuple[str, ...]) -> SourceConnection:
        now = datetime.now(UTC)
        return replace(
            self,
            status=ConnectionStatus.ACTIVE,
            last_tested_at=now,
            capabilities=capabilities,
            error_message=None,
            domain_events=self.domain_events + (
                SourceConnectionTestedEvent(
                    aggregate_id=self.id, success=True, message="Connection active"
                ),
            ),
        )

    def mark_failed(self, error: str) -> SourceConnection:
        now = datetime.now(UTC)
        return replace(
            self,
            status=ConnectionStatus.FAILED,
            last_tested_at=now,
            error_message=error,
            domain_events=self.domain_events + (
                SourceConnectionTestedEvent(
                    aggregate_id=self.id, success=False, message=error
                ),
            ),
        )

    def disable(self) -> SourceConnection:
        return replace(self, status=ConnectionStatus.DISABLED)

    @property
    def is_usable(self) -> bool:
        """A connection is usable in pipelines only when active."""
        return self.status == ConnectionStatus.ACTIVE
