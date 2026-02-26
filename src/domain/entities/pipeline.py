"""
Pipeline Entity

Architectural Intent:
- Aggregate root for end-to-end FHIR→OMOP pipeline execution
- Manages pipeline lifecycle: created → running → completed/failed
- Tracks stage-level progress and error counts
- Business rules: source must be active, mappings must be active

Parallelization Notes:
- Phase 1 uses sequential execution (extract → transform → load)
- Pipeline entity is parallel-ready via stage tracking
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum

from src.domain.events.event_base import DomainEvent
from src.domain.events.pipeline_events import (
    PipelineCompletedEvent,
    PipelineCreatedEvent,
    PipelineFailedEvent,
    PipelineStageCompletedEvent,
    PipelineStartedEvent,
)


class PipelineStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStage(str, Enum):
    EXTRACT = "extract"
    TRANSFORM = "transform"
    LOAD = "load"
    QUALITY_CHECK = "quality_check"


@dataclass(frozen=True)
class StageResult:
    """Result of a single pipeline stage execution."""
    stage: PipelineStage
    records_in: int
    records_out: int
    error_count: int
    started_at: datetime
    completed_at: datetime
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class Pipeline:
    """Aggregate root: an end-to-end FHIR-to-OMOP transformation pipeline."""
    id: str
    name: str
    source_connection_id: str
    mapping_config_ids: tuple[str, ...]
    target_connection_string: str
    status: PipelineStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    current_stage: PipelineStage | None = None
    stage_results: tuple[StageResult, ...] = ()
    error_message: str | None = None
    domain_events: tuple[DomainEvent, ...] = field(default=())

    @staticmethod
    def create(
        id: str,
        name: str,
        source_connection_id: str,
        mapping_config_ids: tuple[str, ...],
        target_connection_string: str,
    ) -> Pipeline:
        if not name.strip():
            raise ValueError("Pipeline name cannot be empty")
        if not mapping_config_ids:
            raise ValueError("At least one mapping configuration is required")

        now = datetime.now(UTC)
        return Pipeline(
            id=id,
            name=name.strip(),
            source_connection_id=source_connection_id,
            mapping_config_ids=mapping_config_ids,
            target_connection_string=target_connection_string,
            status=PipelineStatus.CREATED,
            created_at=now,
            domain_events=(
                PipelineCreatedEvent(aggregate_id=id, pipeline_name=name.strip()),
            ),
        )

    def start(self) -> Pipeline:
        if self.status != PipelineStatus.CREATED:
            raise ValueError(f"Cannot start pipeline in {self.status} status")
        now = datetime.now(UTC)
        return replace(
            self,
            status=PipelineStatus.RUNNING,
            started_at=now,
            current_stage=PipelineStage.EXTRACT,
            domain_events=self.domain_events + (
                PipelineStartedEvent(aggregate_id=self.id),
            ),
        )

    def complete_stage(self, result: StageResult) -> Pipeline:
        if self.status != PipelineStatus.RUNNING:
            raise ValueError("Cannot complete stage on non-running pipeline")

        next_stage = self._next_stage(result.stage)
        return replace(
            self,
            stage_results=self.stage_results + (result,),
            current_stage=next_stage,
            domain_events=self.domain_events + (
                PipelineStageCompletedEvent(
                    aggregate_id=self.id,
                    stage_name=result.stage.value,
                    records_processed=result.records_out,
                ),
            ),
        )

    def complete(self) -> Pipeline:
        if self.status != PipelineStatus.RUNNING:
            raise ValueError("Cannot complete non-running pipeline")
        now = datetime.now(UTC)
        total = sum(r.records_out for r in self.stage_results)
        errors = sum(r.error_count for r in self.stage_results)
        return replace(
            self,
            status=PipelineStatus.COMPLETED,
            completed_at=now,
            current_stage=None,
            domain_events=self.domain_events + (
                PipelineCompletedEvent(
                    aggregate_id=self.id, total_records=total, error_count=errors
                ),
            ),
        )

    def fail(self, stage: PipelineStage, error: str) -> Pipeline:
        now = datetime.now(UTC)
        return replace(
            self,
            status=PipelineStatus.FAILED,
            completed_at=now,
            error_message=error,
            domain_events=self.domain_events + (
                PipelineFailedEvent(
                    aggregate_id=self.id, stage_name=stage.value, error_message=error
                ),
            ),
        )

    def cancel(self) -> Pipeline:
        if self.status not in (PipelineStatus.CREATED, PipelineStatus.RUNNING):
            raise ValueError(f"Cannot cancel pipeline in {self.status} status")
        return replace(
            self,
            status=PipelineStatus.CANCELLED,
            completed_at=datetime.now(UTC),
            current_stage=None,
        )

    @property
    def total_records_processed(self) -> int:
        if not self.stage_results:
            return 0
        return self.stage_results[-1].records_out

    @property
    def total_errors(self) -> int:
        return sum(r.error_count for r in self.stage_results)

    @staticmethod
    def _next_stage(current: PipelineStage) -> PipelineStage | None:
        order = [PipelineStage.EXTRACT, PipelineStage.TRANSFORM, PipelineStage.LOAD]
        try:
            idx = order.index(current)
            return order[idx + 1] if idx + 1 < len(order) else None
        except ValueError:
            return None
