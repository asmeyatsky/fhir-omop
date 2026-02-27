"""
Dependency Injection Container (Composition Root)

Architectural Intent:
- Wires all ports to their infrastructure implementations
- Single place where infrastructure meets domain
- Configurable via environment for dev/test/prod
- Supports both in-memory (testing) and PostgreSQL (production) storage
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
from src.infrastructure.adapters.omop.writer_factory import PostgreSQLOMOPWriterFactory
from src.infrastructure.adapters.whistle.whistle_engine import WhistleEngine
from src.infrastructure.config.database import DatabaseManager
from src.infrastructure.repositories.in_memory import (
    InMemoryEventBus,
    InMemoryMappingConfigRepository,
    InMemoryPipelineRepository,
    InMemorySourceConnectionRepository,
    InMemoryTenantRepository,
)


class NoOpVocabularyLookup:
    """Stub vocabulary lookup for Phase 1 — returns None (unmapped) for all codes."""

    async def find_standard_concept(self, source_code: str, source_vocabulary_id: str):
        return None

    async def search_concepts(self, query: str, vocabulary_id=None, domain_id=None, limit=20):
        return []


@dataclass
class AppContainer:
    """Application dependency container. Holds all wired-up services."""

    # Database manager (initialized on startup for PostgreSQL backend)
    db_manager: DatabaseManager | None = None

    # Repositories (set during initialization based on STORAGE_BACKEND)
    source_repo: object = field(default_factory=InMemorySourceConnectionRepository)
    mapping_repo: object = field(default_factory=InMemoryMappingConfigRepository)
    pipeline_repo: object = field(default_factory=InMemoryPipelineRepository)
    event_bus: object = field(default_factory=InMemoryEventBus)
    tenant_repo: object = field(default_factory=InMemoryTenantRepository)

    # Infrastructure adapters
    fhir_client: HAPIFHIRClient = field(default_factory=HAPIFHIRClient)
    whistle_engine: WhistleEngine = field(default_factory=WhistleEngine)
    omop_writer_factory: PostgreSQLOMOPWriterFactory = field(
        default_factory=PostgreSQLOMOPWriterFactory
    )

    # Templates (populated during init)
    templates: dict[str, MappingTemplate] = field(default_factory=dict)

    async def initialize(self) -> None:
        """Initialize the container — sets up database if using PostgreSQL backend."""
        storage_backend = os.environ.get("STORAGE_BACKEND", "postgresql")

        if storage_backend == "postgresql":
            from src.infrastructure.repositories.postgresql_event_bus import PostgreSQLEventBus
            from src.infrastructure.repositories.postgresql_repos import (
                PostgreSQLMappingConfigRepository,
                PostgreSQLPipelineRepository,
                PostgreSQLSourceConnectionRepository,
            )

            self.db_manager = DatabaseManager()
            pool = await self.db_manager.get_pool()
            self.source_repo = PostgreSQLSourceConnectionRepository(pool)
            self.mapping_repo = PostgreSQLMappingConfigRepository(pool)
            self.pipeline_repo = PostgreSQLPipelineRepository(pool)
            self.event_bus = PostgreSQLEventBus(pool)

    async def shutdown(self) -> None:
        """Clean up resources."""
        if self.db_manager:
            await self.db_manager.close()

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
        vocabulary_domain_service = VocabularyDomainService(NoOpVocabularyLookup())
        mapping_service = MappingDomainService(
            whistle_engine=self.whistle_engine,
            vocabulary_service=vocabulary_domain_service,
        )
        return ExecutePipelineUseCase(
            pipeline_repo=self.pipeline_repo,
            source_repo=self.source_repo,
            mapping_repo=self.mapping_repo,
            fhir_client=self.fhir_client,
            mapping_service=mapping_service,
            omop_writer_factory=self.omop_writer_factory,
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
