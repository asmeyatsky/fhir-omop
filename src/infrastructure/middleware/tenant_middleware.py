"""
Tenant Middleware

Architectural Intent:
- Extracts tenant_id from request headers (X-Tenant-ID)
- Sets the tenant context variable for the duration of the request
- Phase 1: header-based; Phase 2: extracted from JWT claims
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.domain.value_objects.tenant_context import TenantContext
from src.infrastructure.repositories.tenant_context import clear_current_tenant, set_current_tenant

# Paths that don't require tenant context
TENANT_EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class TenantMiddleware(BaseHTTPMiddleware):
    """Extracts and sets tenant context for each request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Skip tenant check for exempt paths
        if path in TENANT_EXEMPT_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return JSONResponse(
                status_code=400,
                content={"detail": "X-Tenant-ID header is required"},
            )

        # Set tenant context for this request
        set_current_tenant(TenantContext(tenant_id=tenant_id))
        try:
            response = await call_next(request)
        finally:
            clear_current_tenant()

        return response
