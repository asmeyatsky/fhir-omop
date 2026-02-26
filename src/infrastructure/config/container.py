"""
Dependency Injection Container (Composition Root)

Architectural Intent:
- Wires all ports to their infrastructure implementations
- Single place where infrastructure meets domain
- Configurable via environment for dev/test/prod
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from src.application.commands.create_mapping import CreateMappingFromTemplateUseCase
from src.application.commands.create_source_connection import CreateSourceConnectionUseCase
from src.application.commands.execute_pipeline import ExecutePipelineUseCase
from src.application.commands.verify_source_connection import VerifySourceConnectionUseCase
from src.application.queries.get_pipeline import (
    GetPipelineQuery,
    ListMappingConfigsQuery,
    ListMappingTemplatesQuery,
    ListPipelinesQuery,
    ListSourceConnectionsQuery,
)
from src.domain.services.mapping_service import MappingDomainService
from src.domain.services.vocabulary_service import VocabularyDomainService
from src.domain.value_objects.mapping import MappingTemplate
from src.infrastructure.adapters.fhir.hapi_fhir_client import HAPIFHIRClient
from src.infrastructure.adapters.omop.postgresql_writer import PostgreSQLOMOPWriter
from src.infrastructure.adapters.vocabulary.athena_vocabulary_service import AthenaVocabularyService
from src.infrastructure.adapters.whistle.whistle_engine import WhistleEngine
from src.infrastructure.repositories.in_memory import (
    InMemoryEventBus,
    InMemoryMappingConfigRepository,
    InMemoryPipelineRepository,
    InMemorySourceConnectionRepository,
)


@dataclass
class AppContainer:
    """Application dependency container. Holds all wired-up services."""

    # Repositories
    source_repo: InMemorySourceConnectionRepository = field(
        default_factory=InMemorySourceConnectionRepository
    )
    mapping_repo: InMemoryMappingConfigRepository = field(
        default_factory=InMemoryMappingConfigRepository
    )
    pipeline_repo: InMemoryPipelineRepository = field(
        default_factory=InMemoryPipelineRepository
    )
    event_bus: InMemoryEventBus = field(default_factory=InMemoryEventBus)

    # Infrastructure adapters
    fhir_client: HAPIFHIRClient = field(default_factory=HAPIFHIRClient)
    whistle_engine: WhistleEngine = field(default_factory=WhistleEngine)

    # Templates (populated during init)
    templates: dict[str, MappingTemplate] = field(default_factory=dict)

    def _get_omop_connection_string(self) -> str:
        return os.environ.get(
            "OMOP_DATABASE_URL",
            "postgresql://localhost:5432/omop",
        )

    def _get_vocab_connection_string(self) -> str:
        return os.environ.get(
            "VOCAB_DATABASE_URL",
            "postgresql://localhost:5432/omop",
        )

    # --- Use Cases ---

    def create_source_connection_use_case(self) -> CreateSourceConnectionUseCase:
        return CreateSourceConnectionUseCase(
            repository=self.source_repo,
            event_bus=self.event_bus,
        )

    def test_source_connection_use_case(self) -> VerifySourceConnectionUseCase:
        return VerifySourceConnectionUseCase(
            repository=self.source_repo,
            fhir_client=self.fhir_client,
            event_bus=self.event_bus,
        )

    def create_mapping_use_case(self) -> CreateMappingFromTemplateUseCase:
        return CreateMappingFromTemplateUseCase(
            repository=self.mapping_repo,
            templates=self.templates,
        )

    def execute_pipeline_use_case(self) -> ExecutePipelineUseCase:
        vocab_service = AthenaVocabularyService(self._get_vocab_connection_string())
        vocabulary_domain_service = VocabularyDomainService(vocab_service)
        mapping_service = MappingDomainService(
            whistle_engine=self.whistle_engine,
            vocabulary_service=vocabulary_domain_service,
        )
        omop_writer = PostgreSQLOMOPWriter(self._get_omop_connection_string())
        return ExecutePipelineUseCase(
            pipeline_repo=self.pipeline_repo,
            source_repo=self.source_repo,
            mapping_repo=self.mapping_repo,
            fhir_client=self.fhir_client,
            mapping_service=mapping_service,
            omop_writer=omop_writer,
            event_bus=self.event_bus,
        )

    # --- Queries ---

    def list_source_connections_query(self) -> ListSourceConnectionsQuery:
        return ListSourceConnectionsQuery(self.source_repo)

    def list_mapping_configs_query(self) -> ListMappingConfigsQuery:
        return ListMappingConfigsQuery(self.mapping_repo)

    def list_mapping_templates_query(self) -> ListMappingTemplatesQuery:
        return ListMappingTemplatesQuery(self.templates)

    def get_pipeline_query(self) -> GetPipelineQuery:
        return GetPipelineQuery(self.pipeline_repo)

    def list_pipelines_query(self) -> ListPipelinesQuery:
        return ListPipelinesQuery(self.pipeline_repo)
