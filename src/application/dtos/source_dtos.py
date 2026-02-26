"""DTOs for Source Connection operations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.source_connection import ConnectionStatus
from src.domain.value_objects.fhir import AuthMethod, FHIRServerType


@dataclass(frozen=True)
class CreateSourceConnectionDTO:
    name: str
    base_url: str
    server_type: FHIRServerType
    auth_method: AuthMethod


@dataclass(frozen=True)
class SourceConnectionResponseDTO:
    id: str
    name: str
    base_url: str
    server_type: str
    auth_method: str
    status: str
    created_at: datetime
    last_tested_at: datetime | None
    capabilities: list[str]
    error_message: str | None
