"""
User Entity

Architectural Intent:
- Aggregate root for application users
- Role-based access control (RBAC) for Saudi compliance
- Roles: ADMIN, DATA_STEWARD, OPERATOR, AUDITOR
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    DATA_STEWARD = "data_steward"
    OPERATOR = "operator"
    AUDITOR = "auditor"


@dataclass(frozen=True)
class User:
    """Aggregate root: an application user with RBAC role."""
    id: str
    email: str
    full_name: str
    role: UserRole
    tenant_id: str
    password_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(
        id: str,
        email: str,
        full_name: str,
        role: UserRole,
        tenant_id: str,
        password_hash: str,
    ) -> User:
        if not email.strip():
            raise ValueError("Email cannot be empty")
        if not full_name.strip():
            raise ValueError("Full name cannot be empty")
        now = datetime.now(UTC)
        return User(
            id=id,
            email=email.strip().lower(),
            full_name=full_name.strip(),
            role=role,
            tenant_id=tenant_id,
            password_hash=password_hash,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def deactivate(self) -> User:
        return replace(self, is_active=False, updated_at=datetime.now(UTC))

    def change_role(self, new_role: UserRole) -> User:
        return replace(self, role=new_role, updated_at=datetime.now(UTC))
