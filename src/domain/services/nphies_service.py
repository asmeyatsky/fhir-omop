"""
NPHIES Service

Architectural Intent:
- Validates FHIR resources against NPHIES profiles
- Enriches resources with NPHIES-required metadata
- Prepares resources for NPHIES submission
"""
from __future__ import annotations

import copy

from src.domain.value_objects.nphies import (
    NPHIES_IDENTIFIER_SYSTEMS,
    NPHIES_PROFILES,
    NPHIESValidationIssue,
    NPHIESValidationResult,
    NPHIESValidationSeverity,
)


class NPHIESService:
    """Validates and enriches FHIR resources for NPHIES compatibility."""

    def validate(self, resource: dict) -> NPHIESValidationResult:
        """Validate a FHIR resource against NPHIES profile requirements."""
        resource_type = resource.get("resourceType", "Unknown")
        resource_id = resource.get("id")
        issues: list[NPHIESValidationIssue] = []

        # Check if resource type has an NPHIES profile
        profile_url = NPHIES_PROFILES.get(resource_type)
        if not profile_url:
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.WARNING,
                field="resourceType",
                message=f"No NPHIES profile defined for {resource_type}",
            ))

        # Check meta.profile
        meta = resource.get("meta", {})
        profiles = meta.get("profile", [])
        if profile_url and profile_url not in profiles:
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.WARNING,
                field="meta.profile",
                message=f"Resource does not declare NPHIES profile: {profile_url}",
                profile=profile_url,
            ))

        # Resource-specific validation
        if resource_type == "Patient":
            self._validate_patient(resource, issues)
        elif resource_type == "Encounter":
            self._validate_encounter(resource, issues)
        elif resource_type == "Condition":
            self._validate_condition(resource, issues)

        is_valid = not any(
            i.severity == NPHIESValidationSeverity.ERROR for i in issues
        )

        return NPHIESValidationResult(
            resource_type=resource_type,
            resource_id=resource_id,
            is_valid=is_valid,
            issues=tuple(issues),
        )

    def enrich(self, resource: dict) -> dict:
        """Add NPHIES-required metadata to a FHIR resource."""
        result = copy.deepcopy(resource)
        resource_type = result.get("resourceType", "Unknown")

        # Add NPHIES profile to meta
        profile_url = NPHIES_PROFILES.get(resource_type)
        if profile_url:
            if "meta" not in result:
                result["meta"] = {}
            if "profile" not in result["meta"]:
                result["meta"]["profile"] = []
            if profile_url not in result["meta"]["profile"]:
                result["meta"]["profile"].append(profile_url)

        return result

    def _validate_patient(
        self, resource: dict, issues: list[NPHIESValidationIssue]
    ) -> None:
        """Validate Patient-specific NPHIES requirements."""
        identifiers = resource.get("identifier", [])
        if not identifiers:
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.ERROR,
                field="identifier",
                message="Patient must have at least one identifier",
            ))

        # Check for NPHIES-recognized identifier systems
        systems = [i.get("system", "") for i in identifiers]
        nphies_systems = set(NPHIES_IDENTIFIER_SYSTEMS.values())
        has_nphies_id = any(s in nphies_systems for s in systems)
        if not has_nphies_id and identifiers:
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.WARNING,
                field="identifier.system",
                message="No NPHIES-recognized identifier system found "
                "(national_id, iqama, or passport recommended)",
            ))

        # Check name
        if not resource.get("name"):
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.ERROR,
                field="name",
                message="Patient must have a name",
            ))

        # Check gender
        if not resource.get("gender"):
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.WARNING,
                field="gender",
                message="Patient gender is recommended for NPHIES",
            ))

    def _validate_encounter(
        self, resource: dict, issues: list[NPHIESValidationIssue]
    ) -> None:
        """Validate Encounter-specific NPHIES requirements."""
        if not resource.get("status"):
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.ERROR,
                field="status",
                message="Encounter must have a status",
            ))

        if not resource.get("class"):
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.ERROR,
                field="class",
                message="Encounter must have a class",
            ))

        if not resource.get("subject"):
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.ERROR,
                field="subject",
                message="Encounter must reference a patient",
            ))

    def _validate_condition(
        self, resource: dict, issues: list[NPHIESValidationIssue]
    ) -> None:
        """Validate Condition-specific NPHIES requirements."""
        if not resource.get("code"):
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.ERROR,
                field="code",
                message="Condition must have a code",
            ))

        if not resource.get("subject"):
            issues.append(NPHIESValidationIssue(
                severity=NPHIESValidationSeverity.ERROR,
                field="subject",
                message="Condition must reference a patient",
            ))
