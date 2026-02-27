"""Tests for Data Classification (NDMO)."""
from src.domain.services.classification_service import ClassificationService
from src.domain.value_objects.classification import (
    ClassificationPolicy,
    DataClassification,
    DEFAULT_POLICIES,
)


class TestDataClassificationEnum:
    def test_sensitivity_ordering(self):
        assert DataClassification.PUBLIC < DataClassification.INTERNAL
        assert DataClassification.INTERNAL < DataClassification.CONFIDENTIAL
        assert DataClassification.CONFIDENTIAL < DataClassification.TOP_SECRET

    def test_sensitivity_levels(self):
        assert DataClassification.PUBLIC.sensitivity_level == 0
        assert DataClassification.TOP_SECRET.sensitivity_level == 3

    def test_comparison_operators(self):
        assert DataClassification.TOP_SECRET >= DataClassification.CONFIDENTIAL
        assert DataClassification.PUBLIC <= DataClassification.INTERNAL
        assert not DataClassification.PUBLIC > DataClassification.INTERNAL


class TestClassificationPolicies:
    def test_default_policies_exist(self):
        assert len(DEFAULT_POLICIES) >= 10

    def test_patient_identifiers_top_secret(self):
        patient_id_policy = next(
            p for p in DEFAULT_POLICIES if p.name == "Patient Identifiers"
        )
        assert patient_id_policy.classification == DataClassification.TOP_SECRET
        assert patient_id_policy.resource_type == "Patient"

    def test_conditions_confidential(self):
        condition_policy = next(
            p for p in DEFAULT_POLICIES if p.name == "Conditions"
        )
        assert condition_policy.classification == DataClassification.CONFIDENTIAL

    def test_value_sets_public(self):
        vs_policy = next(
            p for p in DEFAULT_POLICIES if p.name == "Value Sets"
        )
        assert vs_policy.classification == DataClassification.PUBLIC


class TestClassificationService:
    def setup_method(self):
        self.service = ClassificationService()

    def test_classify_patient_resource(self):
        patient = {
            "resourceType": "Patient",
            "identifier": [{"system": "urn:oid:2.16.840.1", "value": "12345"}],
            "name": [{"family": "Al-Rashid", "given": ["Ahmed"]}],
            "telecom": [{"system": "phone", "value": "+966-555-1234"}],
        }
        result = self.service.classify_resource("Patient", patient)
        assert result == DataClassification.TOP_SECRET

    def test_classify_condition_resource(self):
        condition = {
            "resourceType": "Condition",
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]},
            "subject": {"reference": "Patient/123"},
        }
        result = self.service.classify_resource("Condition", condition)
        assert result == DataClassification.CONFIDENTIAL

    def test_classify_valueset_resource(self):
        valueset = {
            "resourceType": "ValueSet",
            "name": "MaritalStatus",
            "status": "active",
        }
        result = self.service.classify_resource("ValueSet", valueset)
        assert result == DataClassification.PUBLIC

    def test_classify_field_patient_identifier(self):
        result = self.service.classify_field("Patient", "identifier.value")
        assert result == DataClassification.TOP_SECRET

    def test_classify_field_metadata(self):
        result = self.service.classify_field("Patient", "meta.versionId")
        assert result == DataClassification.INTERNAL

    def test_classify_person_source_value(self):
        result = self.service.classify_field("*", "person_source_value")
        assert result == DataClassification.TOP_SECRET

    def test_get_sensitive_fields(self):
        fields = self.service.get_sensitive_fields("Patient")
        assert "identifier.*" in fields
        assert "name.*" in fields
        assert "telecom.*" in fields

    def test_get_policies(self):
        policies = self.service.get_policies()
        assert len(policies) == len(DEFAULT_POLICIES)

    def test_custom_policies(self):
        custom = (
            ClassificationPolicy(
                id="custom-1", name="Custom", resource_type="CustomResource",
                field_pattern="*", classification=DataClassification.INTERNAL,
            ),
        )
        service = ClassificationService(policies=custom)
        result = service.classify_resource("CustomResource", {"field": "value"})
        assert result == DataClassification.INTERNAL

    def test_unknown_resource_defaults_public(self):
        result = self.service.classify_resource("UnknownType", {"foo": "bar"})
        assert result == DataClassification.PUBLIC
