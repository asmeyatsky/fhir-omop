"""
Data Classification Service (NDMO)

Architectural Intent:
- Classifies FHIR resources and fields per NDMO data governance
- Uses configurable policies (defaults provided)
- Returns highest applicable classification level
"""
from __future__ import annotations

import fnmatch

from src.domain.value_objects.classification import (
    DEFAULT_POLICIES,
    ClassificationPolicy,
    DataClassification,
)


class ClassificationService:
    """Classifies data per NDMO guidelines using configurable policies."""

    def __init__(
        self,
        policies: tuple[ClassificationPolicy, ...] | None = None,
    ) -> None:
        self._policies = policies or DEFAULT_POLICIES

    def classify_resource(
        self, resource_type: str, resource_data: dict
    ) -> DataClassification:
        """Determine the highest classification level for a FHIR resource."""
        highest = DataClassification.PUBLIC

        for policy in self._policies:
            if policy.resource_type and policy.resource_type not in (resource_type, "*"):
                continue

            # Check if any field in the resource matches the policy pattern
            if policy.field_pattern == "*":
                if policy.classification > highest:
                    highest = policy.classification
                continue

            if policy.field_pattern:
                # Match top-level keys against pattern (e.g. "identifier.*" matches "identifier")
                pattern_prefix = policy.field_pattern.split(".")[0]
                for key in resource_data:
                    if fnmatch.fnmatch(key, policy.field_pattern) or key == pattern_prefix:
                        if policy.classification > highest:
                            highest = policy.classification
                        break

        return highest

    def classify_field(
        self, resource_type: str, field_path: str
    ) -> DataClassification:
        """Determine the classification level for a specific field."""
        highest = DataClassification.PUBLIC

        for policy in self._policies:
            if policy.resource_type and policy.resource_type not in (resource_type, "*"):
                continue
            if policy.field_pattern and fnmatch.fnmatch(field_path, policy.field_pattern):
                if policy.classification > highest:
                    highest = policy.classification

        return highest

    def get_policies(self) -> list[ClassificationPolicy]:
        return list(self._policies)

    def get_sensitive_fields(self, resource_type: str) -> list[str]:
        """Return field patterns classified as CONFIDENTIAL or higher."""
        result = []
        for policy in self._policies:
            if policy.resource_type and policy.resource_type not in (resource_type, "*"):
                continue
            if policy.classification >= DataClassification.CONFIDENTIAL and policy.field_pattern:
                result.append(policy.field_pattern)
        return result
