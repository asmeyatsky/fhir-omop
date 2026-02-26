"""
Application Layer Tests: Mapping Use Cases
"""
import pytest

from src.application.commands.create_mapping import CreateMappingFromTemplateUseCase
from src.application.dtos.mapping_dtos import CreateMappingFromTemplateDTO
from src.infrastructure.repositories.in_memory import InMemoryMappingConfigRepository
from src.infrastructure.templates.registry import load_all_templates


class TestCreateMappingFromTemplateUseCase:
    @pytest.mark.asyncio
    async def test_create_from_patient_template(self):
        repo = InMemoryMappingConfigRepository()
        templates = load_all_templates()
        use_case = CreateMappingFromTemplateUseCase(repository=repo, templates=templates)

        result = await use_case.execute(
            CreateMappingFromTemplateDTO(
                name="My Patient Mapping",
                template_id="patient-to-person",
            )
        )

        assert result.name == "My Patient Mapping"
        assert result.source_resource == "Patient"
        assert result.target_table == "person"
        assert result.status == "active"
        assert result.template_id == "patient-to-person"
        assert result.field_count > 0

    @pytest.mark.asyncio
    async def test_create_from_encounter_template(self):
        repo = InMemoryMappingConfigRepository()
        templates = load_all_templates()
        use_case = CreateMappingFromTemplateUseCase(repository=repo, templates=templates)

        result = await use_case.execute(
            CreateMappingFromTemplateDTO(
                name="Encounter Mapping",
                template_id="encounter-to-visit",
            )
        )

        assert result.source_resource == "Encounter"
        assert result.target_table == "visit_occurrence"

    @pytest.mark.asyncio
    async def test_create_from_condition_template(self):
        repo = InMemoryMappingConfigRepository()
        templates = load_all_templates()
        use_case = CreateMappingFromTemplateUseCase(repository=repo, templates=templates)

        result = await use_case.execute(
            CreateMappingFromTemplateDTO(
                name="Condition Mapping",
                template_id="condition-to-condition-occurrence",
            )
        )

        assert result.source_resource == "Condition"
        assert result.target_table == "condition_occurrence"

    @pytest.mark.asyncio
    async def test_create_from_observation_template(self):
        repo = InMemoryMappingConfigRepository()
        templates = load_all_templates()
        use_case = CreateMappingFromTemplateUseCase(repository=repo, templates=templates)

        result = await use_case.execute(
            CreateMappingFromTemplateDTO(
                name="Observation Mapping",
                template_id="observation-to-measurement",
            )
        )

        assert result.source_resource == "Observation"
        assert result.target_table == "measurement"

    @pytest.mark.asyncio
    async def test_invalid_template_raises(self):
        repo = InMemoryMappingConfigRepository()
        templates = load_all_templates()
        use_case = CreateMappingFromTemplateUseCase(repository=repo, templates=templates)

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(
                CreateMappingFromTemplateDTO(
                    name="Bad",
                    template_id="nonexistent-template",
                )
            )
