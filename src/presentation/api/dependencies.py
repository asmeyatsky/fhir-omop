"""
FastAPI Dependencies for Auth and RBAC

Architectural Intent:
- Reusable dependency injection for authentication
- Role and permission checking via FastAPI Depends()
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.domain.entities.user import UserRole
from src.domain.value_objects.auth import TokenClaims
from src.infrastructure.adapters.auth.jwt_token_service import JWTTokenService

security = HTTPBearer(auto_error=False)
_token_service = JWTTokenService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenClaims:
    """Extract and validate JWT token from Authorization header."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = _token_service.verify_token(credentials.credentials)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return claims


def require_role(*roles: UserRole):
    """Factory for role-based access control dependency."""

    async def _check_role(
        claims: TokenClaims = Depends(get_current_user),
    ) -> TokenClaims:
        if claims.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{claims.role.value}' does not have access. "
                f"Required: {', '.join(r.value for r in roles)}",
            )
        return claims

    return _check_role


def require_permission(resource: str, action: str):
    """Factory for permission-based access control dependency."""

    async def _check_permission(
        claims: TokenClaims = Depends(get_current_user),
    ) -> TokenClaims:
        required = f"{resource}:{action}"
        if required not in claims.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {required}",
            )
        return claims

    return _check_permission
