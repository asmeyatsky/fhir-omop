"""
FastAPI Application Entry Point

Architectural Intent:
- Composition root for the web application
- Wires DI container, registers routers, configures middleware
- Loads mapping templates on startup
- Initializes database connections for persistent storage
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.container import AppContainer
from src.infrastructure.middleware.audit_middleware import AuditMiddleware, set_global_audit_log
from src.infrastructure.templates.registry import load_all_templates
from src.presentation.api.schemas import HealthResponse

logger = logging.getLogger(__name__)

_container: AppContainer | None = None


def get_container() -> AppContainer:
    if _container is None:
        raise RuntimeError("Application not initialized")
    return _container


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _container
    _container = AppContainer()
    _container.templates = load_all_templates()
    await _container.initialize()
    set_global_audit_log(_container.audit_log)
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Audit middleware — audit_log is injected during lifespan after container init
    app.add_middleware(AuditMiddleware, audit_log=None)

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
        return HealthResponse(version="0.2.0")

    return app


app = create_app()
