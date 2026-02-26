"""
Infrastructure Tests: Mapping Template Registry

Verify all Phase 1 templates are properly configured.
"""
import json

from src.domain.value_objects.fhir import FHIRResourceType
from src.domain.value_objects.omop import OMOPTable
from src.infrastructure.templates.registry import load_all_templates


class TestTemplateRegistry:
    def test_loads_four_templates(self):
        templates = load_all_templates()
        assert len(templates) == 4

    def test_patient_template_exists(self):
        templates = load_all_templates()
        t = templates["patient-to-person"]
        assert t.source_resource == FHIRResourceType.PATIENT
        assert t.target_table == OMOPTable.PERSON
        assert t.field_count > 0
        assert t.version == "1.0.0"

    def test_encounter_template_exists(self):
        templates = load_all_templates()
        t = templates["encounter-to-visit"]
        assert t.source_resource == FHIRResourceType.ENCOUNTER
        assert t.target_table == OMOPTable.VISIT_OCCURRENCE

    def test_condition_template_exists(self):
        templates = load_all_templates()
        t = templates["condition-to-condition-occurrence"]
        assert t.source_resource == FHIRResourceType.CONDITION
        assert t.target_table == OMOPTable.CONDITION_OCCURRENCE

    def test_observation_template_exists(self):
        templates = load_all_templates()
        t = templates["observation-to-measurement"]
        assert t.source_resource == FHIRResourceType.OBSERVATION
        assert t.target_table == OMOPTable.MEASUREMENT

    def test_all_templates_have_valid_whistle_code(self):
        templates = load_all_templates()
        for tid, template in templates.items():
            code = json.loads(template.whistle_code)
            assert "mappings" in code, f"Template {tid} missing 'mappings' key"
            assert len(code["mappings"]) > 0, f"Template {tid} has no mapping rules"

    def test_all_templates_have_descriptions(self):
        templates = load_all_templates()
        for tid, template in templates.items():
            assert template.description, f"Template {tid} missing description"
            assert template.name, f"Template {tid} missing name"
