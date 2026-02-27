"""
Audit Middleware

Architectural Intent:
- Intercepts all HTTP requests and logs them as audit entries
- Captures actor from JWT, IP, method, path, status code
- Non-blocking: audit failures don't break request processing
- Exempt paths: /health, /docs, /openapi.json
"""
from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.domain.entities.audit_entry import AuditAction, AuditEntry, AuditEventType
from src.infrastructure.adapters.auth.jwt_token_service import JWTTokenService

logger = logging.getLogger(__name__)

# Module-level audit log reference — set during app lifespan
_audit_log_ref: object | None = None


def set_global_audit_log(audit_log: object) -> None:
    global _audit_log_ref
    _audit_log_ref = audit_log


EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

# Map HTTP methods to audit actions
_METHOD_ACTION_MAP = {
    "GET": AuditAction.READ,
    "POST": AuditAction.CREATE,
    "PUT": AuditAction.UPDATE,
    "PATCH": AuditAction.UPDATE,
    "DELETE": AuditAction.DELETE,
}

# Map path prefixes to event types
_PATH_EVENT_MAP = [
    ("/api/v1/auth", AuditEventType.AUTH),
    ("/api/v1/users", AuditEventType.ADMIN),
    ("/api/v1/tenants", AuditEventType.ADMIN),
    ("/api/v1/pipelines", AuditEventType.PIPELINE),
    ("/api/v1/audit", AuditEventType.DATA_ACCESS),
]


def _classify_event(path: str) -> AuditEventType:
    for prefix, event_type in _PATH_EVENT_MAP:
        if path.startswith(prefix):
            return event_type
    return AuditEventType.DATA_ACCESS


def _classify_action(method: str, path: str, status: int) -> AuditAction:
    if "/auth/login" in path:
        return AuditAction.LOGIN_SUCCESS if status < 400 else AuditAction.LOGIN_FAILURE
    if "/pipelines" in path and method == "POST" and "execute" in path:
        return AuditAction.PIPELINE_START
    return _METHOD_ACTION_MAP.get(method, AuditAction.READ)


def _extract_resource(path: str) -> tuple[str | None, str | None]:
    """Extract resource type and ID from path like /api/v1/sources/abc-123."""
    parts = path.rstrip("/").split("/")
    # /api/v1/<resource>/<id>
    if len(parts) >= 4:
        resource_type = parts[3]  # e.g. "sources", "pipelines"
        resource_id = parts[4] if len(parts) >= 5 else None
        return resource_type, resource_id
    return None, None


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, audit_log=None):
        super().__init__(app)
        self._token_service = JWTTokenService()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        start_time = time.monotonic()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            raise
        finally:
            duration_ms = (time.monotonic() - start_time) * 1000
            audit_log = _audit_log_ref
            if audit_log is not None:
                await self._record_audit(request, status_code, duration_ms, audit_log)

        return response

    async def _record_audit(
        self, request: Request, status_code: int, duration_ms: float, audit_log
    ) -> None:
        try:
            # Extract actor from JWT if present
            actor_id = None
            actor_email = None
            actor_role = None
            tenant_id = None
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                claims = self._token_service.verify_token(token)
                if claims:
                    actor_id = claims.user_id
                    actor_email = claims.email
                    actor_role = claims.role.value
                    tenant_id = claims.tenant_id

            # Fallback tenant from header
            if not tenant_id:
                tenant_id = request.headers.get("x-tenant-id")

            resource_type, resource_id = _extract_resource(request.url.path)
            method = request.method
            path = request.url.path

            entry = AuditEntry.create(
                id=str(uuid.uuid4()),
                event_type=_classify_event(path),
                action=_classify_action(method, path, status_code),
                actor_id=actor_id,
                actor_email=actor_email,
                actor_role=actor_role,
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id,
                http_method=method,
                http_path=path,
                http_status=status_code,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                details={"duration_ms": round(duration_ms, 2)},
            )
            await audit_log.record(entry)
        except Exception:
            logger.exception("Failed to record audit entry")
