"""
Tenant Context Value Object

Architectural Intent:
- Carries tenant identity through all layers via contextvars
- Used by repositories to scope all queries to the current tenant
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    """Current tenant context for a request."""
    tenant_id: str
    tenant_name: str = ""
