"""DTOs for Pipeline operations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreatePipelineDTO:
    name: str
    source_connection_id: str
    mapping_config_ids: list[str]
    target_connection_string: str


@dataclass(frozen=True)
class StageResultDTO:
    stage: str
    records_in: int
    records_out: int
    error_count: int
    started_at: datetime
    completed_at: datetime


@dataclass(frozen=True)
class PipelineResponseDTO:
    id: str
    name: str
    source_connection_id: str
    mapping_config_ids: list[str]
    status: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    current_stage: str | None
    stage_results: list[StageResultDTO]
    total_records: int
    total_errors: int
    error_message: str | None
