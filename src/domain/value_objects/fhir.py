"""
FHIR Domain Value Objects

Architectural Intent:
- Immutable value objects representing FHIR-related concepts
- No identity — equality based on structural content
- Zero infrastructure dependencies
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FHIRResourceType(str, Enum):
    """Supported FHIR R4 resource types for Phase 1."""
    PATIENT = "Patient"
    ENCOUNTER = "Encounter"
    CONDITION = "Condition"
    OBSERVATION = "Observation"


class AuthMethod(str, Enum):
    """Supported authentication methods for FHIR server connections."""
    SMART_ON_FHIR = "smart_on_fhir"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    MTLS = "mtls"


class FHIRServerType(str, Enum):
    """Known FHIR server implementations."""
    HAPI = "hapi"
    GOOGLE_HEALTHCARE_API = "google_healthcare_api"
    AZURE = "azure"
    EPIC = "epic"
    CERNER = "cerner"
    CUSTOM = "custom"


@dataclass(frozen=True)
class FHIREndpoint:
    """A FHIR server endpoint configuration."""
    base_url: str
    server_type: FHIRServerType
    auth_method: AuthMethod

    def capability_statement_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/metadata"


@dataclass(frozen=True)
class FHIRResourceReference:
    """A reference to a specific FHIR resource."""
    resource_type: FHIRResourceType
    resource_id: str

    @property
    def reference_string(self) -> str:
        return f"{self.resource_type.value}/{self.resource_id}"


@dataclass(frozen=True)
class FHIRBundle:
    """An immutable collection of FHIR resources as raw JSON dicts."""
    resource_type: FHIRResourceType
    resources: tuple[dict, ...]

    @property
    def count(self) -> int:
        return len(self.resources)

    def is_empty(self) -> bool:
        return self.count == 0
