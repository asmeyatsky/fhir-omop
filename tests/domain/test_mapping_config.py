"""
Domain Unit Tests: MappingConfiguration

Pure domain logic tests for mapping configuration entity.
"""
import pytest

from src.domain.entities.mapping_config import MappingConfiguration, MappingStatus
from src.domain.value_objects.fhir import FHIRResourceType
from src.domain.value_objects.mapping import FieldMapping, MappingTemplate, TransformationType
from src.domain.value_objects.omop import OMOPTable


class TestMappingConfiguration:
    def _make_template(self) -> MappingTemplate:
        return MappingTemplate(
            template_id="patient-to-person",
            name="Patient → Person",
            description="Test template",
            source_resource=FHIRResourceType.PATIENT,
            target_table=OMOPTable.PERSON,
            field_mappings=(
                FieldMapping(
                    source_path="gender",
                    target_column="gender_source_value",
                    transformation=TransformationType.DIRECT,
                ),
            ),
            whistle_code='{"mappings": []}',
            version="1.0.0",
        )

    def test_create_from_template(self):
        template = self._make_template()
        config = MappingConfiguration.from_template(
            id="map-1", name="My Patient Mapping", template=template,
        )
        assert config.source_resource == FHIRResourceType.PATIENT
        assert config.target_table == OMOPTable.PERSON
        assert config.template_id == "patient-to-person"
        assert config.status == MappingStatus.VALIDATED
        assert len(config.field_mappings) == 1

    def test_activate_validated_mapping(self):
        template = self._make_template()
        config = MappingConfiguration.from_template(id="1", name="T", template=template)
        active = config.activate()
        assert active.status == MappingStatus.ACTIVE
        assert active.is_active is True

    def test_cannot_activate_draft(self):
        config = MappingConfiguration.create_custom(
            id="1", name="Custom",
            source_resource=FHIRResourceType.PATIENT,
            target_table=OMOPTable.PERSON,
            field_mappings=(
                FieldMapping("gender", "gender_source_value", TransformationType.DIRECT),
            ),
            whistle_code="{}",
        )
        assert config.status == MappingStatus.DRAFT
        with pytest.raises(ValueError, match="Only validated"):
            config.activate()

    def test_validate_then_activate(self):
        config = MappingConfiguration.create_custom(
            id="1", name="Custom",
            source_resource=FHIRResourceType.PATIENT,
            target_table=OMOPTable.PERSON,
            field_mappings=(
                FieldMapping("gender", "gender_source_value", TransformationType.DIRECT),
            ),
            whistle_code="{}",
        )
        validated = config.validate()
        active = validated.activate()
        assert active.is_active

    def test_create_custom_no_mappings_raises(self):
        with pytest.raises(ValueError, match="At least one field mapping"):
            MappingConfiguration.create_custom(
                id="1", name="Empty",
                source_resource=FHIRResourceType.PATIENT,
                target_table=OMOPTable.PERSON,
                field_mappings=(),
                whistle_code="{}",
            )

    def test_add_field_mapping(self):
        template = self._make_template()
        config = MappingConfiguration.from_template(id="1", name="T", template=template)
        new_mapping = FieldMapping("birthDate", "year_of_birth", TransformationType.DATE_EXTRACT)
        updated = config.add_field_mapping(new_mapping)
        assert len(updated.field_mappings) == 2
        assert len(config.field_mappings) == 1  # immutability


class TestValueObjects:
    def test_concept_id_unmapped(self):
        from src.domain.value_objects.omop import ConceptId
        unmapped = ConceptId.unmapped()
        assert unmapped.concept_id == 0
        assert unmapped.is_mapped is False

    def test_concept_id_mapped(self):
        from src.domain.value_objects.omop import ConceptId
        concept = ConceptId(concept_id=8507, concept_name="MALE", vocabulary_id="Gender", domain_id="Gender")
        assert concept.is_mapped is True

    def test_fhir_bundle(self):
        from src.domain.value_objects.fhir import FHIRBundle, FHIRResourceType
        bundle = FHIRBundle(
            resource_type=FHIRResourceType.PATIENT,
            resources=({"id": "1"}, {"id": "2"}),
        )
        assert bundle.count == 2
        assert bundle.is_empty() is False

    def test_fhir_bundle_empty(self):
        from src.domain.value_objects.fhir import FHIRBundle, FHIRResourceType
        bundle = FHIRBundle(resource_type=FHIRResourceType.PATIENT, resources=())
        assert bundle.is_empty() is True

    def test_field_mapping_get_parameter(self):
        fm = FieldMapping(
            source_path="x", target_column="y",
            transformation=TransformationType.VOCABULARY_LOOKUP,
            parameters=(("vocabulary", "SNOMED"), ("fallback", "0")),
        )
        assert fm.get_parameter("vocabulary") == "SNOMED"
        assert fm.get_parameter("missing") is None
