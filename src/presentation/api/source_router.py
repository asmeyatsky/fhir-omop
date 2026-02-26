"""
Source Connection API Router

Architectural Intent:
- Presentation layer for FHIR source connection management
- Thin controller — delegates all logic to use cases
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.application.dtos.source_dtos import CreateSourceConnectionDTO
from src.domain.value_objects.fhir import AuthMethod, FHIRServerType
from src.infrastructure.config.container import AppContainer
from src.presentation.api.schemas import CreateSourceConnectionRequest, SourceConnectionResponse

router = APIRouter(prefix="/sources", tags=["Source Connections"])


def _get_container() -> AppContainer:
    from src.presentation.api.app import get_container
    return get_container()


@router.post("", response_model=SourceConnectionResponse, status_code=201)
async def create_source_connection(request: CreateSourceConnectionRequest):
    """Create a new FHIR source server connection."""
    container = _get_container()
    use_case = container.create_source_connection_use_case()
    try:
        result = await use_case.execute(
            CreateSourceConnectionDTO(
                name=request.name,
                base_url=request.base_url,
                server_type=FHIRServerType(request.server_type),
                auth_method=AuthMethod(request.auth_method),
            )
        )
        return SourceConnectionResponse(**result.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{connection_id}/test", response_model=SourceConnectionResponse)
async def test_source_connection(connection_id: str):
    """Test connectivity to a configured FHIR server."""
    container = _get_container()
    use_case = container.test_source_connection_use_case()
    try:
        result = await use_case.execute(connection_id)
        return SourceConnectionResponse(**result.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=list[SourceConnectionResponse])
async def list_source_connections():
    """List all configured FHIR source connections."""
    container = _get_container()
    query = container.list_source_connections_query()
    results = await query.execute()
    return [SourceConnectionResponse(**r.__dict__) for r in results]
