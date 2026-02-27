"""Auth DTOs for authentication and user management."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LoginDTO:
    email: str
    password: str


@dataclass(frozen=True)
class TokenResponseDTO:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class CreateUserDTO:
    email: str
    full_name: str
    role: str
    tenant_id: str
    password: str


@dataclass(frozen=True)
class UserResponseDTO:
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: str
    is_active: bool
    created_at: datetime
