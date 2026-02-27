"""Tests for Security Middleware: Rate Limiter, Security Headers, Input Validation."""
import json

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.middleware.input_validation import _check_json_depth
from src.infrastructure.middleware.rate_limiter import TokenBucket
from src.presentation.api.app import create_app


class TestTokenBucket:
    def test_initial_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.tokens == 10.0

    def test_consume_success(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.consume() is True
        assert bucket.tokens == 9.0

    def test_consume_exhausted(self):
        bucket = TokenBucket(capacity=2, refill_rate=0.1)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False

    def test_retry_after(self):
        bucket = TokenBucket(capacity=1, refill_rate=1.0)
        bucket.consume()
        assert bucket.retry_after >= 1


class TestJsonDepthCheck:
    def test_flat_object(self):
        assert _check_json_depth({"a": 1, "b": 2}) == 1

    def test_nested_object(self):
        obj = {"a": {"b": {"c": 1}}}
        assert _check_json_depth(obj) == 3

    def test_deeply_nested(self):
        obj = {"level": None}
        current = obj
        for i in range(25):
            current["level"] = {"level": None}
            current = current["level"]
        assert _check_json_depth(obj) > 20

    def test_empty_dict(self):
        assert _check_json_depth({}) == 0

    def test_list(self):
        assert _check_json_depth([1, 2, 3]) == 1

    def test_scalar(self):
        assert _check_json_depth("hello") == 0


class TestSecurityHeadersIntegration:
    @pytest.fixture
    def client(self):
        app = create_app()
        with TestClient(app) as c:
            yield c

    def test_health_has_security_headers(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.headers["x-content-type-options"] == "nosniff"
        assert resp.headers["x-frame-options"] == "DENY"
        assert "max-age=31536000" in resp.headers["strict-transport-security"]
        assert "x-request-id" in resp.headers

    def test_request_id_passthrough(self, client):
        resp = client.get("/health", headers={"x-request-id": "test-123"})
        assert resp.headers["x-request-id"] == "test-123"

    def test_cache_control(self, client):
        resp = client.get("/health")
        assert "no-store" in resp.headers.get("cache-control", "")


class TestRateLimiterIntegration:
    def test_rate_limit_not_hit_on_normal_use(self):
        app = create_app()
        with TestClient(app) as client:
            for _ in range(10):
                resp = client.get("/health")
                assert resp.status_code == 200


class TestInputValidationIntegration:
    @pytest.fixture
    def client(self):
        app = create_app()
        with TestClient(app) as c:
            yield c

    def test_large_content_length_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            headers={"content-length": "999999999", "content-type": "application/json"},
            content=b"{}",
        )
        assert resp.status_code == 413
