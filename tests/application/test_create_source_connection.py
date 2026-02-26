"""
Application Layer Tests: Use Cases

Use case tests with mocked ports — verify orchestration logic.
"""
import pytest

from src.application.commands.create_source_connection import CreateSourceConnectionUseCase
from src.application.commands.verify_source_connection import VerifySourceConnectionUseCase
from src.application.dtos.source_dtos import CreateSourceConnectionDTO
from src.domain.entities.source_connection import ConnectionStatus
from src.domain.value_objects.fhir import AuthMethod, FHIRServerType
from src.infrastructure.repositories.in_memory import InMemoryEventBus, InMemorySourceConnectionRepository


class TestCreateSourceConnectionUseCase:
    @pytest.mark.asyncio
    async def test_creates_connection_successfully(self):
        repo = InMemorySourceConnectionRepository()
        event_bus = InMemoryEventBus()
        use_case = CreateSourceConnectionUseCase(repository=repo, event_bus=event_bus)

        result = await use_case.execute(
            CreateSourceConnectionDTO(
                name="HAPI Dev",
                base_url="https://hapi.fhir.org/baseR4",
                server_type=FHIRServerType.HAPI,
                auth_method=AuthMethod.API_KEY,
            )
        )

        assert result.name == "HAPI Dev"
        assert result.status == "created"
        assert result.base_url == "https://hapi.fhir.org/baseR4"

        # Verify persistence
        stored = await repo.get_by_id(result.id)
        assert stored is not None
        assert stored.name == "HAPI Dev"

    @pytest.mark.asyncio
    async def test_invalid_name_raises(self):
        repo = InMemorySourceConnectionRepository()
        event_bus = InMemoryEventBus()
        use_case = CreateSourceConnectionUseCase(repository=repo, event_bus=event_bus)

        with pytest.raises(ValueError):
            await use_case.execute(
                CreateSourceConnectionDTO(
                    name="",
                    base_url="https://example.com",
                    server_type=FHIRServerType.HAPI,
                    auth_method=AuthMethod.API_KEY,
                )
            )


class MockFHIRClient:
    """Mock FHIR client for testing."""

    def __init__(self, success: bool = True, resources: list[str] | None = None):
        self._success = success
        self._resources = resources or ["Patient", "Encounter", "Observation"]

    async def test_connection(self, endpoint) -> tuple[bool, str]:
        if self._success:
            return True, "Connected"
        return False, "Connection refused"

    async def get_capability_statement(self, endpoint) -> dict:
        return {"fhirVersion": "4.0.1"}

    async def get_supported_resources(self, endpoint) -> list[str]:
        return self._resources

    async def extract_resources(self, endpoint, resource_type, batch_size=1000):
        return None


class TestVerifySourceConnectionUseCase:
    @pytest.mark.asyncio
    async def test_successful_connection_test(self):
        repo = InMemorySourceConnectionRepository()
        event_bus = InMemoryEventBus()
        fhir_client = MockFHIRClient(success=True)

        # First create a connection
        create_uc = CreateSourceConnectionUseCase(repository=repo, event_bus=event_bus)
        created = await create_uc.execute(
            CreateSourceConnectionDTO(
                name="Test Server",
                base_url="https://hapi.fhir.org/baseR4",
                server_type=FHIRServerType.HAPI,
                auth_method=AuthMethod.API_KEY,
            )
        )

        # Then test it
        test_uc = VerifySourceConnectionUseCase(
            repository=repo, fhir_client=fhir_client, event_bus=event_bus,
        )
        result = await test_uc.execute(created.id)

        assert result.status == "active"
        assert "Patient" in result.capabilities
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_failed_connection_test(self):
        repo = InMemorySourceConnectionRepository()
        event_bus = InMemoryEventBus()
        fhir_client = MockFHIRClient(success=False)

        create_uc = CreateSourceConnectionUseCase(repository=repo, event_bus=event_bus)
        created = await create_uc.execute(
            CreateSourceConnectionDTO(
                name="Bad Server",
                base_url="https://bad.example.com",
                server_type=FHIRServerType.CUSTOM,
                auth_method=AuthMethod.BASIC_AUTH,
            )
        )

        test_uc = VerifySourceConnectionUseCase(
            repository=repo, fhir_client=fhir_client, event_bus=event_bus,
        )
        result = await test_uc.execute(created.id)

        assert result.status == "failed"
        assert result.error_message == "Connection refused"

    @pytest.mark.asyncio
    async def test_nonexistent_connection_raises(self):
        repo = InMemorySourceConnectionRepository()
        event_bus = InMemoryEventBus()
        fhir_client = MockFHIRClient()

        test_uc = VerifySourceConnectionUseCase(
            repository=repo, fhir_client=fhir_client, event_bus=event_bus,
        )
        with pytest.raises(ValueError, match="not found"):
            await test_uc.execute("nonexistent-id")
