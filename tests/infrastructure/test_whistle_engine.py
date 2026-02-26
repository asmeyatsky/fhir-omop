"""
Infrastructure Tests: Whistle Engine

Tests the Whistle-compatible transformation engine with actual mapping templates.
"""
import json

import pytest

from src.infrastructure.adapters.whistle.whistle_engine import WhistleEngine
from src.infrastructure.templates.registry import load_all_templates


class TestWhistleEngine:
    @pytest.fixture
    def engine(self):
        return WhistleEngine()

    @pytest.mark.asyncio
    async def test_patient_to_person_transform(self, engine):
        templates = load_all_templates()
        whistle_code = templates["patient-to-person"].whistle_code

        patient = {
            "id": "pat-123",
            "resourceType": "Patient",
            "identifier": [{"value": "MRN-001"}],
            "birthDate": "1990-05-15",
            "gender": "male",
        }

        result = await engine.execute(whistle_code, patient)

        assert result is not None
        assert result["person_source_value"] == "MRN-001"
        assert result["year_of_birth"] == 1990
        assert result["month_of_birth"] == 5
        assert result["day_of_birth"] == 15
        assert result["gender_concept_id"] == 8507  # male
        assert result["gender_source_value"] == "male"
        assert result["race_concept_id"] == 0
        assert result["ethnicity_concept_id"] == 0

    @pytest.mark.asyncio
    async def test_patient_female_gender(self, engine):
        templates = load_all_templates()
        whistle_code = templates["patient-to-person"].whistle_code

        patient = {
            "id": "pat-456",
            "identifier": [{"value": "MRN-002"}],
            "birthDate": "1985-11-20",
            "gender": "female",
        }

        result = await engine.execute(whistle_code, patient)
        assert result["gender_concept_id"] == 8532  # female

    @pytest.mark.asyncio
    async def test_encounter_to_visit_transform(self, engine):
        templates = load_all_templates()
        whistle_code = templates["encounter-to-visit"].whistle_code

        encounter = {
            "id": "enc-789",
            "resourceType": "Encounter",
            "period": {
                "start": "2024-01-15T09:00:00Z",
                "end": "2024-01-15T17:00:00Z",
            },
            "class": {"code": "AMB"},
        }

        result = await engine.execute(whistle_code, encounter)

        assert result is not None
        assert result["visit_source_value"] == "enc-789"
        assert result["visit_start_date"] == "2024-01-15T09:00:00Z"
        assert result["visit_end_date"] == "2024-01-15T17:00:00Z"
        assert result["visit_concept_id"] == 9202  # Outpatient
        assert result["visit_type_concept_id"] == 32817  # EHR

    @pytest.mark.asyncio
    async def test_encounter_inpatient(self, engine):
        templates = load_all_templates()
        whistle_code = templates["encounter-to-visit"].whistle_code

        encounter = {
            "id": "enc-inpatient",
            "period": {"start": "2024-01-10", "end": "2024-01-15"},
            "class": {"code": "IMP"},
        }

        result = await engine.execute(whistle_code, encounter)
        assert result["visit_concept_id"] == 9201  # Inpatient

    @pytest.mark.asyncio
    async def test_condition_transform(self, engine):
        templates = load_all_templates()
        whistle_code = templates["condition-to-condition-occurrence"].whistle_code

        condition = {
            "id": "cond-001",
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]},
            "onsetDateTime": "2024-03-01",
        }

        result = await engine.execute(whistle_code, condition)

        assert result is not None
        assert result["condition_source_value"] == "38341003"
        assert result["condition_start_date"] == "2024-03-01"
        assert result["condition_type_concept_id"] == 32817

    @pytest.mark.asyncio
    async def test_observation_to_measurement_transform(self, engine):
        templates = load_all_templates()
        whistle_code = templates["observation-to-measurement"].whistle_code

        observation = {
            "id": "obs-001",
            "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
            "effectiveDateTime": "2024-02-15T10:30:00Z",
            "valueQuantity": {"value": 72, "unit": "beats/minute"},
        }

        result = await engine.execute(whistle_code, observation)

        assert result is not None
        assert result["measurement_source_value"] == "8867-4"
        assert result["measurement_date"] == "2024-02-15T10:30:00Z"
        assert result["value_as_number"] == 72
        assert result["unit_source_value"] == "beats/minute"
        assert result["measurement_type_concept_id"] == 32817

    @pytest.mark.asyncio
    async def test_validate_valid_code(self, engine):
        code = json.dumps({"mappings": [{"source": "id", "target": "person_id"}]})
        valid, errors = await engine.validate_code(code)
        assert valid is True
        assert errors == []

    @pytest.mark.asyncio
    async def test_validate_invalid_json(self, engine):
        valid, errors = await engine.validate_code("not json")
        assert valid is False
        assert len(errors) == 1

    @pytest.mark.asyncio
    async def test_validate_missing_mappings_key(self, engine):
        valid, errors = await engine.validate_code('{"rules": []}')
        assert valid is False

    @pytest.mark.asyncio
    async def test_execute_with_empty_resource(self, engine):
        code = json.dumps({"mappings": [{"source": "id", "target": "person_id"}]})
        result = await engine.execute(code, {})
        assert result is None  # No fields matched → None
