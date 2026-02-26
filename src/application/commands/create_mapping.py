"""
Create Mapping Configuration Use Case

Architectural Intent:
- Creates a mapping config from a pre-built template
- Templates are the primary Phase 1 path for mapping creation
"""
from __future__ import annotations

import uuid

from src.application.dtos.mapping_dtos import CreateMappingFromTemplateDTO, MappingConfigResponseDTO
from src.domain.entities.mapping_config import MappingConfiguration
from src.domain.ports.repository_ports import MappingConfigRepositoryPort
from src.domain.value_objects.mapping import MappingTemplate


class CreateMappingFromTemplateUseCase:
    def __init__(
        self,
        repository: MappingConfigRepositoryPort,
        templates: dict[str, MappingTemplate],
    ) -> None:
        self._repository = repository
        self._templates = templates

    async def execute(self, dto: CreateMappingFromTemplateDTO) -> MappingConfigResponseDTO:
        template = self._templates.get(dto.template_id)
        if template is None:
            available = ", ".join(self._templates.keys())
            raise ValueError(
                f"Template '{dto.template_id}' not found. Available: {available}"
            )

        config = MappingConfiguration.from_template(
            id=str(uuid.uuid4()),
            name=dto.name,
            template=template,
        )
        config = config.activate()

        await self._repository.save(config)

        return MappingConfigResponseDTO(
            id=config.id,
            name=config.name,
            source_resource=config.source_resource.value,
            target_table=config.target_table.value,
            field_count=len(config.field_mappings),
            status=config.status.value,
            version=config.version,
            template_id=config.template_id,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
