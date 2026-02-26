"""
Domain Unit Tests: SourceConnection

Pure domain logic tests — no mocks, no infrastructure.
Tests business rules and state transitions.
"""
from datetime import UTC, datetime

import pytest

from src.domain.entities.source_connection import ConnectionStatus, SourceConnection
from src.domain.events.pipeline_events import SourceConnectionTestedEvent
from src.domain.value_objects.fhir import AuthMethod, FHIRServerType


class TestSourceConnectionCreate:
    def test_create_valid_connection(self):
        conn = SourceConnection.create(
            id="conn-1",
            name="Test HAPI",
            base_url="https://hapi.fhir.org/baseR4",
            server_type=FHIRServerType.HAPI,
            auth_method=AuthMethod.API_KEY,
        )
        assert conn.id == "conn-1"
        assert conn.name == "Test HAPI"
        assert conn.endpoint.base_url == "https://hapi.fhir.org/baseR4"
        assert conn.status == ConnectionStatus.CREATED
        assert conn.is_usable is False

    def test_create_strips_whitespace(self):
        conn = SourceConnection.create(
            id="conn-1",
            name="  My Server  ",
            base_url="  https://example.com/fhir/  ",
            server_type=FHIRServerType.CUSTOM,
            auth_method=AuthMethod.BASIC_AUTH,
        )
        assert conn.name == "My Server"
        assert conn.endpoint.base_url == "https://example.com/fhir"

    def test_create_empty_name_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            SourceConnection.create(
                id="conn-1", name="", base_url="https://x.com",
                server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
            )

    def test_create_empty_url_raises(self):
        with pytest.raises(ValueError, match="Base URL cannot be empty"):
            SourceConnection.create(
                id="conn-1", name="Test", base_url="  ",
                server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
            )


class TestSourceConnectionStateTransitions:
    def _make_connection(self) -> SourceConnection:
        return SourceConnection.create(
            id="conn-1", name="Test", base_url="https://hapi.fhir.org/baseR4",
            server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
        )

    def test_mark_testing(self):
        conn = self._make_connection()
        testing = conn.mark_testing()
        assert testing.status == ConnectionStatus.TESTING
        assert conn.status == ConnectionStatus.CREATED  # immutability

    def test_mark_active_with_capabilities(self):
        conn = self._make_connection().mark_testing()
        active = conn.mark_active(capabilities=("Patient", "Encounter"))
        assert active.status == ConnectionStatus.ACTIVE
        assert active.capabilities == ("Patient", "Encounter")
        assert active.is_usable is True
        assert active.last_tested_at is not None
        assert active.error_message is None

    def test_mark_active_emits_event(self):
        conn = self._make_connection().mark_testing()
        active = conn.mark_active(capabilities=())
        events = [e for e in active.domain_events if isinstance(e, SourceConnectionTestedEvent)]
        assert len(events) == 1
        assert events[0].success is True

    def test_mark_failed(self):
        conn = self._make_connection().mark_testing()
        failed = conn.mark_failed("Connection refused")
        assert failed.status == ConnectionStatus.FAILED
        assert failed.error_message == "Connection refused"
        assert failed.is_usable is False

    def test_mark_failed_emits_event(self):
        conn = self._make_connection().mark_testing()
        failed = conn.mark_failed("timeout")
        events = [e for e in failed.domain_events if isinstance(e, SourceConnectionTestedEvent)]
        assert len(events) == 1
        assert events[0].success is False

    def test_disable(self):
        conn = self._make_connection()
        disabled = conn.disable()
        assert disabled.status == ConnectionStatus.DISABLED
        assert disabled.is_usable is False


class TestFHIREndpoint:
    def test_capability_statement_url(self):
        conn = SourceConnection.create(
            id="1", name="T", base_url="https://hapi.fhir.org/baseR4",
            server_type=FHIRServerType.HAPI, auth_method=AuthMethod.API_KEY,
        )
        assert conn.endpoint.capability_statement_url() == "https://hapi.fhir.org/baseR4/metadata"
