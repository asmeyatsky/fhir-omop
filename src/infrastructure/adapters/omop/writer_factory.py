"""
OMOP Writer Factory

Architectural Intent:
- Infrastructure adapter implementing OMOPWriterFactoryPort
- Creates PostgreSQLOMOPWriter instances from connection strings
"""
from __future__ import annotations

from src.infrastructure.adapters.omop.postgresql_writer import PostgreSQLOMOPWriter


class PostgreSQLOMOPWriterFactory:
    """Creates PostgreSQLOMOPWriter instances."""

    def create_writer(self, connection_string: str) -> PostgreSQLOMOPWriter:
        return PostgreSQLOMOPWriter(connection_string)
