"""
FastAPI Application Entry Point

Architectural Intent:
- Composition root for the web application
- Wires DI container, registers routers, configures middleware
- Loads mapping templates on startup
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.container import AppContainer
from src.infrastructure.templates.registry import load_all_templates
from src.presentation.api.schemas import HealthResponse

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
    yield
    _container = None


def create_app() -> FastAPI:
    app = FastAPI(
        title="FHIR-to-OMOP Data Accelerator",
        description="Transform FHIR R4 clinical data into OMOP CDM v5.4 datasets. "
        "Powered by Google Whistle Mapping Language.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and register routers
    from src.presentation.api.mapping_router import router as mapping_router
    from src.presentation.api.pipeline_router import router as pipeline_router
    from src.presentation.api.source_router import router as source_router

    app.include_router(source_router, prefix="/api/v1")
    app.include_router(mapping_router, prefix="/api/v1")
    app.include_router(pipeline_router, prefix="/api/v1")

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        return HealthResponse()

    return app


app = create_app()
