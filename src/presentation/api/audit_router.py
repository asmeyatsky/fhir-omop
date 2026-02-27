"""
Audit API Router

Endpoints for querying and verifying audit logs.
Restricted to AUDITOR and ADMIN roles.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.domain.entities.user import UserRole
from src.domain.value_objects.auth import TokenClaims
from src.presentation.api.app import get_container
from src.presentation.api.dependencies import require_role

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditEntryResponse(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    action: str
    actor_id: str | None = None
    actor_email: str | None = None
    actor_role: str | None = None
    tenant_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    http_method: str | None = None
    http_path: str | None = None
    http_status: int | None = None
    ip_address: str | None = None
    details: dict | None = None
    checksum: str


class AuditListResponse(BaseModel):
    entries: list[AuditEntryResponse]
    total: int
    limit: int
    offset: int


class IntegrityResponse(BaseModel):
    id: str
    valid: bool
    checksum: str


@router.get("", response_model=AuditListResponse)
async def list_audit_entries(
    event_type: str | None = Query(None, description="Filter by event type"),
    actor_id: str | None = Query(None, description="Filter by actor user ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    claims: TokenClaims = Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR)),
):
    container = get_container()
    entries = await container.audit_log.query(
        tenant_id=claims.tenant_id,
        actor_id=actor_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    total = await container.audit_log.count(
        tenant_id=claims.tenant_id,
        actor_id=actor_id,
        event_type=event_type,
    )
    return AuditListResponse(
        entries=[
            AuditEntryResponse(
                id=e.id,
                timestamp=e.timestamp,
                event_type=e.event_type.value,
                action=e.action.value,
                actor_id=e.actor_id,
                actor_email=e.actor_email,
                actor_role=e.actor_role,
                tenant_id=e.tenant_id,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                http_method=e.http_method,
                http_path=e.http_path,
                http_status=e.http_status,
                ip_address=e.ip_address,
                details=e.details,
                checksum=e.checksum,
            )
            for e in entries
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{entry_id}/verify", response_model=IntegrityResponse)
async def verify_audit_entry(
    entry_id: str,
    claims: TokenClaims = Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR)),
):
    container = get_container()
    entry = await container.audit_log.get_by_id(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    return IntegrityResponse(
        id=entry.id,
        valid=entry.verify_integrity(),
        checksum=entry.checksum,
    )
