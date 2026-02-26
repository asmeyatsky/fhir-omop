"""
OMOP Writer Port

Architectural Intent:
- Interface for writing transformed records to OMOP CDM databases
- Defined in domain layer, implemented in infrastructure
- Supports batch writes and schema validation
"""
from __future__ import annotations

from typing import Protocol

from src.domain.value_objects.omop import OMOPRecord, OMOPTable


class OMOPWriterPort(Protocol):
    """Port for writing data to OMOP CDM target databases."""

    async def write_records(self, records: list[OMOPRecord]) -> int:
        """Write a batch of OMOP records. Returns count of successfully written records."""
        ...

    async def validate_schema(self) -> tuple[bool, list[str]]:
        """Validate that the target database has a valid OMOP CDM v5.4 schema."""
        ...

    async def test_connection(self) -> tuple[bool, str]:
        """Test connectivity to the target database."""
        ...

    async def get_record_count(self, table: OMOPTable) -> int:
        """Get the current record count for a given OMOP table."""
        ...


class OMOPWriterFactoryPort(Protocol):
    """Factory port for creating OMOP writers from connection strings."""

    def create_writer(self, connection_string: str) -> OMOPWriterPort:
        ...
