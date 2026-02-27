"""Tests for Audit Middleware."""
import pytest
from fastapi.testclient import TestClient

from src.infrastructure.middleware.audit_middleware import (
    _classify_action,
    _classify_event,
    _extract_resource,
    set_global_audit_log,
)
from src.infrastructure.repositories.in_memory import InMemoryAuditLog
from src.domain.entities.audit_entry import AuditAction, AuditEventType
from src.presentation.api.app import create_app


class TestClassifiers:
    def test_classify_auth_event(self):
        assert _classify_event("/api/v1/auth/login") == AuditEventType.AUTH

    def test_classify_pipeline_event(self):
        assert _classify_event("/api/v1/pipelines") == AuditEventType.PIPELINE

    def test_classify_admin_event(self):
        assert _classify_event("/api/v1/users") == AuditEventType.ADMIN

    def test_classify_default_event(self):
        assert _classify_event("/api/v1/sources") == AuditEventType.DATA_ACCESS

    def test_classify_login_success(self):
        assert _classify_action("POST", "/api/v1/auth/login", 200) == AuditAction.LOGIN_SUCCESS

    def test_classify_login_failure(self):
        assert _classify_action("POST", "/api/v1/auth/login", 401) == AuditAction.LOGIN_FAILURE

    def test_classify_get_action(self):
        assert _classify_action("GET", "/api/v1/sources", 200) == AuditAction.READ

    def test_classify_post_action(self):
        assert _classify_action("POST", "/api/v1/sources", 201) == AuditAction.CREATE

    def test_classify_delete_action(self):
        assert _classify_action("DELETE", "/api/v1/sources/abc", 204) == AuditAction.DELETE


class TestResourceExtraction:
    def test_extract_resource_with_id(self):
        rtype, rid = _extract_resource("/api/v1/sources/abc-123")
        assert rtype == "sources"
        assert rid == "abc-123"

    def test_extract_resource_without_id(self):
        rtype, rid = _extract_resource("/api/v1/sources")
        assert rtype == "sources"
        assert rid is None

    def test_extract_short_path(self):
        rtype, rid = _extract_resource("/api")
        assert rtype is None
        assert rid is None


class TestAuditMiddlewareIntegration:
    def test_health_exempt(self):
        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200

            # The lifespan sets audit_log on the container; get it from the module ref
            from src.infrastructure.middleware import audit_middleware
            audit_log = audit_middleware._audit_log_ref
            assert audit_log is not None
            health_entries = [e for e in audit_log._store if e.http_path == "/health"]
            assert len(health_entries) == 0

    def test_api_call_audited(self):
        app = create_app()
        with TestClient(app) as client:
            client.get("/api/v1/sources")

            from src.infrastructure.middleware import audit_middleware
            audit_log = audit_middleware._audit_log_ref
            assert audit_log is not None
            source_entries = [e for e in audit_log._store if e.http_path == "/api/v1/sources"]
            assert len(source_entries) >= 1
            entry = source_entries[0]
            assert entry.http_method == "GET"
            assert entry.checksum is not None
