"""
Auth Value Objects

Architectural Intent:
- Token claims and permission definitions for RBAC
- Maps roles to granular permissions per NCA ECC-2:2024
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.user import UserRole


@dataclass(frozen=True)
class Permission:
    """A granular permission: resource + action."""
    resource: str  # e.g., "pipeline", "source", "mapping", "tenant", "user", "audit", "consent"
    action: str    # e.g., "create", "read", "update", "delete", "execute"


@dataclass(frozen=True)
class TokenClaims:
    """Claims embedded in a JWT token."""
    user_id: str
    email: str
    role: UserRole
    tenant_id: str
    permissions: tuple[str, ...]  # Flattened "resource:action" strings
    expires_at: datetime


# Role → Permission mapping (NCA ECC-2:2024 least-privilege)
ROLE_PERMISSIONS: dict[UserRole, tuple[Permission, ...]] = {
    UserRole.ADMIN: (
        Permission("tenant", "create"), Permission("tenant", "read"),
        Permission("tenant", "update"), Permission("tenant", "delete"),
        Permission("user", "create"), Permission("user", "read"),
        Permission("user", "update"), Permission("user", "delete"),
        Permission("source", "create"), Permission("source", "read"),
        Permission("source", "update"), Permission("source", "delete"),
        Permission("mapping", "create"), Permission("mapping", "read"),
        Permission("mapping", "update"), Permission("mapping", "delete"),
        Permission("pipeline", "create"), Permission("pipeline", "read"),
        Permission("pipeline", "execute"),
        Permission("consent", "create"), Permission("consent", "read"),
        Permission("consent", "revoke"),
        Permission("audit", "read"),
    ),
    UserRole.DATA_STEWARD: (
        Permission("mapping", "create"), Permission("mapping", "read"),
        Permission("mapping", "update"),
        Permission("pipeline", "read"),
        Permission("consent", "create"), Permission("consent", "read"),
        Permission("consent", "revoke"),
        Permission("source", "read"),
    ),
    UserRole.OPERATOR: (
        Permission("source", "create"), Permission("source", "read"),
        Permission("source", "update"),
        Permission("mapping", "read"),
        Permission("pipeline", "create"), Permission("pipeline", "read"),
        Permission("pipeline", "execute"),
    ),
    UserRole.AUDITOR: (
        Permission("source", "read"),
        Permission("mapping", "read"),
        Permission("pipeline", "read"),
        Permission("audit", "read"),
        Permission("consent", "read"),
    ),
}


def get_permission_strings(role: UserRole) -> tuple[str, ...]:
    """Get flattened permission strings for a role."""
    return tuple(f"{p.resource}:{p.action}" for p in ROLE_PERMISSIONS.get(role, ()))
