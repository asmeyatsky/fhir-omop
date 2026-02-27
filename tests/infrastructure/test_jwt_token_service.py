"""Tests for JWT Token Service and Password Service."""
from datetime import UTC, datetime

from src.domain.entities.user import UserRole
from src.domain.value_objects.auth import TokenClaims, get_permission_strings
from src.infrastructure.adapters.auth.jwt_token_service import JWTTokenService
from src.infrastructure.adapters.auth.password_service import BcryptPasswordService


class TestJWTTokenService:
    def _make_claims(self) -> TokenClaims:
        return TokenClaims(
            user_id="u-001",
            email="admin@kfshrc.sa",
            role=UserRole.ADMIN,
            tenant_id="t-001",
            permissions=get_permission_strings(UserRole.ADMIN),
            expires_at=datetime.now(UTC),
        )

    def test_create_and_verify_access_token(self):
        service = JWTTokenService()
        claims = self._make_claims()
        token = service.create_access_token(claims)

        verified = service.verify_token(token)
        assert verified is not None
        assert verified.user_id == "u-001"
        assert verified.email == "admin@kfshrc.sa"
        assert verified.role == UserRole.ADMIN
        assert verified.tenant_id == "t-001"
        assert "user:create" in verified.permissions

    def test_create_refresh_token(self):
        service = JWTTokenService()
        claims = self._make_claims()
        token = service.create_refresh_token(claims)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_invalid_token_returns_none(self):
        service = JWTTokenService()
        assert service.verify_token("invalid.token.here") is None

    def test_empty_token_returns_none(self):
        service = JWTTokenService()
        assert service.verify_token("") is None


class TestBcryptPasswordService:
    def test_hash_and_verify(self):
        service = BcryptPasswordService()
        password = "SecureP@ss123!"
        hashed = service.hash_password(password)

        assert hashed != password
        assert service.verify_password(password, hashed) is True

    def test_wrong_password(self):
        service = BcryptPasswordService()
        hashed = service.hash_password("correct_password")
        assert service.verify_password("wrong_password", hashed) is False

    def test_different_hashes(self):
        service = BcryptPasswordService()
        hash1 = service.hash_password("same_password")
        hash2 = service.hash_password("same_password")
        assert hash1 != hash2  # bcrypt uses random salt
