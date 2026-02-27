"""Tests for tenant context variable and middleware."""
from src.domain.value_objects.tenant_context import TenantContext
from src.infrastructure.repositories.tenant_context import (
    clear_current_tenant,
    get_current_tenant,
    get_current_tenant_id,
    set_current_tenant,
)


class TestTenantContextVar:
    def test_set_and_get(self):
        ctx = TenantContext(tenant_id="t-001", tenant_name="Test Hospital")
        set_current_tenant(ctx)
        assert get_current_tenant() == ctx
        assert get_current_tenant_id() == "t-001"
        clear_current_tenant()

    def test_default_none(self):
        clear_current_tenant()
        assert get_current_tenant() is None
        assert get_current_tenant_id() is None

    def test_clear(self):
        set_current_tenant(TenantContext(tenant_id="t-002"))
        clear_current_tenant()
        assert get_current_tenant() is None
