"""
Mapping Template Registry

Architectural Intent:
- Provides pre-built FHIR R4 → OMOP CDM v5.4 mapping templates
- Phase 1 covers: Patient→Person, Encounter→Visit_Occurrence,
  Condition→Condition_Occurrence, Observation→Measurement/Observation
- Templates generate Whistle-compatible JSON-DSL mapping rules
- Each template documents the mapping logic per PRD Section 7

Key Mapping Reference (from PRD):
- Patient: identifier→person_source_value, birthDate→year/month/day_of_birth,
  gender→gender_concept_id, race(US Core)→race_concept_id
- Encounter: period→visit_start/end_date, class→visit_concept_id,
  type→visit_type_concept_id, serviceProvider→care_site_id
- Condition: code→condition_concept_id, onsetDateTime→condition_start_date,
  clinicalStatus→condition_status_concept_id
- Observation: domain-routed (LOINC→Measurement, others→Observation),
  valueQuantity→value_as_number+unit_concept_id
"""
from __future__ import annotations

import json

from src.domain.value_objects.fhir import FHIRResourceType
from src.domain.value_objects.mapping import FieldMapping, MappingTemplate, TransformationType
from src.domain.value_objects.omop import OMOPTable


def _build_whistle_code(mappings: list[dict]) -> str:
    """Generate Whistle-compatible JSON-DSL from mapping rules."""
    return json.dumps({"mappings": mappings}, indent=2)


def build_patient_to_person_template() -> MappingTemplate:
    """Patient → PERSON mapping template."""
    field_mappings = (
        FieldMapping(
            source_path="identifier[0].value",
            target_column="person_source_value",
            transformation=TransformationType.DIRECT,
        ),
        FieldMapping(
            source_path="birthDate",
            target_column="year_of_birth",
            transformation=TransformationType.DATE_EXTRACT,
            parameters=(("component", "year"),),
        ),
        FieldMapping(
            source_path="birthDate",
            target_column="month_of_birth",
            transformation=TransformationType.DATE_EXTRACT,
            parameters=(("component", "month"),),
        ),
        FieldMapping(
            source_path="birthDate",
            target_column="day_of_birth",
            transformation=TransformationType.DATE_EXTRACT,
            parameters=(("component", "day"),),
        ),
        FieldMapping(
            source_path="gender",
            target_column="gender_concept_id",
            transformation=TransformationType.VOCABULARY_LOOKUP,
            parameters=(("vocabulary", "Gender"),),
        ),
        FieldMapping(
            source_path="gender",
            target_column="gender_source_value",
            transformation=TransformationType.DIRECT,
        ),
    )

    whistle_rules = [
        {"source": "id", "target": "person_id", "transform": "person_id_hash"},
        {"source": "identifier[0].value", "target": "person_source_value", "transform": "direct",
         "default": "unknown", "allow_null": True},
        {"source": "birthDate", "target": "year_of_birth", "transform": "year_from_date",
         "default": 1900, "allow_null": True},
        {"source": "birthDate", "target": "month_of_birth", "transform": "month_from_date",
         "default": 1, "allow_null": True},
        {"source": "birthDate", "target": "day_of_birth", "transform": "day_from_date",
         "default": 1, "allow_null": True},
        {
            "source": "gender",
            "target": "gender_concept_id",
            "transform": "map",
            "params": {
                "mapping": {"male": 8507, "female": 8532, "other": 8521, "unknown": 8551},
                "default": 8551,
            },
            "default": 8551,
            "allow_null": True,
        },
        {"source": "gender", "target": "gender_source_value", "transform": "direct",
         "default": "unknown", "allow_null": True},
        {
            "source": None,
            "target": "race_concept_id",
            "transform": "constant",
            "params": {"value": 0},
            "default": 0,
            "allow_null": True,
        },
        {
            "source": None,
            "target": "ethnicity_concept_id",
            "transform": "constant",
            "params": {"value": 0},
            "default": 0,
            "allow_null": True,
        },
    ]

    return MappingTemplate(
        template_id="patient-to-person",
        name="Patient → Person",
        description="Maps FHIR R4 Patient resource to OMOP CDM v5.4 PERSON table. "
        "Extracts demographics, maps gender via Athena vocabulary.",
        source_resource=FHIRResourceType.PATIENT,
        target_table=OMOPTable.PERSON,
        field_mappings=field_mappings,
        whistle_code=_build_whistle_code(whistle_rules),
        version="1.0.0",
    )


def build_encounter_to_visit_template() -> MappingTemplate:
    """Encounter → VISIT_OCCURRENCE mapping template."""
    field_mappings = (
        FieldMapping(
            source_path="id",
            target_column="visit_source_value",
            transformation=TransformationType.DIRECT,
        ),
        FieldMapping(
            source_path="period.start",
            target_column="visit_start_date",
            transformation=TransformationType.DIRECT,
        ),
        FieldMapping(
            source_path="period.end",
            target_column="visit_end_date",
            transformation=TransformationType.DIRECT,
        ),
        FieldMapping(
            source_path="class.code",
            target_column="visit_concept_id",
            transformation=TransformationType.VOCABULARY_LOOKUP,
            parameters=(("vocabulary", "Visit"),),
        ),
    )

    whistle_rules = [
        {"source": "subject.reference", "target": "person_id", "transform": "reference_to_person_id",
         "default": 0, "allow_null": True},
        {"source": "id", "target": "visit_source_value", "transform": "direct"},
        {"source": "period.start", "target": "visit_start_date", "transform": "direct",
         "default": "1970-01-01", "allow_null": True},
        {"source": "period.end", "target": "visit_end_date", "transform": "direct",
         "default": "1970-01-01", "allow_null": True},
        {
            "source": "class.code",
            "target": "visit_concept_id",
            "transform": "map",
            "params": {
                "mapping": {
                    "IMP": 9201,    # Inpatient
                    "AMB": 9202,    # Outpatient
                    "EMER": 9203,   # Emergency
                    "SS": 9202,     # Short Stay → Outpatient
                    "HH": 581476,   # Home Health
                },
                "default": 9202,
            },
            "default": 9202,
            "allow_null": True,
        },
        {
            "source": None,
            "target": "visit_type_concept_id",
            "transform": "constant",
            "params": {"value": 32817},  # EHR
            "default": 32817,
            "allow_null": True,
        },
    ]

    return MappingTemplate(
        template_id="encounter-to-visit",
        name="Encounter → Visit Occurrence",
        description="Maps FHIR R4 Encounter resource to OMOP CDM v5.4 VISIT_OCCURRENCE table. "
        "Maps encounter class to visit concept (inpatient/outpatient/ER).",
        source_resource=FHIRResourceType.ENCOUNTER,
        target_table=OMOPTable.VISIT_OCCURRENCE,
        field_mappings=field_mappings,
        whistle_code=_build_whistle_code(whistle_rules),
        version="1.0.0",
    )


def build_condition_to_condition_occurrence_template() -> MappingTemplate:
    """Condition → CONDITION_OCCURRENCE mapping template."""
    field_mappings = (
        FieldMapping(
            source_path="code.coding[0].code",
            target_column="condition_source_value",
            transformation=TransformationType.DIRECT,
        ),
        FieldMapping(
            source_path="code.coding[0].code",
            target_column="condition_concept_id",
            transformation=TransformationType.VOCABULARY_LOOKUP,
            parameters=(("vocabulary", "SNOMED"),),
        ),
        FieldMapping(
            source_path="onsetDateTime",
            target_column="condition_start_date",
            transformation=TransformationType.DIRECT,
        ),
    )

    whistle_rules = [
        {"source": "subject.reference", "target": "person_id", "transform": "reference_to_person_id",
         "default": 0, "allow_null": True},
        {"source": "code.coding[0].code", "target": "condition_source_value", "transform": "direct",
         "default": "unknown", "allow_null": True},
        {
            "source": "code.coding[0].code",
            "target": "condition_concept_id",
            "transform": "vocabulary_lookup",
            "params": {"vocabulary": "SNOMED"},
            "default": 0,
            "allow_null": True,
        },
        {"source": "onsetDateTime", "target": "condition_start_date", "transform": "direct",
         "default": "1970-01-01", "allow_null": True},
        {
            "source": None,
            "target": "condition_type_concept_id",
            "transform": "constant",
            "params": {"value": 32817},  # EHR
            "default": 32817,
            "allow_null": True,
        },
    ]

    return MappingTemplate(
        template_id="condition-to-condition-occurrence",
        name="Condition → Condition Occurrence",
        description="Maps FHIR R4 Condition resource to OMOP CDM v5.4 CONDITION_OCCURRENCE table. "
        "Maps condition codes via SNOMED→OMOP vocabulary lookup.",
        source_resource=FHIRResourceType.CONDITION,
        target_table=OMOPTable.CONDITION_OCCURRENCE,
        field_mappings=field_mappings,
        whistle_code=_build_whistle_code(whistle_rules),
        version="1.0.0",
    )


def build_observation_to_measurement_template() -> MappingTemplate:
    """Observation → MEASUREMENT mapping template (for LOINC-domain observations)."""
    field_mappings = (
        FieldMapping(
            source_path="code.coding[0].code",
            target_column="measurement_source_value",
            transformation=TransformationType.DIRECT,
        ),
        FieldMapping(
            source_path="code.coding[0].code",
            target_column="measurement_concept_id",
            transformation=TransformationType.VOCABULARY_LOOKUP,
            parameters=(("vocabulary", "LOINC"),),
        ),
        FieldMapping(
            source_path="effectiveDateTime",
            target_column="measurement_date",
            transformation=TransformationType.DIRECT,
        ),
        FieldMapping(
            source_path="valueQuantity.value",
            target_column="value_as_number",
            transformation=TransformationType.DIRECT,
        ),
    )

    whistle_rules = [
        {"source": "subject.reference", "target": "person_id", "transform": "reference_to_person_id",
         "default": 0, "allow_null": True},
        {"source": "code.coding[0].code", "target": "measurement_source_value", "transform": "direct",
         "default": "unknown", "allow_null": True},
        {
            "source": "code.coding[0].code",
            "target": "measurement_concept_id",
            "transform": "vocabulary_lookup",
            "params": {"vocabulary": "LOINC"},
            "default": 0,
            "allow_null": True,
        },
        {"source": "effectiveDateTime", "target": "measurement_date", "transform": "direct",
         "default": "1970-01-01", "allow_null": True},
        {"source": "valueQuantity.value", "target": "value_as_number", "transform": "direct",
         "default": 0, "allow_null": True},
        {"source": "valueQuantity.unit", "target": "unit_source_value", "transform": "direct",
         "default": "", "allow_null": True},
        {
            "source": None,
            "target": "measurement_type_concept_id",
            "transform": "constant",
            "params": {"value": 32817},  # EHR
            "default": 32817,
            "allow_null": True,
        },
        {
            "source": None,
            "target": "unit_concept_id",
            "transform": "constant",
            "params": {"value": 0},
            "default": 0,
            "allow_null": True,
        },
    ]

    return MappingTemplate(
        template_id="observation-to-measurement",
        name="Observation → Measurement",
        description="Maps FHIR R4 Observation resource to OMOP CDM v5.4 MEASUREMENT table. "
        "Handles LOINC-coded lab observations with quantity values.",
        source_resource=FHIRResourceType.OBSERVATION,
        target_table=OMOPTable.MEASUREMENT,
        field_mappings=field_mappings,
        whistle_code=_build_whistle_code(whistle_rules),
        version="1.0.0",
    )


def load_all_templates() -> dict[str, MappingTemplate]:
    """Load all Phase 1 mapping templates."""
    templates = [
        build_patient_to_person_template(),
        build_encounter_to_visit_template(),
        build_condition_to_condition_occurrence_template(),
        build_observation_to_measurement_template(),
    ]
    return {t.template_id: t for t in templates}
