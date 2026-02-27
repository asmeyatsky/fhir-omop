"""
FastAPI Application Entry Point

Architectural Intent:
- Composition root for the web application
- Wires DI container, registers routers, configures middleware
- Loads mapping templates on startup
- Initializes database connections for persistent storage
- Serves frontend static files and SPA catch-all
"""
from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from src.domain.entities.tenant import Tenant
from src.domain.entities.user import User, UserRole
from src.infrastructure.config.container import AppContainer
from src.infrastructure.middleware.audit_middleware import AuditMiddleware, set_global_audit_log
from src.infrastructure.middleware.input_validation import InputValidationMiddleware
from src.infrastructure.middleware.rate_limiter import RateLimiterMiddleware
from src.infrastructure.middleware.security_headers import SecurityHeadersMiddleware
from src.infrastructure.templates.registry import load_all_templates
from src.presentation.api.schemas import HealthResponse

logger = logging.getLogger(__name__)

_container: AppContainer | None = None


def get_container() -> AppContainer:
    if _container is None:
        raise RuntimeError("Application not initialized")
    return _container


async def _bootstrap_demo_user(container: AppContainer) -> None:
    """If no users exist, create a default tenant and admin user for local dev."""
    users = await container.user_repo.list_all()
    if users:
        return
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@local.dev")
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "Admin123!")
    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    tenant = Tenant.create(
        id=tenant_id,
        name="default",
        hospital_name="Local Development",
        nphies_facility_id=None,
    )
    await container.tenant_repo.save(tenant)
    password_hash = container.password_service.hash_password(password)
    user = User.create(
        id=user_id,
        email=email,
        full_name="Local Admin",
        role=UserRole.ADMIN,
        tenant_id=tenant_id,
        password_hash=password_hash,
    )
    await container.user_repo.save(user)
    logger.info("Bootstrap: created default tenant and admin user %s", email)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _container
    _container = AppContainer()
    _container.templates = load_all_templates()
    await _container.initialize()
    set_global_audit_log(_container.audit_log)
    await _bootstrap_demo_user(_container)
    logger.info("Application initialized")
    yield
    await _container.shutdown()
    _container = None
    logger.info("Application shut down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="FHIR-to-OMOP Data Accelerator",
        description="Transform FHIR R4 clinical data into OMOP CDM v5.4 datasets. "
        "Enterprise edition for Saudi healthcare compliance.",
        version="0.2.0",
        lifespan=lifespan,
    )

    # Middleware stack (executed in reverse order of registration):
    # SecurityHeaders → RateLimiter → CORS → Audit → InputValidation → App
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(AuditMiddleware, audit_log=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimiterMiddleware, requests_per_minute=100, burst_size=20)
    app.add_middleware(SecurityHeadersMiddleware)

    # Import and register routers
    from src.presentation.api.mapping_router import router as mapping_router
    from src.presentation.api.pipeline_router import router as pipeline_router
    from src.presentation.api.source_router import router as source_router
    from src.presentation.api.auth_router import router as auth_router
    from src.presentation.api.tenant_router import router as tenant_router
    from src.presentation.api.user_router import router as user_router
    from src.presentation.api.audit_router import router as audit_router
    from src.presentation.api.consent_router import router as consent_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(user_router, prefix="/api/v1")
    app.include_router(source_router, prefix="/api/v1")
    app.include_router(mapping_router, prefix="/api/v1")
    app.include_router(pipeline_router, prefix="/api/v1")
    app.include_router(tenant_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(consent_router, prefix="/api/v1")

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        return HealthResponse(status="healthy", version="0.2.0", service="fhir-omop-accelerator")

    # Avoid 404 when the browser requests /favicon.ico
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        frontend_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend"
        ico = frontend_dir / "favicon.ico"
        if ico.is_file():
            return FileResponse(ico, media_type="image/x-icon")
        return Response(status_code=204)

    @app.get("/api/v1", include_in_schema=False)
    async def api_root():
        """API entry point — confirms this is the FHIR-OMOP app and lists key URLs."""
        return {
            "service": "FHIR-to-OMOP Data Accelerator",
            "version": "0.2.0",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health": "/health",
            "login": "POST /api/v1/auth/login",
        }

    # Serve frontend static files
    frontend_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend"
    if frontend_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            """SPA catch-all: serve index.html for all non-API routes."""
            return FileResponse(str(frontend_dir / "index.html"))

    return app


app = create_app()
