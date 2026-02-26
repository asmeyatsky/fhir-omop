"""
Pipeline Domain Events

Architectural Intent:
- Events emitted during pipeline lifecycle
- Used for audit trail and cross-context communication
"""
from __future__ import annotations

from dataclasses import dataclass

from src.domain.events.event_base import DomainEvent


@dataclass(frozen=True)
class PipelineCreatedEvent(DomainEvent):
    pipeline_name: str = ""


@dataclass(frozen=True)
class PipelineStartedEvent(DomainEvent):
    pass


@dataclass(frozen=True)
class PipelineStageCompletedEvent(DomainEvent):
    stage_name: str = ""
    records_processed: int = 0


@dataclass(frozen=True)
class PipelineCompletedEvent(DomainEvent):
    total_records: int = 0
    error_count: int = 0


@dataclass(frozen=True)
class PipelineFailedEvent(DomainEvent):
    stage_name: str = ""
    error_message: str = ""


@dataclass(frozen=True)
class SourceConnectionTestedEvent(DomainEvent):
    success: bool = False
    message: str = ""
