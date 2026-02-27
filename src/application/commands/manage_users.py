"""
User Management Use Cases

Architectural Intent:
- CRUD operations for user accounts
- Admin-only operations per RBAC matrix
"""
from __future__ import annotations

import uuid

from src.application.dtos.auth_dtos import CreateUserDTO, UserResponseDTO
from src.domain.entities.user import User, UserRole
from src.domain.ports.auth_port import PasswordPort, UserRepositoryPort


class CreateUserUseCase:
    def __init__(
        self,
        user_repo: UserRepositoryPort,
        password_service: PasswordPort,
    ) -> None:
        self._user_repo = user_repo
        self._password_service = password_service

    async def execute(self, dto: CreateUserDTO) -> UserResponseDTO:
        # Check for duplicate email
        existing = await self._user_repo.get_by_email(dto.email.lower().strip())
        if existing:
            raise ValueError(f"User with email '{dto.email}' already exists")

        password_hash = self._password_service.hash_password(dto.password)
        user = User.create(
            id=str(uuid.uuid4()),
            email=dto.email,
            full_name=dto.full_name,
            role=UserRole(dto.role),
            tenant_id=dto.tenant_id,
            password_hash=password_hash,
        )
        await self._user_repo.save(user)

        return UserResponseDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            tenant_id=user.tenant_id,
            is_active=user.is_active,
            created_at=user.created_at,
        )
