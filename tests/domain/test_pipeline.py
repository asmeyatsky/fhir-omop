"""
Domain Unit Tests: Pipeline

Pure domain logic tests — pipeline lifecycle, state transitions, stage tracking.
"""
from datetime import UTC, datetime

import pytest

from src.domain.entities.pipeline import Pipeline, PipelineStage, PipelineStatus, StageResult
from src.domain.events.pipeline_events import (
    PipelineCompletedEvent,
    PipelineCreatedEvent,
    PipelineFailedEvent,
    PipelineStageCompletedEvent,
    PipelineStartedEvent,
)


class TestPipelineCreate:
    def test_create_valid_pipeline(self):
        p = Pipeline.create(
            id="pipe-1",
            name="Patient ETL",
            source_connection_id="src-1",
            mapping_config_ids=("map-1",),
            target_connection_string="postgresql://localhost/omop",
        )
        assert p.id == "pipe-1"
        assert p.status == PipelineStatus.CREATED
        assert p.total_records_processed == 0

    def test_create_emits_event(self):
        p = Pipeline.create(
            id="pipe-1", name="Test", source_connection_id="src-1",
            mapping_config_ids=("map-1",), target_connection_string="pg://localhost/omop",
        )
        assert len(p.domain_events) == 1
        assert isinstance(p.domain_events[0], PipelineCreatedEvent)

    def test_create_empty_name_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Pipeline.create(
                id="1", name="", source_connection_id="s",
                mapping_config_ids=("m",), target_connection_string="pg://x",
            )

    def test_create_no_mappings_raises(self):
        with pytest.raises(ValueError, match="At least one mapping"):
            Pipeline.create(
                id="1", name="Test", source_connection_id="s",
                mapping_config_ids=(), target_connection_string="pg://x",
            )


class TestPipelineLifecycle:
    def _make_pipeline(self) -> Pipeline:
        return Pipeline.create(
            id="pipe-1", name="Test Pipeline", source_connection_id="src-1",
            mapping_config_ids=("map-1",), target_connection_string="pg://localhost/omop",
        )

    def _make_stage_result(self, stage: PipelineStage, records_out: int = 10) -> StageResult:
        now = datetime.now(UTC)
        return StageResult(
            stage=stage, records_in=10, records_out=records_out,
            error_count=0, started_at=now, completed_at=now,
        )

    def test_start_pipeline(self):
        p = self._make_pipeline()
        started = p.start()
        assert started.status == PipelineStatus.RUNNING
        assert started.current_stage == PipelineStage.EXTRACT
        assert started.started_at is not None

    def test_start_emits_event(self):
        p = self._make_pipeline().start()
        events = [e for e in p.domain_events if isinstance(e, PipelineStartedEvent)]
        assert len(events) == 1

    def test_cannot_start_twice(self):
        p = self._make_pipeline().start()
        with pytest.raises(ValueError, match="Cannot start"):
            p.start()

    def test_complete_stage_advances(self):
        p = self._make_pipeline().start()
        result = self._make_stage_result(PipelineStage.EXTRACT)
        p2 = p.complete_stage(result)
        assert p2.current_stage == PipelineStage.TRANSFORM
        assert len(p2.stage_results) == 1

    def test_complete_stage_emits_event(self):
        p = self._make_pipeline().start()
        result = self._make_stage_result(PipelineStage.EXTRACT, records_out=42)
        p2 = p.complete_stage(result)
        stage_events = [e for e in p2.domain_events if isinstance(e, PipelineStageCompletedEvent)]
        assert len(stage_events) == 1
        assert stage_events[0].records_processed == 42

    def test_full_lifecycle(self):
        p = self._make_pipeline().start()
        p = p.complete_stage(self._make_stage_result(PipelineStage.EXTRACT, 100))
        p = p.complete_stage(self._make_stage_result(PipelineStage.TRANSFORM, 95))
        p = p.complete_stage(self._make_stage_result(PipelineStage.LOAD, 95))
        p = p.complete()

        assert p.status == PipelineStatus.COMPLETED
        assert p.completed_at is not None
        assert p.total_records_processed == 95
        assert len(p.stage_results) == 3

    def test_complete_emits_event(self):
        p = self._make_pipeline().start()
        p = p.complete_stage(self._make_stage_result(PipelineStage.EXTRACT))
        p = p.complete_stage(self._make_stage_result(PipelineStage.TRANSFORM))
        p = p.complete_stage(self._make_stage_result(PipelineStage.LOAD))
        p = p.complete()
        completed_events = [e for e in p.domain_events if isinstance(e, PipelineCompletedEvent)]
        assert len(completed_events) == 1

    def test_fail_pipeline(self):
        p = self._make_pipeline().start()
        failed = p.fail(PipelineStage.EXTRACT, "Connection timeout")
        assert failed.status == PipelineStatus.FAILED
        assert failed.error_message == "Connection timeout"

    def test_fail_emits_event(self):
        p = self._make_pipeline().start()
        failed = p.fail(PipelineStage.TRANSFORM, "Bad data")
        fail_events = [e for e in failed.domain_events if isinstance(e, PipelineFailedEvent)]
        assert len(fail_events) == 1
        assert fail_events[0].error_message == "Bad data"

    def test_cancel_created_pipeline(self):
        p = self._make_pipeline()
        cancelled = p.cancel()
        assert cancelled.status == PipelineStatus.CANCELLED

    def test_cancel_running_pipeline(self):
        p = self._make_pipeline().start()
        cancelled = p.cancel()
        assert cancelled.status == PipelineStatus.CANCELLED
        assert cancelled.current_stage is None

    def test_cannot_cancel_completed(self):
        p = self._make_pipeline().start()
        p = p.complete_stage(self._make_stage_result(PipelineStage.EXTRACT))
        p = p.complete_stage(self._make_stage_result(PipelineStage.TRANSFORM))
        p = p.complete_stage(self._make_stage_result(PipelineStage.LOAD))
        p = p.complete()
        with pytest.raises(ValueError, match="Cannot cancel"):
            p.cancel()

    def test_immutability_preserved(self):
        p1 = self._make_pipeline()
        p2 = p1.start()
        assert p1.status == PipelineStatus.CREATED
        assert p2.status == PipelineStatus.RUNNING
        assert p1 is not p2
