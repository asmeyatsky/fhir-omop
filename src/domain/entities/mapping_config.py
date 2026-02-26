"""
Mapping Configuration Entity

Architectural Intent:
- Aggregate root for FHIR-to-OMOP mapping configurations
- Holds field mappings and generated Whistle code
- Business rule: must have at least one field mapping to be valid
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum

from src.domain.events.event_base import DomainEvent
from src.domain.value_objects.fhir import FHIRResourceType
from src.domain.value_objects.mapping import FieldMapping, MappingTemplate
from src.domain.value_objects.omop import OMOPTable


class MappingStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"


@dataclass(frozen=True)
class MappingConfiguration:
    """Aggregate root: a complete mapping from a FHIR resource to an OMOP table."""
    id: str
    name: str
    source_resource: FHIRResourceType
    target_table: OMOPTable
    field_mappings: tuple[FieldMapping, ...]
    whistle_code: str
    status: MappingStatus
    version: str
    created_at: datetime
    updated_at: datetime
    template_id: str | None = None
    domain_events: tuple[DomainEvent, ...] = field(default=())

    @staticmethod
    def from_template(
        id: str,
        name: str,
        template: MappingTemplate,
    ) -> MappingConfiguration:
        """Create a mapping configuration from a pre-built template."""
        now = datetime.now(UTC)
        return MappingConfiguration(
            id=id,
            name=name,
            source_resource=template.source_resource,
            target_table=template.target_table,
            field_mappings=template.field_mappings,
            whistle_code=template.whistle_code,
            status=MappingStatus.VALIDATED,
            version=template.version,
            template_id=template.template_id,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def create_custom(
        id: str,
        name: str,
        source_resource: FHIRResourceType,
        target_table: OMOPTable,
        field_mappings: tuple[FieldMapping, ...],
        whistle_code: str,
    ) -> MappingConfiguration:
        if not field_mappings:
            raise ValueError("At least one field mapping is required")
        now = datetime.now(UTC)
        return MappingConfiguration(
            id=id,
            name=name,
            source_resource=source_resource,
            target_table=target_table,
            field_mappings=field_mappings,
            whistle_code=whistle_code,
            status=MappingStatus.DRAFT,
            version="1.0.0",
            created_at=now,
            updated_at=now,
        )

    def add_field_mapping(self, mapping: FieldMapping) -> MappingConfiguration:
        return replace(
            self,
            field_mappings=self.field_mappings + (mapping,),
            updated_at=datetime.now(UTC),
        )

    def update_whistle_code(self, code: str) -> MappingConfiguration:
        return replace(self, whistle_code=code, updated_at=datetime.now(UTC))

    def validate(self) -> MappingConfiguration:
        if not self.field_mappings:
            raise ValueError("Cannot validate mapping with no field mappings")
        return replace(self, status=MappingStatus.VALIDATED, updated_at=datetime.now(UTC))

    def activate(self) -> MappingConfiguration:
        if self.status != MappingStatus.VALIDATED:
            raise ValueError("Only validated mappings can be activated")
        return replace(self, status=MappingStatus.ACTIVE, updated_at=datetime.now(UTC))

    @property
    def is_active(self) -> bool:
        return self.status == MappingStatus.ACTIVE
