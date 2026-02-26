"""
Mapping Configuration API Router

Architectural Intent:
- Presentation layer for mapping templates and configurations
- Provides template listing and mapping creation from templates
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.application.dtos.mapping_dtos import CreateMappingFromTemplateDTO
from src.infrastructure.config.container import AppContainer
from src.presentation.api.schemas import (
    CreateMappingFromTemplateRequest,
    MappingConfigResponse,
    MappingTemplateResponse,
)

router = APIRouter(prefix="/mappings", tags=["Mappings"])


def _get_container() -> AppContainer:
    from src.presentation.api.app import get_container
    return get_container()


@router.get("/templates", response_model=list[MappingTemplateResponse])
async def list_templates():
    """List all available pre-built mapping templates."""
    container = _get_container()
    query = container.list_mapping_templates_query()
    results = await query.execute()
    return [MappingTemplateResponse(**r.__dict__) for r in results]


@router.post("", response_model=MappingConfigResponse, status_code=201)
async def create_mapping_from_template(request: CreateMappingFromTemplateRequest):
    """Create a mapping configuration from a pre-built template."""
    container = _get_container()
    use_case = container.create_mapping_use_case()
    try:
        result = await use_case.execute(
            CreateMappingFromTemplateDTO(
                name=request.name,
                template_id=request.template_id,
            )
        )
        return MappingConfigResponse(**result.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[MappingConfigResponse])
async def list_mapping_configs():
    """List all mapping configurations."""
    container = _get_container()
    query = container.list_mapping_configs_query()
    results = await query.execute()
    return [MappingConfigResponse(**r.__dict__) for r in results]
