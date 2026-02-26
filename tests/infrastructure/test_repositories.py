"""
Infrastructure Tests: In-Memory Repositories

Test repository CRUD operations.
"""
import pytest

from src.domain.entities.source_connection import SourceConnection
from src.domain.value_objects.fhir import AuthMethod, FHIRServerType
from src.infrastructure.repositories.in_memory import (
    InMemoryEventBus,
    InMemorySourceConnectionRepository,
)


class TestInMemorySourceConnectionRepository:
    @pytest.mark.asyncio
    async def test_save_and_get(self):
        repo = InMemorySourceConnectionRepository()
        conn = SourceConnection.create(
            id="1", name="Test", base_url="https://test.com",
            server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
        )
        await repo.save(conn)
        retrieved = await repo.get_by_id("1")
        assert retrieved is not None
        assert retrieved.name == "Test"

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self):
        repo = InMemorySourceConnectionRepository()
        assert await repo.get_by_id("missing") is None

    @pytest.mark.asyncio
    async def test_list_all(self):
        repo = InMemorySourceConnectionRepository()
        for i in range(3):
            conn = SourceConnection.create(
                id=str(i), name=f"Conn {i}", base_url=f"https://test{i}.com",
                server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
            )
            await repo.save(conn)
        all_conns = await repo.list_all()
        assert len(all_conns) == 3

    @pytest.mark.asyncio
    async def test_delete(self):
        repo = InMemorySourceConnectionRepository()
        conn = SourceConnection.create(
            id="1", name="Test", base_url="https://test.com",
            server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
        )
        await repo.save(conn)
        await repo.delete("1")
        assert await repo.get_by_id("1") is None

    @pytest.mark.asyncio
    async def test_save_overwrites(self):
        repo = InMemorySourceConnectionRepository()
        conn = SourceConnection.create(
            id="1", name="Original", base_url="https://test.com",
            server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
        )
        await repo.save(conn)
        updated = conn.mark_testing()
        await repo.save(updated)
        retrieved = await repo.get_by_id("1")
        assert retrieved.status.value == "testing"


class TestInMemoryEventBus:
    @pytest.mark.asyncio
    async def test_publishes_events(self):
        bus = InMemoryEventBus()
        await bus.publish(["event1", "event2"])
        assert len(bus.published_events) == 2
