"""DTOs for Mapping operations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateMappingFromTemplateDTO:
    name: str
    template_id: str


@dataclass(frozen=True)
class MappingConfigResponseDTO:
    id: str
    name: str
    source_resource: str
    target_table: str
    field_count: int
    status: str
    version: str
    template_id: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class MappingTemplateResponseDTO:
    template_id: str
    name: str
    description: str
    source_resource: str
    target_table: str
    field_count: int
    version: str
