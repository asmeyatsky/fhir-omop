"""
Application Layer Tests: Pipeline Execution Use Case

Tests the full pipeline orchestration with mocked infrastructure ports.
"""
import pytest

from src.application.commands.create_mapping import CreateMappingFromTemplateUseCase
from src.application.commands.create_source_connection import CreateSourceConnectionUseCase
from src.application.commands.execute_pipeline import ExecutePipelineUseCase
from src.application.commands.verify_source_connection import VerifySourceConnectionUseCase
from src.application.dtos.mapping_dtos import CreateMappingFromTemplateDTO
from src.application.dtos.pipeline_dtos import CreatePipelineDTO
from src.application.dtos.source_dtos import CreateSourceConnectionDTO
from src.domain.services.mapping_service import MappingDomainService
from src.domain.services.vocabulary_service import VocabularyDomainService
from src.domain.value_objects.fhir import AuthMethod, FHIRBundle, FHIRResourceType, FHIRServerType
from src.domain.value_objects.omop import ConceptId, OMOPRecord
from src.infrastructure.repositories.in_memory import (
    InMemoryEventBus,
    InMemoryMappingConfigRepository,
    InMemoryPipelineRepository,
    InMemorySourceConnectionRepository,
)
from src.infrastructure.templates.registry import load_all_templates


class MockFHIRClient:
    async def test_connection(self, endpoint):
        return True, "OK"

    async def get_capability_statement(self, endpoint):
        return {"fhirVersion": "4.0.1"}

    async def get_supported_resources(self, endpoint):
        return ["Patient", "Encounter"]

    async def extract_resources(self, endpoint, resource_type, batch_size=1000):
        if resource_type == FHIRResourceType.PATIENT:
            return FHIRBundle(
                resource_type=FHIRResourceType.PATIENT,
                resources=(
                    {
                        "id": "pat-1",
                        "resourceType": "Patient",
                        "identifier": [{"value": "MRN-001"}],
                        "birthDate": "1990-05-15",
                        "gender": "male",
                    },
                    {
                        "id": "pat-2",
                        "resourceType": "Patient",
                        "identifier": [{"value": "MRN-002"}],
                        "birthDate": "1985-11-20",
                        "gender": "female",
                    },
                ),
            )
        return FHIRBundle(resource_type=resource_type, resources=())


class MockWhistleEngine:
    async def execute(self, whistle_code, input_resource):
        import json
        rules = json.loads(whistle_code)
        output = {}
        for rule in rules.get("mappings", []):
            target = rule["target"]
            source = rule.get("source")
            transform = rule.get("transform", "direct")
            params = rule.get("params", {})

            if source is None:
                if rule.get("default") is not None:
                    output[target] = rule["default"]
                elif transform == "constant":
                    output[target] = params.get("value")
                continue

            # Simple dot-path extraction
            val = input_resource
            for part in source.split("."):
                if "[" in part:
                    key = part.split("[")[0]
                    idx = int(part.split("[")[1].rstrip("]"))
                    val = val.get(key, [])
                    val = val[idx] if idx < len(val) else None
                elif isinstance(val, dict):
                    val = val.get(part)
                else:
                    val = None
                if val is None:
                    break

            if val is not None:
                if transform == "year_from_date" and isinstance(val, str):
                    output[target] = int(val[:4])
                elif transform == "month_from_date" and isinstance(val, str):
                    output[target] = int(val[5:7])
                elif transform == "day_from_date" and isinstance(val, str):
                    output[target] = int(val[8:10])
                elif transform == "map":
                    mapping = params.get("mapping", {})
                    output[target] = mapping.get(str(val), params.get("default", 0))
                else:
                    output[target] = val

        return output if output else None

    async def validate_code(self, whistle_code):
        return True, []


class MockVocabularyLookup:
    async def find_standard_concept(self, source_code, source_vocabulary_id):
        return ConceptId(concept_id=0, concept_name="", vocabulary_id="", domain_id="")

    async def search_concepts(self, query, vocabulary_id=None, domain_id=None, limit=20):
        return []


class MockOMOPWriter:
    def __init__(self):
        self.written_records: list = []

    async def write_records(self, records):
        self.written_records.extend(records)
        return len(records)

    async def validate_schema(self):
        return True, []

    async def test_connection(self):
        return True, "OK"

    async def get_record_count(self, table):
        return len(self.written_records)


class TestExecutePipelineUseCase:
    async def _setup(self):
        source_repo = InMemorySourceConnectionRepository()
        mapping_repo = InMemoryMappingConfigRepository()
        pipeline_repo = InMemoryPipelineRepository()
        event_bus = InMemoryEventBus()
        fhir_client = MockFHIRClient()
        whistle_engine = MockWhistleEngine()
        vocab_lookup = MockVocabularyLookup()
        omop_writer = MockOMOPWriter()

        vocab_service = VocabularyDomainService(vocab_lookup)
        mapping_service = MappingDomainService(whistle_engine, vocab_service)

        templates = load_all_templates()

        # Create source connection
        create_src = CreateSourceConnectionUseCase(source_repo, event_bus)
        src = await create_src.execute(CreateSourceConnectionDTO(
            name="Test Server", base_url="https://test.fhir.org",
            server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
        ))

        # Test it to make it active
        test_src = VerifySourceConnectionUseCase(source_repo, fhir_client, event_bus)
        src = await test_src.execute(src.id)
        assert src.status == "active"

        # Create mapping from template
        create_map = CreateMappingFromTemplateUseCase(mapping_repo, templates)
        mapping = await create_map.execute(CreateMappingFromTemplateDTO(
            name="Patient Mapping", template_id="patient-to-person",
        ))

        use_case = ExecutePipelineUseCase(
            pipeline_repo=pipeline_repo,
            source_repo=source_repo,
            mapping_repo=mapping_repo,
            fhir_client=fhir_client,
            mapping_service=mapping_service,
            omop_writer=omop_writer,
            event_bus=event_bus,
        )

        return use_case, src, mapping, omop_writer, event_bus

    @pytest.mark.asyncio
    async def test_successful_pipeline_execution(self):
        use_case, src, mapping, writer, event_bus = await self._setup()

        result = await use_case.execute(CreatePipelineDTO(
            name="Patient ETL",
            source_connection_id=src.id,
            mapping_config_ids=[mapping.id],
            target_connection_string="postgresql://localhost/omop",
        ))

        assert result.status == "completed"
        assert result.total_records == 2
        assert result.total_errors == 0
        assert len(result.stage_results) == 3
        assert result.stage_results[0].stage == "extract"
        assert result.stage_results[1].stage == "transform"
        assert result.stage_results[2].stage == "load"

        # Verify records written
        assert len(writer.written_records) == 2

    @pytest.mark.asyncio
    async def test_pipeline_with_inactive_source_raises(self):
        source_repo = InMemorySourceConnectionRepository()
        mapping_repo = InMemoryMappingConfigRepository()
        pipeline_repo = InMemoryPipelineRepository()
        event_bus = InMemoryEventBus()

        create_src = CreateSourceConnectionUseCase(source_repo, event_bus)
        src = await create_src.execute(CreateSourceConnectionDTO(
            name="Untested", base_url="https://test.fhir.org",
            server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
        ))

        templates = load_all_templates()
        create_map = CreateMappingFromTemplateUseCase(mapping_repo, templates)
        mapping = await create_map.execute(CreateMappingFromTemplateDTO(
            name="Test", template_id="patient-to-person",
        ))

        use_case = ExecutePipelineUseCase(
            pipeline_repo=pipeline_repo, source_repo=source_repo,
            mapping_repo=mapping_repo, fhir_client=MockFHIRClient(),
            mapping_service=MappingDomainService(MockWhistleEngine(), VocabularyDomainService(MockVocabularyLookup())),
            omop_writer=MockOMOPWriter(), event_bus=event_bus,
        )

        with pytest.raises(ValueError, match="not active"):
            await use_case.execute(CreatePipelineDTO(
                name="Test", source_connection_id=src.id,
                mapping_config_ids=[mapping.id],
                target_connection_string="pg://localhost/omop",
            ))

    @pytest.mark.asyncio
    async def test_pipeline_with_missing_source_raises(self):
        use_case, _, mapping, _, _ = await self._setup()

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(CreatePipelineDTO(
                name="Test", source_connection_id="nonexistent",
                mapping_config_ids=[mapping.id],
                target_connection_string="pg://localhost/omop",
            ))
