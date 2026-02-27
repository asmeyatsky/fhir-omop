"""
Data Classification Value Objects (NDMO)

Architectural Intent:
- Saudi NDMO data governance classification levels
- Classifies all data flows: PUBLIC, INTERNAL, CONFIDENTIAL, TOP_SECRET
- Patient IDs and PII → TOP_SECRET
- Clinical data → CONFIDENTIAL
- Administrative data → INTERNAL
- Public reference data → PUBLIC
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DataClassification(str, Enum):
    """NDMO data classification levels (ascending sensitivity)."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    TOP_SECRET = "top_secret"

    @property
    def sensitivity_level(self) -> int:
        return {"public": 0, "internal": 1, "confidential": 2, "top_secret": 3}[self.value]

    def __ge__(self, other: DataClassification) -> bool:
        return self.sensitivity_level >= other.sensitivity_level

    def __gt__(self, other: DataClassification) -> bool:
        return self.sensitivity_level > other.sensitivity_level

    def __le__(self, other: DataClassification) -> bool:
        return self.sensitivity_level <= other.sensitivity_level

    def __lt__(self, other: DataClassification) -> bool:
        return self.sensitivity_level < other.sensitivity_level


@dataclass(frozen=True)
class ClassificationPolicy:
    """A rule mapping data patterns to classification levels."""
    id: str
    name: str
    resource_type: str | None  # FHIR resource type or "*"
    field_pattern: str | None  # Field path pattern (e.g., "identifier.*", "name.*")
    classification: DataClassification
    description: str = ""


# Default classification rules per NDMO guidelines
DEFAULT_POLICIES: tuple[ClassificationPolicy, ...] = (
    # TOP_SECRET: Patient identifiers, national IDs, contact info
    ClassificationPolicy(
        id="pol-001", name="Patient Identifiers", resource_type="Patient",
        field_pattern="identifier.*", classification=DataClassification.TOP_SECRET,
        description="National IDs, MRNs, passport numbers",
    ),
    ClassificationPolicy(
        id="pol-002", name="Patient Contact", resource_type="Patient",
        field_pattern="telecom.*", classification=DataClassification.TOP_SECRET,
        description="Phone numbers, email addresses",
    ),
    ClassificationPolicy(
        id="pol-003", name="Patient Address", resource_type="Patient",
        field_pattern="address.*", classification=DataClassification.TOP_SECRET,
        description="Physical addresses",
    ),
    ClassificationPolicy(
        id="pol-004", name="Patient Name", resource_type="Patient",
        field_pattern="name.*", classification=DataClassification.TOP_SECRET,
        description="Patient full name, family name",
    ),
    ClassificationPolicy(
        id="pol-005", name="Person Source Value", resource_type="*",
        field_pattern="person_source_value", classification=DataClassification.TOP_SECRET,
        description="OMOP person source value containing patient ID",
    ),
    # CONFIDENTIAL: Clinical data
    ClassificationPolicy(
        id="pol-010", name="Conditions", resource_type="Condition",
        field_pattern="*", classification=DataClassification.CONFIDENTIAL,
        description="Diagnosis and condition data",
    ),
    ClassificationPolicy(
        id="pol-011", name="Observations", resource_type="Observation",
        field_pattern="*", classification=DataClassification.CONFIDENTIAL,
        description="Clinical observations and lab results",
    ),
    ClassificationPolicy(
        id="pol-012", name="Encounters", resource_type="Encounter",
        field_pattern="*", classification=DataClassification.CONFIDENTIAL,
        description="Visit and encounter data",
    ),
    # INTERNAL: Administrative data
    ClassificationPolicy(
        id="pol-020", name="Admin Metadata", resource_type="*",
        field_pattern="meta.*", classification=DataClassification.INTERNAL,
        description="Resource metadata",
    ),
    # PUBLIC: Terminology and reference data
    ClassificationPolicy(
        id="pol-030", name="Value Sets", resource_type="ValueSet",
        field_pattern="*", classification=DataClassification.PUBLIC,
        description="Terminology value sets",
    ),
    ClassificationPolicy(
        id="pol-031", name="Code Systems", resource_type="CodeSystem",
        field_pattern="*", classification=DataClassification.PUBLIC,
        description="Terminology code systems",
    ),
)
