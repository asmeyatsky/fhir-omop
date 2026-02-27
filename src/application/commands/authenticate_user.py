"""
Authenticate User Use Case

Architectural Intent:
- Validates credentials and issues JWT tokens
- Follows command pattern from application layer
"""
from __future__ import annotations

from src.application.dtos.auth_dtos import LoginDTO, TokenResponseDTO
from src.domain.ports.auth_port import PasswordPort, TokenPort, UserRepositoryPort
from src.domain.value_objects.auth import TokenClaims, get_permission_strings


class AuthenticateUserUseCase:
    def __init__(
        self,
        user_repo: UserRepositoryPort,
        password_service: PasswordPort,
        token_service: TokenPort,
    ) -> None:
        self._user_repo = user_repo
        self._password_service = password_service
        self._token_service = token_service

    async def execute(self, dto: LoginDTO) -> TokenResponseDTO:
        user = await self._user_repo.get_by_email(dto.email.lower().strip())
        if user is None:
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("Account is disabled")

        if not self._password_service.verify_password(dto.password, user.password_hash):
            raise ValueError("Invalid credentials")

        claims = TokenClaims(
            user_id=user.id,
            email=user.email,
            role=user.role,
            tenant_id=user.tenant_id,
            permissions=get_permission_strings(user.role),
            expires_at=user.created_at,  # Placeholder; actual expiry set by token service
        )

        return TokenResponseDTO(
            access_token=self._token_service.create_access_token(claims),
            refresh_token=self._token_service.create_refresh_token(claims),
        )
