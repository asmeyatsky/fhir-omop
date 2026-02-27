"""
Data Classification Port

Architectural Intent:
- Interface for data classification per NDMO guidelines
- Defined in domain layer, implemented in infrastructure
"""
from __future__ import annotations

from typing import Protocol

from src.domain.value_objects.classification import ClassificationPolicy, DataClassification


class DataClassificationPort(Protocol):
    def classify_resource(self, resource_type: str, resource_data: dict) -> DataClassification:
        """Determine the highest classification level for a FHIR resource."""
        ...

    def classify_field(self, resource_type: str, field_path: str) -> DataClassification:
        """Determine the classification level for a specific field."""
        ...

    def get_policies(self) -> list[ClassificationPolicy]:
        """Return all active classification policies."""
        ...
