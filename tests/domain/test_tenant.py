"""Tests for Tenant entity."""
import pytest

from src.domain.entities.tenant import Tenant, TenantSettings


class TestTenantCreation:
    def test_create_tenant(self):
        tenant = Tenant.create(
            id="t-001", name="King Faisal Hospital", hospital_name="KFSH&RC Riyadh"
        )
        assert tenant.id == "t-001"
        assert tenant.name == "King Faisal Hospital"
        assert tenant.hospital_name == "KFSH&RC Riyadh"
        assert tenant.is_active is True
        assert tenant.nphies_facility_id is None
        assert tenant.settings.max_pipelines_concurrent == 5
        assert tenant.settings.data_retention_days == 2555

    def test_create_with_nphies_id(self):
        tenant = Tenant.create(
            id="t-002", name="NGHA", hospital_name="National Guard Health Affairs",
            nphies_facility_id="NGHA-001",
        )
        assert tenant.nphies_facility_id == "NGHA-001"

    def test_create_empty_name_raises(self):
        with pytest.raises(ValueError, match="Tenant name"):
            Tenant.create(id="t-003", name="", hospital_name="Hospital")

    def test_create_empty_hospital_raises(self):
        with pytest.raises(ValueError, match="Hospital name"):
            Tenant.create(id="t-004", name="Test", hospital_name="  ")

    def test_deactivate(self):
        tenant = Tenant.create(id="t-005", name="Test", hospital_name="Test Hospital")
        deactivated = tenant.deactivate()
        assert deactivated.is_active is False
        assert deactivated.updated_at > tenant.created_at or deactivated.updated_at == tenant.updated_at

    def test_activate(self):
        tenant = Tenant.create(id="t-006", name="Test", hospital_name="Test Hospital")
        deactivated = tenant.deactivate()
        reactivated = deactivated.activate()
        assert reactivated.is_active is True

    def test_update_settings(self):
        tenant = Tenant.create(id="t-007", name="Test", hospital_name="Test Hospital")
        new_settings = TenantSettings(max_pipelines_concurrent=10, data_retention_days=3650)
        updated = tenant.update_settings(new_settings)
        assert updated.settings.max_pipelines_concurrent == 10
        assert updated.settings.data_retention_days == 3650

    def test_frozen(self):
        tenant = Tenant.create(id="t-008", name="Test", hospital_name="Test Hospital")
        with pytest.raises(AttributeError):
            tenant.name = "Modified"  # type: ignore[misc]


class TestTenantContext:
    def test_tenant_context_creation(self):
        from src.domain.value_objects.tenant_context import TenantContext
        ctx = TenantContext(tenant_id="t-001", tenant_name="King Faisal")
        assert ctx.tenant_id == "t-001"
        assert ctx.tenant_name == "King Faisal"

    def test_tenant_context_default_name(self):
        from src.domain.value_objects.tenant_context import TenantContext
        ctx = TenantContext(tenant_id="t-001")
        assert ctx.tenant_name == ""
