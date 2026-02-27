"""
Consent API Router

Endpoints for managing patient consent per PDPL.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.domain.entities.consent import (
    Consent,
    ConsentPurpose,
    ConsentScope,
    ConsentStatus,
)
from src.domain.entities.user import UserRole
from src.domain.value_objects.auth import TokenClaims
from src.presentation.api.app import get_container
from src.presentation.api.dependencies import require_permission

router = APIRouter(prefix="/consent", tags=["Consent"])


class GrantConsentRequest(BaseModel):
    patient_id: str = Field(..., min_length=1)
    purpose: ConsentPurpose
    scope: ConsentScope
    expires_at: datetime | None = None
    resource_types: list[str] | None = None
    notes: str | None = None


class ConsentResponse(BaseModel):
    id: str
    patient_id: str
    tenant_id: str
    purpose: str
    scope: str
    status: str
    granted_by: str
    granted_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_by: str | None = None
    resource_types: list[str] | None = None
    notes: str | None = None
    is_valid: bool


class ConsentListResponse(BaseModel):
    consents: list[ConsentResponse]
    total: int


def _to_response(c: Consent) -> ConsentResponse:
    return ConsentResponse(
        id=c.id,
        patient_id=c.patient_id,
        tenant_id=c.tenant_id,
        purpose=c.purpose.value,
        scope=c.scope.value,
        status=c.status.value,
        granted_by=c.granted_by,
        granted_at=c.granted_at,
        expires_at=c.expires_at,
        revoked_at=c.revoked_at,
        revoked_by=c.revoked_by,
        resource_types=list(c.resource_types) if c.resource_types else None,
        notes=c.notes,
        is_valid=c.is_valid,
    )


@router.post("", response_model=ConsentResponse, status_code=201)
async def grant_consent(
    request: GrantConsentRequest,
    claims: TokenClaims = Depends(require_permission("consent", "create")),
):
    container = get_container()
    consent = Consent.grant(
        id=str(uuid.uuid4()),
        patient_id=request.patient_id,
        tenant_id=claims.tenant_id,
        purpose=request.purpose,
        scope=request.scope,
        granted_by=claims.user_id,
        expires_at=request.expires_at,
        resource_types=tuple(request.resource_types) if request.resource_types else None,
        notes=request.notes,
    )
    await container.consent_repo.save(consent)
    return _to_response(consent)


@router.get("", response_model=ConsentListResponse)
async def list_consents(
    patient_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    claims: TokenClaims = Depends(require_permission("consent", "read")),
):
    container = get_container()
    if patient_id:
        consents = await container.consent_repo.get_active_consents(
            patient_id, claims.tenant_id
        )
    else:
        consents = await container.consent_repo.list_by_tenant(
            claims.tenant_id, limit=limit, offset=offset
        )
    return ConsentListResponse(
        consents=[_to_response(c) for c in consents],
        total=len(consents),
    )


@router.post("/{consent_id}/revoke", response_model=ConsentResponse)
async def revoke_consent(
    consent_id: str,
    claims: TokenClaims = Depends(require_permission("consent", "create")),
):
    container = get_container()
    consent = await container.consent_repo.get_by_id(consent_id)
    if consent is None:
        raise HTTPException(status_code=404, detail="Consent not found")
    if consent.tenant_id != claims.tenant_id:
        raise HTTPException(status_code=404, detail="Consent not found")
    revoked = consent.revoke(revoked_by=claims.user_id)
    await container.consent_repo.save(revoked)
    return _to_response(revoked)
