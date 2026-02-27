"""Tests for NPHIES Service."""
from src.domain.services.nphies_service import NPHIESService
from src.domain.value_objects.nphies import (
    NPHIES_PROFILES,
    NPHIESValidationSeverity,
)


class TestNPHIESProfiles:
    def test_profiles_defined(self):
        assert "Patient" in NPHIES_PROFILES
        assert "Encounter" in NPHIES_PROFILES
        assert "Condition" in NPHIES_PROFILES
        assert "Observation" in NPHIES_PROFILES

    def test_profile_url_format(self):
        for rtype, url in NPHIES_PROFILES.items():
            assert "nphies.sa" in url
            assert rtype.lower() in url.lower()


class TestNPHIESValidation:
    def setup_method(self):
        self.service = NPHIESService()

    def test_valid_patient(self):
        patient = {
            "resourceType": "Patient",
            "id": "p-001",
            "identifier": [
                {"system": "http://nphies.sa/identifier/nationalid", "value": "1234567890"}
            ],
            "name": [{"family": "Al-Rashid", "given": ["Ahmed"]}],
            "gender": "male",
        }
        result = self.service.validate(patient)
        assert result.is_valid is True
        assert result.error_count == 0

    def test_patient_missing_identifier(self):
        patient = {
            "resourceType": "Patient",
            "id": "p-002",
            "name": [{"family": "Test"}],
        }
        result = self.service.validate(patient)
        assert result.is_valid is False
        assert result.error_count >= 1
        error_fields = [i.field for i in result.issues if i.severity == NPHIESValidationSeverity.ERROR]
        assert "identifier" in error_fields

    def test_patient_missing_name(self):
        patient = {
            "resourceType": "Patient",
            "id": "p-003",
            "identifier": [{"system": "http://example.com", "value": "123"}],
        }
        result = self.service.validate(patient)
        assert result.is_valid is False

    def test_patient_non_nphies_identifier_warns(self):
        patient = {
            "resourceType": "Patient",
            "id": "p-004",
            "identifier": [{"system": "http://hospital.local/mrn", "value": "MRN123"}],
            "name": [{"family": "Test"}],
            "gender": "female",
        }
        result = self.service.validate(patient)
        assert result.is_valid is True  # Warning, not error
        assert result.warning_count >= 1

    def test_valid_encounter(self):
        encounter = {
            "resourceType": "Encounter",
            "id": "e-001",
            "status": "finished",
            "class": {"code": "AMB"},
            "subject": {"reference": "Patient/p-001"},
        }
        result = self.service.validate(encounter)
        assert result.is_valid is True

    def test_encounter_missing_status(self):
        encounter = {
            "resourceType": "Encounter",
            "id": "e-002",
            "class": {"code": "AMB"},
            "subject": {"reference": "Patient/p-001"},
        }
        result = self.service.validate(encounter)
        assert result.is_valid is False

    def test_valid_condition(self):
        condition = {
            "resourceType": "Condition",
            "id": "c-001",
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]},
            "subject": {"reference": "Patient/p-001"},
        }
        result = self.service.validate(condition)
        assert result.is_valid is True

    def test_condition_missing_code(self):
        condition = {
            "resourceType": "Condition",
            "id": "c-002",
            "subject": {"reference": "Patient/p-001"},
        }
        result = self.service.validate(condition)
        assert result.is_valid is False

    def test_unknown_resource_type(self):
        resource = {"resourceType": "MedicationRequest", "id": "m-001"}
        result = self.service.validate(resource)
        assert result.warning_count >= 1


class TestNPHIESEnrichment:
    def setup_method(self):
        self.service = NPHIESService()

    def test_enrich_adds_profile(self):
        patient = {"resourceType": "Patient", "id": "p-001"}
        enriched = self.service.enrich(patient)
        assert "meta" in enriched
        assert NPHIES_PROFILES["Patient"] in enriched["meta"]["profile"]

    def test_enrich_preserves_existing_meta(self):
        patient = {
            "resourceType": "Patient",
            "id": "p-001",
            "meta": {"versionId": "1"},
        }
        enriched = self.service.enrich(patient)
        assert enriched["meta"]["versionId"] == "1"
        assert NPHIES_PROFILES["Patient"] in enriched["meta"]["profile"]

    def test_enrich_no_duplicate_profiles(self):
        patient = {
            "resourceType": "Patient",
            "id": "p-001",
            "meta": {"profile": [NPHIES_PROFILES["Patient"]]},
        }
        enriched = self.service.enrich(patient)
        assert enriched["meta"]["profile"].count(NPHIES_PROFILES["Patient"]) == 1

    def test_enrich_unknown_resource(self):
        resource = {"resourceType": "Unknown", "id": "x-001"}
        enriched = self.service.enrich(resource)
        # No profile to add for unknown types
        assert "meta" not in enriched or "profile" not in enriched.get("meta", {})

    def test_enrich_does_not_modify_original(self):
        patient = {"resourceType": "Patient", "id": "p-001"}
        self.service.enrich(patient)
        assert "meta" not in patient  # Original unchanged

    def test_validation_result_properties(self):
        patient = {
            "resourceType": "Patient", "id": "p-005",
        }
        result = self.service.validate(patient)
        assert result.resource_type == "Patient"
        assert result.resource_id == "p-005"
