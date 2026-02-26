"""
Execute Pipeline Use Case

Architectural Intent:
- Orchestrates the full extract → transform → load pipeline
- Phase 1: sequential execution
- Delegates each stage to domain services and ports
- Tracks stage-level progress on the Pipeline aggregate

Parallelization Notes:
- Phase 1 is sequential (extract all → transform all → load all)
- Phase 2 will introduce parallel chunked processing via DAG orchestrator
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.application.dtos.pipeline_dtos import CreatePipelineDTO, PipelineResponseDTO, StageResultDTO
from src.domain.entities.pipeline import Pipeline, PipelineStage, StageResult
from src.domain.ports.fhir_client_port import FHIRClientPort
from src.domain.ports.omop_writer_port import OMOPWriterPort
from src.domain.ports.repository_ports import (
    EventBusPort,
    MappingConfigRepositoryPort,
    PipelineRepositoryPort,
    SourceConnectionRepositoryPort,
)
from src.domain.services.mapping_service import MappingDomainService
from src.domain.value_objects.fhir import FHIRBundle
from src.domain.value_objects.omop import OMOPRecord


class ExecutePipelineUseCase:
    def __init__(
        self,
        pipeline_repo: PipelineRepositoryPort,
        source_repo: SourceConnectionRepositoryPort,
        mapping_repo: MappingConfigRepositoryPort,
        fhir_client: FHIRClientPort,
        mapping_service: MappingDomainService,
        omop_writer: OMOPWriterPort,
        event_bus: EventBusPort,
    ) -> None:
        self._pipeline_repo = pipeline_repo
        self._source_repo = source_repo
        self._mapping_repo = mapping_repo
        self._fhir_client = fhir_client
        self._mapping_service = mapping_service
        self._omop_writer = omop_writer
        self._event_bus = event_bus

    async def execute(self, dto: CreatePipelineDTO) -> PipelineResponseDTO:
        # Validate source connection is usable
        source = await self._source_repo.get_by_id(dto.source_connection_id)
        if source is None:
            raise ValueError(f"Source connection {dto.source_connection_id} not found")
        if not source.is_usable:
            raise ValueError(f"Source connection '{source.name}' is not active")

        # Validate all mapping configs exist and are active
        mappings = []
        for mid in dto.mapping_config_ids:
            m = await self._mapping_repo.get_by_id(mid)
            if m is None:
                raise ValueError(f"Mapping configuration {mid} not found")
            if not m.is_active:
                raise ValueError(f"Mapping '{m.name}' is not active")
            mappings.append(m)

        # Create and start pipeline
        pipeline = Pipeline.create(
            id=str(uuid.uuid4()),
            name=dto.name,
            source_connection_id=dto.source_connection_id,
            mapping_config_ids=tuple(dto.mapping_config_ids),
            target_connection_string=dto.target_connection_string,
        )
        pipeline = pipeline.start()
        await self._pipeline_repo.save(pipeline)

        try:
            # === EXTRACT STAGE ===
            extract_start = datetime.now(UTC)
            all_bundles: list[FHIRBundle] = []
            for mapping in mappings:
                bundle = await self._fhir_client.extract_resources(
                    endpoint=source.endpoint,
                    resource_type=mapping.source_resource,
                )
                all_bundles.append(bundle)

            total_extracted = sum(b.count for b in all_bundles)
            extract_result = StageResult(
                stage=PipelineStage.EXTRACT,
                records_in=0,
                records_out=total_extracted,
                error_count=0,
                started_at=extract_start,
                completed_at=datetime.now(UTC),
            )
            pipeline = pipeline.complete_stage(extract_result)
            await self._pipeline_repo.save(pipeline)

            # === TRANSFORM STAGE ===
            transform_start = datetime.now(UTC)
            all_records: list[OMOPRecord] = []
            transform_errors = 0
            for bundle, mapping in zip(all_bundles, mappings):
                try:
                    records = await self._mapping_service.transform_bundle(bundle, mapping)
                    all_records.extend(records)
                except Exception as e:
                    transform_errors += 1

            transform_result = StageResult(
                stage=PipelineStage.TRANSFORM,
                records_in=total_extracted,
                records_out=len(all_records),
                error_count=transform_errors,
                started_at=transform_start,
                completed_at=datetime.now(UTC),
            )
            pipeline = pipeline.complete_stage(transform_result)
            await self._pipeline_repo.save(pipeline)

            # === LOAD STAGE ===
            load_start = datetime.now(UTC)
            loaded_count = await self._omop_writer.write_records(all_records)

            load_result = StageResult(
                stage=PipelineStage.LOAD,
                records_in=len(all_records),
                records_out=loaded_count,
                error_count=len(all_records) - loaded_count,
                started_at=load_start,
                completed_at=datetime.now(UTC),
            )
            pipeline = pipeline.complete_stage(load_result)
            pipeline = pipeline.complete()
            await self._pipeline_repo.save(pipeline)

        except Exception as e:
            stage = pipeline.current_stage or PipelineStage.EXTRACT
            pipeline = pipeline.fail(stage, str(e))
            await self._pipeline_repo.save(pipeline)

        if pipeline.domain_events:
            await self._event_bus.publish(list(pipeline.domain_events))

        return self._to_response(pipeline)

    @staticmethod
    def _to_response(p: Pipeline) -> PipelineResponseDTO:
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
