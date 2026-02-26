"""
Create Source Connection Use Case

Architectural Intent:
- Orchestrates creation of a new FHIR source connection
- Validates input, creates domain entity, persists via repository port
"""
from __future__ import annotations

import uuid

from src.application.dtos.source_dtos import CreateSourceConnectionDTO, SourceConnectionResponseDTO
from src.domain.entities.source_connection import SourceConnection
from src.domain.ports.repository_ports import EventBusPort, SourceConnectionRepositoryPort


class CreateSourceConnectionUseCase:
    def __init__(
        self,
        repository: SourceConnectionRepositoryPort,
        event_bus: EventBusPort,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus

    async def execute(self, dto: CreateSourceConnectionDTO) -> SourceConnectionResponseDTO:
        connection = SourceConnection.create(
            id=str(uuid.uuid4()),
            name=dto.name,
            base_url=dto.base_url,
            server_type=dto.server_type,
            auth_method=dto.auth_method,
        )

        await self._repository.save(connection)
        if connection.domain_events:
            await self._event_bus.publish(list(connection.domain_events))

        return self._to_response(connection)

    @staticmethod
    def _to_response(conn: SourceConnection) -> SourceConnectionResponseDTO:
        return SourceConnectionResponseDTO(
            id=conn.id,
            name=conn.name,
            base_url=conn.endpoint.base_url,
            server_type=conn.endpoint.server_type.value,
            auth_method=conn.endpoint.auth_method.value,
            status=conn.status.value,
            created_at=conn.created_at,
            last_tested_at=conn.last_tested_at,
            capabilities=list(conn.capabilities),
            error_message=conn.error_message,
        )
