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


class InMemoryUserRepository:
    """In-memory implementation of UserRepositoryPort."""

    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    async def save(self, user: object) -> None:
        self._store[user.id] = user  # type: ignore[attr-defined]

    async def get_by_id(self, id: str) -> object | None:
        return self._store.get(id)

    async def get_by_email(self, email: str) -> object | None:
        for u in self._store.values():
            if getattr(u, "email", None) == email:
                return u
        return None

    async def list_all(self) -> list:
        return list(self._store.values())

    async def delete(self, id: str) -> None:
        self._store.pop(id, None)


class InMemoryTenantRepository:
    """In-memory implementation of TenantRepositoryPort."""

    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    async def save(self, tenant: object) -> None:
        self._store[tenant.id] = tenant  # type: ignore[attr-defined]

    async def get_by_id(self, id: str) -> object | None:
        return self._store.get(id)

    async def list_all(self) -> list:
        return list(self._store.values())

    async def delete(self, id: str) -> None:
        self._store.pop(id, None)


class InMemoryConsentRepository:
    """In-memory implementation of ConsentRepositoryPort."""

    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    async def save(self, consent: object) -> None:
        self._store[consent.id] = consent  # type: ignore[attr-defined]

    async def get_by_id(self, id: str) -> object | None:
        return self._store.get(id)

    async def get_active_consents(self, patient_id: str, tenant_id: str) -> list:
        return [
            c for c in self._store.values()
            if getattr(c, "patient_id", None) == patient_id
            and getattr(c, "tenant_id", None) == tenant_id
            and getattr(c, "status", None).value == "active"
        ]

    async def list_by_tenant(
        self, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> list:
        results = [
            c for c in self._store.values()
            if getattr(c, "tenant_id", None) == tenant_id
        ]
        return results[offset:offset + limit]

    async def delete(self, id: str) -> None:
        self._store.pop(id, None)


class InMemoryAuditLog:
    """In-memory implementation of AuditLogPort for testing."""

    def __init__(self) -> None:
        self._store: list[object] = []

    async def record(self, entry: object) -> None:
        self._store.append(entry)

    async def get_by_id(self, id: str) -> object | None:
        for e in self._store:
            if getattr(e, "id", None) == id:
                return e
        return None

    async def query(
        self,
        tenant_id: str | None = None,
        actor_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        results = self._store
        if tenant_id:
            results = [e for e in results if getattr(e, "tenant_id", None) == tenant_id]
        if actor_id:
            results = [e for e in results if getattr(e, "actor_id", None) == actor_id]
        if event_type:
            results = [
                e for e in results
                if getattr(getattr(e, "event_type", None), "value", None) == event_type
            ]
        # Sort by timestamp descending
        results = sorted(results, key=lambda e: getattr(e, "timestamp", ""), reverse=True)
        return results[offset:offset + limit]

    async def count(
        self,
        tenant_id: str | None = None,
        actor_id: str | None = None,
        event_type: str | None = None,
    ) -> int:
        results = self._store
        if tenant_id:
            results = [e for e in results if getattr(e, "tenant_id", None) == tenant_id]
        if actor_id:
            results = [e for e in results if getattr(e, "actor_id", None) == actor_id]
        if event_type:
            results = [
                e for e in results
                if getattr(getattr(e, "event_type", None), "value", None) == event_type
            ]
        return len(results)


class InMemoryEventBus:
    """In-memory event bus for development. Logs events."""

    def __init__(self) -> None:
        self.published_events: list = []

    async def publish(self, events: list) -> None:
        self.published_events.extend(events)
