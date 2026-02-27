"""
NPHIES Value Objects

Architectural Intent:
- Saudi NPHIES (National Platform for Health Information Exchange) compatibility
- FHIR R4.0.1 profile URLs and validation rules
- Resource enrichment for NPHIES submission
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# NPHIES FHIR Profile base URLs
NPHIES_BASE_URL = "http://nphies.sa/fhir/ksa"

# NPHIES Profile URLs per resource type
NPHIES_PROFILES: dict[str, str] = {
    "Patient": f"{NPHIES_BASE_URL}/nphies-fs/StructureDefinition/patient|1.0.0",
    "Encounter": f"{NPHIES_BASE_URL}/nphies-fs/StructureDefinition/encounter|1.0.0",
    "Condition": f"{NPHIES_BASE_URL}/nphies-fs/StructureDefinition/condition|1.0.0",
    "Observation": f"{NPHIES_BASE_URL}/nphies-fs/StructureDefinition/observation|1.0.0",
    "Organization": f"{NPHIES_BASE_URL}/nphies-fs/StructureDefinition/organization|1.0.0",
    "Practitioner": f"{NPHIES_BASE_URL}/nphies-fs/StructureDefinition/practitioner|1.0.0",
    "Coverage": f"{NPHIES_BASE_URL}/nphies-fs/StructureDefinition/coverage|1.0.0",
    "Claim": f"{NPHIES_BASE_URL}/nphies-fs/StructureDefinition/claim|1.0.0",
}

# NPHIES required identifier systems
NPHIES_IDENTIFIER_SYSTEMS = {
    "national_id": "http://nphies.sa/identifier/nationalid",
    "iqama": "http://nphies.sa/identifier/iqama",
    "passport": "http://nphies.sa/identifier/passport",
    "facility_id": "http://nphies.sa/identifier/nphies-facility",
    "provider_license": "http://nphies.sa/identifier/provider-license",
}

# NPHIES required code systems
NPHIES_CODE_SYSTEMS = {
    "diagnosis": "http://nphies.sa/terminology/CodeSystem/diagnosis",
    "procedure": "http://nphies.sa/terminology/CodeSystem/procedure",
    "service_type": "http://nphies.sa/terminology/CodeSystem/service-type",
}


class NPHIESValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class NPHIESValidationIssue:
    """A single validation issue found during NPHIES profile checking."""
    severity: NPHIESValidationSeverity
    field: str
    message: str
    profile: str | None = None


@dataclass(frozen=True)
class NPHIESValidationResult:
    """Result of validating a FHIR resource against NPHIES profiles."""
    resource_type: str
    resource_id: str | None
    is_valid: bool
    issues: tuple[NPHIESValidationIssue, ...]

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == NPHIESValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == NPHIESValidationSeverity.WARNING)
