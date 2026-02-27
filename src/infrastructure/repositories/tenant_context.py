"""
Tenant Context Variable

Architectural Intent:
- Python contextvars-based tenant scoping
- Set by middleware on each request
- Read by repositories to filter queries
"""
from __future__ import annotations

import contextvars

from src.domain.value_objects.tenant_context import TenantContext

_current_tenant: contextvars.ContextVar[TenantContext | None] = contextvars.ContextVar(
    "current_tenant", default=None
)


def set_current_tenant(ctx: TenantContext) -> None:
    """Set the current tenant for this async context."""
    _current_tenant.set(ctx)


def get_current_tenant() -> TenantContext | None:
    """Get the current tenant for this async context."""
    return _current_tenant.get()


def get_current_tenant_id() -> str | None:
    """Get just the tenant ID, or None if not set."""
    ctx = _current_tenant.get()
    return ctx.tenant_id if ctx else None


def clear_current_tenant() -> None:
    """Clear the current tenant context."""
    _current_tenant.set(None)
