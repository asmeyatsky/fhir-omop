"""
Tests for PostgreSQL Repository Implementations

Tests serialization/deserialization logic without requiring a live database.
Uses in-memory verification of the entity mapping methods.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.mapping_config import MappingConfiguration, MappingStatus
from src.domain.entities.pipeline import Pipeline, PipelineStage, PipelineStatus, StageResult
from src.domain.entities.source_connection import ConnectionStatus, SourceConnection
from src.domain.value_objects.fhir import AuthMethod, FHIREndpoint, FHIRResourceType, FHIRServerType
from src.domain.value_objects.mapping import FieldMapping, TransformationType
from src.domain.value_objects.omop import OMOPTable
from src.infrastructure.repositories.postgresql_repos import (
    PostgreSQLMappingConfigRepository,
    PostgreSQLPipelineRepository,
    PostgreSQLSourceConnectionRepository,
)


class TestSourceConnectionSerialization:
    def _make_row(self, **overrides) -> dict:
        defaults = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "HAPI FHIR Dev",
            "base_url": "https://hapi.fhir.org/baseR4",
            "server_type": "hapi",
            "auth_method": "api_key",
            "status": "active",
            "created_at": datetime(2024, 1, 1, tzinfo=UTC),
            "last_tested_at": datetime(2024, 1, 2, tzinfo=UTC),
            "capabilities": json.dumps(["Patient", "Encounter"]),
            "error_message": None,
        }
        defaults.update(overrides)
        return defaults

    def test_row_to_entity(self):
        row = self._make_row()
        entity = PostgreSQLSourceConnectionRepository._row_to_entity(row)

        assert entity.id == "550e8400-e29b-41d4-a716-446655440000"
        assert entity.name == "HAPI FHIR Dev"
        assert entity.endpoint.base_url == "https://hapi.fhir.org/baseR4"
        assert entity.endpoint.server_type == FHIRServerType.HAPI
        assert entity.endpoint.auth_method == AuthMethod.API_KEY
        assert entity.status == ConnectionStatus.ACTIVE
        assert entity.capabilities == ("Patient", "Encounter")
        assert entity.error_message is None

    def test_row_to_entity_with_error(self):
        row = self._make_row(status="failed", error_message="Connection refused")
        entity = PostgreSQLSourceConnectionRepository._row_to_entity(row)

        assert entity.status == ConnectionStatus.FAILED
        assert entity.error_message == "Connection refused"

    def test_row_to_entity_empty_capabilities(self):
        row = self._make_row(capabilities=json.dumps([]))
        entity = PostgreSQLSourceConnectionRepository._row_to_entity(row)
        assert entity.capabilities == ()

    def test_row_to_entity_null_last_tested(self):
        row = self._make_row(last_tested_at=None)
        entity = PostgreSQLSourceConnectionRepository._row_to_entity(row)
        assert entity.last_tested_at is None


class TestMappingConfigSerialization:
    def _make_row(self, **overrides) -> dict:
        defaults = {
            "id": "mapping-001",
            "name": "Patient to Person",
            "source_resource": "Patient",
            "target_table": "person",
            "field_mappings": json.dumps([
                {
                    "source_path": "birthDate",
                    "target_column": "year_of_birth",
                    "transformation": "date_extract",
                    "parameters": [["component", "year"]],
                }
            ]),
            "whistle_code": '{"mappings": []}',
            "status": "active",
            "version": "1.0.0",
            "template_id": "patient-to-person",
            "created_at": datetime(2024, 1, 1, tzinfo=UTC),
            "updated_at": datetime(2024, 1, 1, tzinfo=UTC),
        }
        defaults.update(overrides)
        return defaults

    def test_row_to_entity(self):
        row = self._make_row()
        entity = PostgreSQLMappingConfigRepository._row_to_entity(row)

        assert entity.id == "mapping-001"
        assert entity.name == "Patient to Person"
        assert entity.source_resource == FHIRResourceType.PATIENT
        assert entity.target_table == OMOPTable.PERSON
        assert entity.status == MappingStatus.ACTIVE
        assert len(entity.field_mappings) == 1
        assert entity.field_mappings[0].source_path == "birthDate"
        assert entity.field_mappings[0].transformation == TransformationType.DATE_EXTRACT
        assert entity.field_mappings[0].get_parameter("component") == "year"

    def test_row_to_entity_no_template(self):
        row = self._make_row(template_id=None)
        entity = PostgreSQLMappingConfigRepository._row_to_entity(row)
        assert entity.template_id is None


class TestPipelineSerialization:
    def _make_row(self, **overrides) -> dict:
        stage_results = [
            {
                "stage": "extract",
                "records_in": 0,
                "records_out": 100,
                "error_count": 0,
                "started_at": "2024-01-01T00:00:00+00:00",
                "completed_at": "2024-01-01T00:01:00+00:00",
                "errors": [],
            }
        ]
        defaults = {
            "id": "pipeline-001",
            "name": "Test Pipeline",
            "source_connection_id": "source-001",
            "mapping_config_ids": json.dumps(["mapping-001"]),
            "target_connection_string": "postgresql://localhost/omop",
            "status": "completed",
            "created_at": datetime(2024, 1, 1, tzinfo=UTC),
            "started_at": datetime(2024, 1, 1, tzinfo=UTC),
            "completed_at": datetime(2024, 1, 1, 0, 5, tzinfo=UTC),
            "current_stage": None,
            "stage_results": json.dumps(stage_results),
            "error_message": None,
        }
        defaults.update(overrides)
        return defaults

    def test_row_to_entity(self):
        row = self._make_row()
        entity = PostgreSQLPipelineRepository._row_to_entity(row)

        assert entity.id == "pipeline-001"
        assert entity.name == "Test Pipeline"
        assert entity.status == PipelineStatus.COMPLETED
        assert entity.mapping_config_ids == ("mapping-001",)
        assert len(entity.stage_results) == 1
        assert entity.stage_results[0].stage == PipelineStage.EXTRACT
        assert entity.stage_results[0].records_out == 100
        assert entity.current_stage is None

    def test_row_to_entity_running(self):
        row = self._make_row(status="running", current_stage="transform", completed_at=None)
        entity = PostgreSQLPipelineRepository._row_to_entity(row)

        assert entity.status == PipelineStatus.RUNNING
        assert entity.current_stage == PipelineStage.TRANSFORM
        assert entity.completed_at is None

    def test_row_to_entity_failed(self):
        row = self._make_row(status="failed", error_message="Connection timeout")
        entity = PostgreSQLPipelineRepository._row_to_entity(row)

        assert entity.status == PipelineStatus.FAILED
        assert entity.error_message == "Connection timeout"

    def test_row_to_entity_no_stage_results(self):
        row = self._make_row(stage_results=json.dumps([]))
        entity = PostgreSQLPipelineRepository._row_to_entity(row)
        assert entity.stage_results == ()


class TestDatabaseManager:
    async def test_health_check_import(self):
        """Verify DatabaseManager can be imported and instantiated."""
        from src.infrastructure.config.database import DatabaseManager
        mgr = DatabaseManager("postgresql://test:test@localhost:5432/test")
        assert mgr._connection_string == "postgresql://test:test@localhost:5432/test"
