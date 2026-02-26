"""
Pydantic request/response schemas for the API layer.

Architectural Intent:
- Presentation-layer schemas separate from domain/application DTOs
- Handles JSON serialization and OpenAPI documentation
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# --- Source Connection ---

class CreateSourceConnectionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["HAPI FHIR Dev Server"])
    base_url: str = Field(..., examples=["https://hapi.fhir.org/baseR4"])
    server_type: str = Field(..., examples=["hapi"])
    auth_method: str = Field(..., examples=["api_key"])


class SourceConnectionResponse(BaseModel):
    id: str
    name: str
    base_url: str
    server_type: str
    auth_method: str
    status: str
    created_at: datetime
    last_tested_at: datetime | None = None
    capabilities: list[str] = []
    error_message: str | None = None


# --- Mapping ---

class CreateMappingFromTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    template_id: str = Field(..., examples=["patient-to-person"])


class MappingConfigResponse(BaseModel):
    id: str
    name: str
    source_resource: str
    target_table: str
    field_count: int
    status: str
    version: str
    template_id: str | None = None
    created_at: datetime
    updated_at: datetime


class MappingTemplateResponse(BaseModel):
    template_id: str
    name: str
    description: str
    source_resource: str
    target_table: str
    field_count: int
    version: str


# --- Pipeline ---

class CreatePipelineRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_connection_id: str
    mapping_config_ids: list[str] = Field(..., min_length=1)
    target_connection_string: str = Field(..., examples=["postgresql://localhost:5432/omop"])


class StageResultResponse(BaseModel):
    stage: str
    records_in: int
    records_out: int
    error_count: int
    started_at: datetime
    completed_at: datetime


class PipelineResponse(BaseModel):
    id: str
    name: str
    source_connection_id: str
    mapping_config_ids: list[str]
    status: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    current_stage: str | None = None
    stage_results: list[StageResultResponse] = []
    total_records: int = 0
    total_errors: int = 0
    error_message: str | None = None


# --- Health ---

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    service: str = "fhir-omop-accelerator"
