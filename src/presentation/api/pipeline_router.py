"""
Pipeline API Router

Architectural Intent:
- Presentation layer for pipeline execution and monitoring
- Create, execute, and query pipeline status
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.application.dtos.pipeline_dtos import CreatePipelineDTO
from src.infrastructure.config.container import AppContainer
from src.presentation.api.schemas import (
    CreatePipelineRequest,
    PipelineResponse,
    StageResultResponse,
)

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


def _get_container() -> AppContainer:
    from src.presentation.api.app import get_container
    return get_container()


@router.post("", response_model=PipelineResponse, status_code=201)
async def execute_pipeline(request: CreatePipelineRequest):
    """Create and execute a FHIR-to-OMOP pipeline."""
    container = _get_container()
    use_case = container.execute_pipeline_use_case()
    try:
        result = await use_case.execute(
            CreatePipelineDTO(
                name=request.name,
                source_connection_id=request.source_connection_id,
                mapping_config_ids=request.mapping_config_ids,
                target_connection_string=request.target_connection_string,
            )
        )
        return _to_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: str):
    """Get pipeline execution status and details."""
    container = _get_container()
    query = container.get_pipeline_query()
    result = await query.execute(pipeline_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return _to_response(result)


@router.get("", response_model=list[PipelineResponse])
async def list_pipelines():
    """List all pipelines."""
    container = _get_container()
    query = container.list_pipelines_query()
    results = await query.execute()
    return [_to_response(r) for r in results]


def _to_response(dto) -> PipelineResponse:
    return PipelineResponse(
        id=dto.id,
        name=dto.name,
        source_connection_id=dto.source_connection_id,
        mapping_config_ids=dto.mapping_config_ids,
        status=dto.status,
        created_at=dto.created_at,
        started_at=dto.started_at,
        completed_at=dto.completed_at,
        current_stage=dto.current_stage,
        stage_results=[
            StageResultResponse(
                stage=sr.stage,
                records_in=sr.records_in,
                records_out=sr.records_out,
                error_count=sr.error_count,
                started_at=sr.started_at,
                completed_at=sr.completed_at,
            )
            for sr in dto.stage_results
        ],
        total_records=dto.total_records,
        total_errors=dto.total_errors,
        error_message=dto.error_message,
    )
