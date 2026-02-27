"""
Tenant API Router

Endpoints for managing hospital/organization tenants.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.domain.entities.tenant import Tenant
from src.presentation.api.app import get_container

router = APIRouter(prefix="/tenants", tags=["Tenants"])


class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    hospital_name: str = Field(..., min_length=1, max_length=500)
    nphies_facility_id: str | None = None


class TenantResponse(BaseModel):
    id: str
    name: str
    hospital_name: str
    nphies_facility_id: str | None
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


def _tenant_to_response(tenant: Tenant) -> TenantResponse:
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        hospital_name=tenant.hospital_name,
        nphies_facility_id=tenant.nphies_facility_id,
        is_active=tenant.is_active,
        created_at=tenant.created_at.isoformat(),
        updated_at=tenant.updated_at.isoformat(),
    )


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(request: CreateTenantRequest):
    container = get_container()
    tenant = Tenant.create(
        id=str(uuid.uuid4()),
        name=request.name,
        hospital_name=request.hospital_name,
        nphies_facility_id=request.nphies_facility_id,
    )
    await container.tenant_repo.save(tenant)
    return _tenant_to_response(tenant)


@router.get("", response_model=list[TenantResponse])
async def list_tenants():
    container = get_container()
    tenants = await container.tenant_repo.list_all()
    return [_tenant_to_response(t) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    container = get_container()
    tenant = await container.tenant_repo.get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return _tenant_to_response(tenant)
