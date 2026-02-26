"""
Mapping Domain Value Objects

Architectural Intent:
- Represents field-level mapping configurations between FHIR and OMOP
- Immutable — changes produce new instances
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.domain.value_objects.fhir import FHIRResourceType
from src.domain.value_objects.omop import OMOPTable


class TransformationType(str, Enum):
    """Types of field transformations."""
    DIRECT = "direct"
    VOCABULARY_LOOKUP = "vocabulary_lookup"
    DATE_EXTRACT = "date_extract"
    CONDITIONAL = "conditional"
    CONSTANT = "constant"
    CUSTOM_WHISTLE = "custom_whistle"


@dataclass(frozen=True)
class FieldMapping:
    """A single field-level mapping from FHIR path to OMOP column."""
    source_path: str          # e.g., "Patient.birthDate"
    target_column: str        # e.g., "year_of_birth"
    transformation: TransformationType
    parameters: tuple[tuple[str, str], ...] = ()  # Immutable key-value pairs

    def get_parameter(self, key: str) -> str | None:
        for k, v in self.parameters:
            if k == key:
                return v
        return None


@dataclass(frozen=True)
class MappingTemplate:
    """A reusable mapping template for a FHIR resource to OMOP table pair."""
    template_id: str
    name: str
    description: str
    source_resource: FHIRResourceType
    target_table: OMOPTable
    field_mappings: tuple[FieldMapping, ...]
    whistle_code: str
    version: str

    @property
    def field_count(self) -> int:
        return len(self.field_mappings)
