"""
PostgreSQL Repository Implementations

Architectural Intent:
- Persistent storage for all aggregate roots
- Implements domain repository ports using asyncpg
- JSON serialization for nested value objects (field_mappings, stage_results)
- Domain events excluded from persistence (handled separately by event bus)
"""
from __future__ import annotations

import json
from datetime import datetime

import asyncpg

from src.domain.entities.mapping_config import MappingConfiguration, MappingStatus
from src.domain.entities.pipeline import Pipeline, PipelineStage, PipelineStatus, StageResult
from src.domain.entities.source_connection import ConnectionStatus, SourceConnection
from src.domain.value_objects.fhir import AuthMethod, FHIREndpoint, FHIRResourceType, FHIRServerType
from src.domain.value_objects.mapping import FieldMapping, TransformationType
from src.domain.value_objects.omop import OMOPTable


def _parse_datetime(val: object) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    return None


class PostgreSQLSourceConnectionRepository:
    """PostgreSQL implementation of SourceConnectionRepositoryPort."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save(self, connection: SourceConnection) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO source_connection
                    (id, name, base_url, server_type, auth_method, status,
                     created_at, last_tested_at, capabilities, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    base_url = EXCLUDED.base_url,
                    server_type = EXCLUDED.server_type,
                    auth_method = EXCLUDED.auth_method,
                    status = EXCLUDED.status,
                    last_tested_at = EXCLUDED.last_tested_at,
                    capabilities = EXCLUDED.capabilities,
                    error_message = EXCLUDED.error_message
                """,
                connection.id,
                connection.name,
                connection.endpoint.base_url,
                connection.endpoint.server_type.value,
                connection.endpoint.auth_method.value,
                connection.status.value,
                connection.created_at,
                connection.last_tested_at,
                json.dumps(list(connection.capabilities)),
                connection.error_message,
            )

    async def get_by_id(self, id: str) -> SourceConnection | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM source_connection WHERE id = $1", id
            )
        if row is None:
            return None
        return self._row_to_entity(row)

    async def list_all(self) -> list[SourceConnection]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM source_connection ORDER BY created_at DESC")
        return [self._row_to_entity(row) for row in rows]

    async def delete(self, id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM source_connection WHERE id = $1", id)

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> SourceConnection:
        caps = json.loads(row["capabilities"]) if row["capabilities"] else []
        return SourceConnection(
            id=str(row["id"]),
            name=row["name"],
            endpoint=FHIREndpoint(
                base_url=row["base_url"],
                server_type=FHIRServerType(row["server_type"]),
                auth_method=AuthMethod(row["auth_method"]),
            ),
            status=ConnectionStatus(row["status"]),
            created_at=row["created_at"],
            last_tested_at=_parse_datetime(row["last_tested_at"]),
            capabilities=tuple(caps),
            error_message=row["error_message"],
        )


class PostgreSQLMappingConfigRepository:
    """PostgreSQL implementation of MappingConfigRepositoryPort."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save(self, config: MappingConfiguration) -> None:
        field_mappings_json = json.dumps([
            {
                "source_path": fm.source_path,
                "target_column": fm.target_column,
                "transformation": fm.transformation.value,
                "parameters": list(fm.parameters),
            }
            for fm in config.field_mappings
        ])

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO mapping_configuration
                    (id, name, source_resource, target_table, field_mappings,
                     whistle_code, status, version, template_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    field_mappings = EXCLUDED.field_mappings,
                    whistle_code = EXCLUDED.whistle_code,
                    status = EXCLUDED.status,
                    version = EXCLUDED.version,
                    updated_at = EXCLUDED.updated_at
                """,
                config.id,
                config.name,
                config.source_resource.value,
                config.target_table.value,
                field_mappings_json,
                config.whistle_code,
                config.status.value,
                config.version,
                config.template_id,
                config.created_at,
                config.updated_at,
            )

    async def get_by_id(self, id: str) -> MappingConfiguration | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM mapping_configuration WHERE id = $1", id
            )
        if row is None:
            return None
        return self._row_to_entity(row)

    async def list_all(self) -> list[MappingConfiguration]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM mapping_configuration ORDER BY created_at DESC"
            )
        return [self._row_to_entity(row) for row in rows]

    async def delete(self, id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM mapping_configuration WHERE id = $1", id)

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> MappingConfiguration:
        raw_mappings = json.loads(row["field_mappings"]) if row["field_mappings"] else []
        field_mappings = tuple(
            FieldMapping(
                source_path=fm["source_path"],
                target_column=fm["target_column"],
                transformation=TransformationType(fm["transformation"]),
                parameters=tuple(tuple(p) for p in fm.get("parameters", [])),
            )
            for fm in raw_mappings
        )
        return MappingConfiguration(
            id=str(row["id"]),
            name=row["name"],
            source_resource=FHIRResourceType(row["source_resource"]),
            target_table=OMOPTable(row["target_table"]),
            field_mappings=field_mappings,
            whistle_code=row["whistle_code"],
            status=MappingStatus(row["status"]),
            version=row["version"],
            template_id=row["template_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class PostgreSQLPipelineRepository:
    """PostgreSQL implementation of PipelineRepositoryPort."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save(self, pipeline: Pipeline) -> None:
        stage_results_json = json.dumps([
            {
                "stage": sr.stage.value,
                "records_in": sr.records_in,
                "records_out": sr.records_out,
                "error_count": sr.error_count,
                "started_at": sr.started_at.isoformat(),
                "completed_at": sr.completed_at.isoformat(),
                "errors": list(sr.errors),
            }
            for sr in pipeline.stage_results
        ])

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pipeline
                    (id, name, source_connection_id, mapping_config_ids,
                     target_connection_string, status, created_at, started_at,
                     completed_at, current_stage, stage_results, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    started_at = EXCLUDED.started_at,
                    completed_at = EXCLUDED.completed_at,
                    current_stage = EXCLUDED.current_stage,
                    stage_results = EXCLUDED.stage_results,
                    error_message = EXCLUDED.error_message
                """,
                pipeline.id,
                pipeline.name,
                pipeline.source_connection_id,
                json.dumps(list(pipeline.mapping_config_ids)),
                pipeline.target_connection_string,
                pipeline.status.value,
                pipeline.created_at,
                pipeline.started_at,
                pipeline.completed_at,
                pipeline.current_stage.value if pipeline.current_stage else None,
                stage_results_json,
                pipeline.error_message,
            )

    async def get_by_id(self, id: str) -> Pipeline | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM pipeline WHERE id = $1", id)
        if row is None:
            return None
        return self._row_to_entity(row)

    async def list_all(self) -> list[Pipeline]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM pipeline ORDER BY created_at DESC")
        return [self._row_to_entity(row) for row in rows]

    async def delete(self, id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM pipeline WHERE id = $1", id)

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> Pipeline:
        raw_stages = json.loads(row["stage_results"]) if row["stage_results"] else []
        stage_results = tuple(
            StageResult(
                stage=PipelineStage(sr["stage"]),
                records_in=sr["records_in"],
                records_out=sr["records_out"],
                error_count=sr["error_count"],
                started_at=datetime.fromisoformat(sr["started_at"]),
                completed_at=datetime.fromisoformat(sr["completed_at"]),
                errors=tuple(sr.get("errors", [])),
            )
            for sr in raw_stages
        )
        mapping_ids = json.loads(row["mapping_config_ids"]) if row["mapping_config_ids"] else []
        return Pipeline(
            id=str(row["id"]),
            name=row["name"],
            source_connection_id=str(row["source_connection_id"]),
            mapping_config_ids=tuple(mapping_ids),
            target_connection_string=row["target_connection_string"],
            status=PipelineStatus(row["status"]),
            created_at=row["created_at"],
            started_at=_parse_datetime(row["started_at"]),
            completed_at=_parse_datetime(row["completed_at"]),
            current_stage=PipelineStage(row["current_stage"]) if row["current_stage"] else None,
            stage_results=stage_results,
            error_message=row["error_message"],
        )
