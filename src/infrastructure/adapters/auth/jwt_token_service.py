"""
JWT Token Service

Architectural Intent:
- Implements TokenPort using PyJWT with HS256
- Access tokens: 30 min expiry
- Refresh tokens: 24h expiry
"""
from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import jwt

from src.domain.entities.user import UserRole
from src.domain.value_objects.auth import TokenClaims, get_permission_strings

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_HOURS = 24


class JWTTokenService:
    """JWT token creation and verification."""

    def create_access_token(self, claims: TokenClaims) -> str:
        expires = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": claims.user_id,
            "email": claims.email,
            "role": claims.role.value,
            "tenant_id": claims.tenant_id,
            "permissions": list(claims.permissions),
            "exp": expires,
            "type": "access",
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, claims: TokenClaims) -> str:
        expires = datetime.now(UTC) + timedelta(hours=REFRESH_TOKEN_EXPIRE_HOURS)
        payload = {
            "sub": claims.user_id,
            "exp": expires,
            "type": "refresh",
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> TokenClaims | None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            role = UserRole(payload["role"])
            return TokenClaims(
                user_id=payload["sub"],
                email=payload.get("email", ""),
                role=role,
                tenant_id=payload.get("tenant_id", ""),
                permissions=tuple(payload.get("permissions", get_permission_strings(role))),
                expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, ValueError):
            return None
