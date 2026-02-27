"""
Encryption Value Objects

Architectural Intent:
- Defines PII field paths per FHIR resource type
- Used by encryption service to determine which fields to encrypt
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EncryptedField:
    """Represents an encrypted field value with metadata."""
    ciphertext: str
    algorithm: str = "AES-256-GCM"


# PII field paths per FHIR resource type that require encryption
PII_FIELD_PATHS: dict[str, list[str]] = {
    "Patient": [
        "person_source_value",
        "gender_source_value",
        "year_of_birth",
        "month_of_birth",
        "day_of_birth",
    ],
    "Encounter": [
        "person_source_value",
        "visit_source_value",
    ],
    "Condition": [
        "person_source_value",
        "condition_source_value",
    ],
    "Observation": [
        "person_source_value",
        "observation_source_value",
        "value_as_string",
    ],
}

# OMOP table fields that contain PII (used for output encryption)
OMOP_PII_FIELDS: dict[str, list[str]] = {
    "person": ["person_source_value"],
    "visit_occurrence": ["person_source_value", "visit_source_value"],
    "condition_occurrence": ["person_source_value", "condition_source_value"],
    "measurement": ["person_source_value", "measurement_source_value"],
    "observation": ["person_source_value", "observation_source_value", "value_as_string"],
}
