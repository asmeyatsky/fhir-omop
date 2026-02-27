"""
OMOP CDM Domain Value Objects

Architectural Intent:
- Immutable value objects for OMOP CDM v5.4 concepts
- Maps OMOP table/column structure without infrastructure dependency
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.domain.value_objects.classification import DataClassification


class OMOPTable(str, Enum):
    """OMOP CDM v5.4 target tables for Phase 1."""
    PERSON = "person"
    VISIT_OCCURRENCE = "visit_occurrence"
    CONDITION_OCCURRENCE = "condition_occurrence"
    MEASUREMENT = "measurement"
    OBSERVATION = "observation"


class LoadStrategy(str, Enum):
    """Data loading strategies for OMOP targets."""
    FULL_REFRESH = "full_refresh"
    INCREMENTAL = "incremental"
    MERGE = "merge"


class DatabaseDialect(str, Enum):
    """Supported OMOP target database dialects."""
    POSTGRESQL = "postgresql"


@dataclass(frozen=True)
class OMOPTargetConfig:
    """Configuration for an OMOP CDM target database."""
    dialect: DatabaseDialect
    host: str
    port: int
    database: str
    schema: str = "public"
    load_strategy: LoadStrategy = LoadStrategy.INCREMENTAL


@dataclass(frozen=True)
class ConceptId:
    """An OMOP Standard Concept identifier."""
    concept_id: int
    concept_name: str
    vocabulary_id: str
    domain_id: str

    @staticmethod
    def unmapped() -> ConceptId:
        return ConceptId(concept_id=0, concept_name="No matching concept",
                         vocabulary_id="None", domain_id="None")

    @property
    def is_mapped(self) -> bool:
        return self.concept_id != 0


@dataclass(frozen=True)
class OMOPRecord:
    """A single transformed OMOP record ready for loading."""
    target_table: OMOPTable
    data: dict
    source_fhir_id: str
    mapping_version: str
    classification: DataClassification = DataClassification.CONFIDENTIAL
