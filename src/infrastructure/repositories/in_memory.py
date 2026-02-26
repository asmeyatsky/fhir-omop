"""
In-Memory Repository Implementations

Architectural Intent:
- Simple in-memory storage for development and testing
- Implements all repository ports from domain layer
- Will be replaced by PostgreSQL repositories in production
"""
from __future__ import annotations

from src.domain.entities.mapping_config import MappingConfiguration
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.source_connection import SourceConnection


class InMemorySourceConnectionRepository:
    """In-memory implementation of SourceConnectionRepositoryPort."""

    def __init__(self) -> None:
        self._store: dict[str, SourceConnection] = {}

    async def save(self, connection: SourceConnection) -> None:
        self._store[connection.id] = connection

    async def get_by_id(self, id: str) -> SourceConnection | None:
        return self._store.get(id)

    async def list_all(self) -> list[SourceConnection]:
        return list(self._store.values())

    async def delete(self, id: str) -> None:
        self._store.pop(id, None)


class InMemoryMappingConfigRepository:
    """In-memory implementation of MappingConfigRepositoryPort."""

    def __init__(self) -> None:
        self._store: dict[str, MappingConfiguration] = {}

    async def save(self, config: MappingConfiguration) -> None:
        self._store[config.id] = config

    async def get_by_id(self, id: str) -> MappingConfiguration | None:
        return self._store.get(id)

    async def list_all(self) -> list[MappingConfiguration]:
        return list(self._store.values())

    async def delete(self, id: str) -> None:
        self._store.pop(id, None)


class InMemoryPipelineRepository:
    """In-memory implementation of PipelineRepositoryPort."""

    def __init__(self) -> None:
        self._store: dict[str, Pipeline] = {}

    async def save(self, pipeline: Pipeline) -> None:
        self._store[pipeline.id] = pipeline

    async def get_by_id(self, id: str) -> Pipeline | None:
        return self._store.get(id)

    async def list_all(self) -> list[Pipeline]:
        return list(self._store.values())

    async def delete(self, id: str) -> None:
        self._store.pop(id, None)


class InMemoryEventBus:
    """In-memory event bus for development. Logs events."""

    def __init__(self) -> None:
        self.published_events: list = []

    async def publish(self, events: list) -> None:
        self.published_events.extend(events)
