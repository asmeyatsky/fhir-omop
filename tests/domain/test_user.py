"""Tests for User entity."""
import pytest

from src.domain.entities.user import User, UserRole


class TestUserCreation:
    def test_create_user(self):
        user = User.create(
            id="u-001", email="admin@kfshrc.sa", full_name="Ahmed Al-Rashid",
            role=UserRole.ADMIN, tenant_id="t-001", password_hash="hashed",
        )
        assert user.id == "u-001"
        assert user.email == "admin@kfshrc.sa"
        assert user.full_name == "Ahmed Al-Rashid"
        assert user.role == UserRole.ADMIN
        assert user.is_active is True

    def test_email_normalized(self):
        user = User.create(
            id="u-002", email="  Admin@KFSHRC.SA  ", full_name="Test",
            role=UserRole.OPERATOR, tenant_id="t-001", password_hash="hashed",
        )
        assert user.email == "admin@kfshrc.sa"

    def test_empty_email_raises(self):
        with pytest.raises(ValueError, match="Email"):
            User.create(id="u-003", email="", full_name="Test",
                       role=UserRole.ADMIN, tenant_id="t-001", password_hash="h")

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="Full name"):
            User.create(id="u-004", email="test@test.sa", full_name="",
                       role=UserRole.ADMIN, tenant_id="t-001", password_hash="h")

    def test_deactivate(self):
        user = User.create(
            id="u-005", email="op@test.sa", full_name="Operator",
            role=UserRole.OPERATOR, tenant_id="t-001", password_hash="h",
        )
        deactivated = user.deactivate()
        assert deactivated.is_active is False

    def test_change_role(self):
        user = User.create(
            id="u-006", email="ds@test.sa", full_name="Data Steward",
            role=UserRole.DATA_STEWARD, tenant_id="t-001", password_hash="h",
        )
        promoted = user.change_role(UserRole.ADMIN)
        assert promoted.role == UserRole.ADMIN

    def test_frozen(self):
        user = User.create(
            id="u-007", email="test@test.sa", full_name="Test",
            role=UserRole.AUDITOR, tenant_id="t-001", password_hash="h",
        )
        with pytest.raises(AttributeError):
            user.email = "changed@test.sa"  # type: ignore[misc]


class TestRolePermissions:
    def test_admin_has_all_permissions(self):
        from src.domain.value_objects.auth import ROLE_PERMISSIONS, get_permission_strings
        perms = get_permission_strings(UserRole.ADMIN)
        assert "user:create" in perms
        assert "pipeline:execute" in perms
        assert "audit:read" in perms
        assert "consent:create" in perms

    def test_auditor_read_only(self):
        from src.domain.value_objects.auth import get_permission_strings
        perms = get_permission_strings(UserRole.AUDITOR)
        assert "audit:read" in perms
        assert "pipeline:read" in perms
        assert "pipeline:execute" not in perms
        assert "user:create" not in perms

    def test_operator_can_execute_pipelines(self):
        from src.domain.value_objects.auth import get_permission_strings
        perms = get_permission_strings(UserRole.OPERATOR)
        assert "pipeline:execute" in perms
        assert "source:create" in perms
        assert "mapping:create" not in perms

    def test_data_steward_can_manage_mappings(self):
        from src.domain.value_objects.auth import get_permission_strings
        perms = get_permission_strings(UserRole.DATA_STEWARD)
        assert "mapping:create" in perms
        assert "consent:create" in perms
        assert "pipeline:execute" not in perms
