"""
Auth API Router

Endpoints for login, token refresh, and current user info.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.application.dtos.auth_dtos import LoginDTO
from src.domain.value_objects.auth import TokenClaims
from src.presentation.api.app import get_container
from src.presentation.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    user_id: str
    email: str
    role: str
    tenant_id: str
    permissions: list[str]


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    container = get_container()
    use_case = container.authenticate_user_use_case()
    try:
        result = await use_case.execute(
            LoginDTO(email=request.email, password=request.password)
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.get("/me", response_model=MeResponse)
async def get_me(claims: TokenClaims = Depends(get_current_user)):
    return MeResponse(
        user_id=claims.user_id,
        email=claims.email,
        role=claims.role.value,
        tenant_id=claims.tenant_id,
        permissions=list(claims.permissions),
    )
