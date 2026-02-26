"""
Query Use Cases

Architectural Intent:
- Read-only operations returning DTOs
- No side effects — pure queries
"""
from __future__ import annotations

from src.application.dtos.mapping_dtos import MappingConfigResponseDTO, MappingTemplateResponseDTO
from src.application.dtos.pipeline_dtos import PipelineResponseDTO, StageResultDTO
from src.application.dtos.source_dtos import SourceConnectionResponseDTO
from src.domain.entities.mapping_config import MappingConfiguration
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.source_connection import SourceConnection
from src.domain.ports.repository_ports import (
    MappingConfigRepositoryPort,
    PipelineRepositoryPort,
    SourceConnectionRepositoryPort,
)
from src.domain.value_objects.mapping import MappingTemplate


class ListSourceConnectionsQuery:
    def __init__(self, repository: SourceConnectionRepositoryPort) -> None:
        self._repository = repository

    async def execute(self) -> list[SourceConnectionResponseDTO]:
        connections = await self._repository.list_all()
        return [self._to_dto(c) for c in connections]

    @staticmethod
    def _to_dto(c: SourceConnection) -> SourceConnectionResponseDTO:
        return SourceConnectionResponseDTO(
            id=c.id,
            name=c.name,
            base_url=c.endpoint.base_url,
            server_type=c.endpoint.server_type.value,
            auth_method=c.endpoint.auth_method.value,
            status=c.status.value,
            created_at=c.created_at,
            last_tested_at=c.last_tested_at,
            capabilities=list(c.capabilities),
            error_message=c.error_message,
        )


class ListMappingConfigsQuery:
    def __init__(self, repository: MappingConfigRepositoryPort) -> None:
        self._repository = repository

    async def execute(self) -> list[MappingConfigResponseDTO]:
        configs = await self._repository.list_all()
        return [self._to_dto(c) for c in configs]

    @staticmethod
    def _to_dto(c: MappingConfiguration) -> MappingConfigResponseDTO:
        return MappingConfigResponseDTO(
            id=c.id,
            name=c.name,
            source_resource=c.source_resource.value,
            target_table=c.target_table.value,
            field_count=len(c.field_mappings),
            status=c.status.value,
            version=c.version,
            template_id=c.template_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )


class ListMappingTemplatesQuery:
    def __init__(self, templates: dict[str, MappingTemplate]) -> None:
        self._templates = templates

    async def execute(self) -> list[MappingTemplateResponseDTO]:
        return [
            MappingTemplateResponseDTO(
                template_id=t.template_id,
                name=t.name,
                description=t.description,
                source_resource=t.source_resource.value,
                target_table=t.target_table.value,
                field_count=t.field_count,
                version=t.version,
            )
            for t in self._templates.values()
        ]


class GetPipelineQuery:
    def __init__(self, repository: PipelineRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, pipeline_id: str) -> PipelineResponseDTO | None:
        p = await self._repository.get_by_id(pipeline_id)
        if p is None:
            return None
        return self._to_dto(p)

    @staticmethod
    def _to_dto(p: Pipeline) -> PipelineResponseDTO:
        return PipelineResponseDTO(
            id=p.id,
            name=p.name,
            source_connection_id=p.source_connection_id,
            mapping_config_ids=list(p.mapping_config_ids),
            status=p.status.value,
            created_at=p.created_at,
            started_at=p.started_at,
            completed_at=p.completed_at,
            current_stage=p.current_stage.value if p.current_stage else None,
            stage_results=[
                StageResultDTO(
                    stage=sr.stage.value,
                    records_in=sr.records_in,
                    records_out=sr.records_out,
                    error_count=sr.error_count,
                    started_at=sr.started_at,
                    completed_at=sr.completed_at,
                )
                for sr in p.stage_results
            ],
            total_records=p.total_records_processed,
            total_errors=p.total_errors,
            error_message=p.error_message,
        )


class ListPipelinesQuery:
    def __init__(self, repository: PipelineRepositoryPort) -> None:
        self._repository = repository

    async def execute(self) -> list[PipelineResponseDTO]:
        pipelines = await self._repository.list_all()
        return [GetPipelineQuery._to_dto(p) for p in pipelines]
