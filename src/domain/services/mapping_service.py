"""
Mapping Domain Service

Architectural Intent:
- Domain service for FHIR-to-OMOP transformation logic
- Applies field mappings to produce OMOP records
- Delegates vocabulary resolution to VocabularyDomainService
- Delegates Whistle execution to port
"""
from __future__ import annotations

from src.domain.entities.mapping_config import MappingConfiguration
from src.domain.ports.whistle_engine_port import WhistleEnginePort
from src.domain.services.vocabulary_service import VocabularyDomainService
from src.domain.value_objects.fhir import FHIRBundle
from src.domain.value_objects.omop import OMOPRecord


class MappingDomainService:
    """Transforms FHIR resources to OMOP records using mapping configurations."""

    def __init__(
        self,
        whistle_engine: WhistleEnginePort,
        vocabulary_service: VocabularyDomainService,
    ) -> None:
        self._whistle = whistle_engine
        self._vocabulary = vocabulary_service

    async def transform_bundle(
        self,
        bundle: FHIRBundle,
        mapping: MappingConfiguration,
    ) -> list[OMOPRecord]:
        """Transform a FHIR bundle into OMOP records using the mapping configuration."""
        if not mapping.is_active and mapping.status.value != "validated":
            raise ValueError("Mapping must be validated or active for transformation")

        records: list[OMOPRecord] = []
        for resource in bundle.resources:
            transformed = await self._whistle.execute(
                whistle_code=mapping.whistle_code,
                input_resource=resource,
            )
            if transformed is not None:
                record = OMOPRecord(
                    target_table=mapping.target_table,
                    data=transformed,
                    source_fhir_id=resource.get("id", "unknown"),
                    mapping_version=mapping.version,
                )
                records.append(record)
        return records
