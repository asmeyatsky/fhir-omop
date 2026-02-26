"""
Test Source Connection Use Case

Architectural Intent:
- Tests connectivity to a configured FHIR server
- Updates connection status based on result
- Discovers server capabilities on success
"""
from __future__ import annotations

from src.application.dtos.source_dtos import SourceConnectionResponseDTO
from src.domain.ports.fhir_client_port import FHIRClientPort
from src.domain.ports.repository_ports import EventBusPort, SourceConnectionRepositoryPort


class VerifySourceConnectionUseCase:
    def __init__(
        self,
        repository: SourceConnectionRepositoryPort,
        fhir_client: FHIRClientPort,
        event_bus: EventBusPort,
    ) -> None:
        self._repository = repository
        self._fhir_client = fhir_client
        self._event_bus = event_bus

    async def execute(self, connection_id: str) -> SourceConnectionResponseDTO:
        connection = await self._repository.get_by_id(connection_id)
        if connection is None:
            raise ValueError(f"Source connection {connection_id} not found")

        connection = connection.mark_testing()
        await self._repository.save(connection)

        success, message = await self._fhir_client.test_connection(connection.endpoint)

        if success:
            resources = await self._fhir_client.get_supported_resources(connection.endpoint)
            connection = connection.mark_active(capabilities=tuple(resources))
        else:
            connection = connection.mark_failed(message)

        await self._repository.save(connection)
        if connection.domain_events:
            await self._event_bus.publish(list(connection.domain_events))

        return SourceConnectionResponseDTO(
            id=connection.id,
            name=connection.name,
            base_url=connection.endpoint.base_url,
            server_type=connection.endpoint.server_type.value,
            auth_method=connection.endpoint.auth_method.value,
            status=connection.status.value,
            created_at=connection.created_at,
            last_tested_at=connection.last_tested_at,
            capabilities=list(connection.capabilities),
            error_message=connection.error_message,
        )
