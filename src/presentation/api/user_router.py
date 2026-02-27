"""
User Management API Router

Admin-only endpoints for managing users.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.application.dtos.auth_dtos import CreateUserDTO
from src.domain.entities.user import UserRole
from src.domain.value_objects.auth import TokenClaims
from src.presentation.api.app import get_container
from src.presentation.api.dependencies import require_role

router = APIRouter(prefix="/users", tags=["Users"])


class CreateUserRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(admin|data_steward|operator|auditor)$")
    tenant_id: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: str
    is_active: bool
    created_at: str


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    request: CreateUserRequest,
    claims: TokenClaims = Depends(require_role(UserRole.ADMIN)),
):
    container = get_container()
    use_case = container.create_user_use_case()
    try:
        result = await use_case.execute(
            CreateUserDTO(
                email=request.email,
                full_name=request.full_name,
                role=request.role,
                tenant_id=request.tenant_id,
                password=request.password,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return UserResponse(
        id=result.id,
        email=result.email,
        full_name=result.full_name,
        role=result.role,
        tenant_id=result.tenant_id,
        is_active=result.is_active,
        created_at=result.created_at.isoformat(),
    )


@router.get("", response_model=list[UserResponse])
async def list_users(
    claims: TokenClaims = Depends(require_role(UserRole.ADMIN)),
):
    container = get_container()
    users = await container.user_repo.list_all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value,
            tenant_id=u.tenant_id,
            is_active=u.is_active,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]
