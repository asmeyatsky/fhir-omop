"""
Integration Tests: FastAPI API Endpoints

Tests the full HTTP request → use case → response flow.
"""
import pytest
from fastapi.testclient import TestClient

from src.presentation.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert data["service"] == "fhir-omop-accelerator"


class TestSourceConnectionAPI:
    def test_create_source_connection(self, client):
        response = client.post("/api/v1/sources", json={
            "name": "HAPI Dev",
            "base_url": "https://hapi.fhir.org/baseR4",
            "server_type": "hapi",
            "auth_method": "api_key",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "HAPI Dev"
        assert data["status"] == "created"
        assert data["base_url"] == "https://hapi.fhir.org/baseR4"
        assert "id" in data

    def test_create_source_connection_invalid_name(self, client):
        response = client.post("/api/v1/sources", json={
            "name": "",
            "base_url": "https://example.com",
            "server_type": "hapi",
            "auth_method": "api_key",
        })
        assert response.status_code == 422  # Pydantic validation

    def test_list_source_connections(self, client):
        # Create two connections
        client.post("/api/v1/sources", json={
            "name": "Server 1", "base_url": "https://s1.com",
            "server_type": "hapi", "auth_method": "api_key",
        })
        client.post("/api/v1/sources", json={
            "name": "Server 2", "base_url": "https://s2.com",
            "server_type": "google_healthcare_api", "auth_method": "smart_on_fhir",
        })

        response = client.get("/api/v1/sources")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestMappingAPI:
    def test_list_templates(self, client):
        response = client.get("/api/v1/mappings/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        template_ids = [t["template_id"] for t in data]
        assert "patient-to-person" in template_ids
        assert "encounter-to-visit" in template_ids
        assert "condition-to-condition-occurrence" in template_ids
        assert "observation-to-measurement" in template_ids

    def test_create_mapping_from_template(self, client):
        response = client.post("/api/v1/mappings", json={
            "name": "Patient Mapping",
            "template_id": "patient-to-person",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Patient Mapping"
        assert data["source_resource"] == "Patient"
        assert data["target_table"] == "person"
        assert data["status"] == "active"

    def test_create_mapping_invalid_template(self, client):
        response = client.post("/api/v1/mappings", json={
            "name": "Bad Mapping",
            "template_id": "nonexistent",
        })
        assert response.status_code == 400

    def test_list_mappings(self, client):
        client.post("/api/v1/mappings", json={
            "name": "Mapping 1", "template_id": "patient-to-person",
        })
        response = client.get("/api/v1/mappings")
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestPipelineAPI:
    def test_list_pipelines_empty(self, client):
        response = client.get("/api/v1/pipelines")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_pipeline_missing_source(self, client):
        # Create a mapping first
        mapping_resp = client.post("/api/v1/mappings", json={
            "name": "Test Mapping", "template_id": "patient-to-person",
        })
        mapping_id = mapping_resp.json()["id"]

        response = client.post("/api/v1/pipelines", json={
            "name": "Test Pipeline",
            "source_connection_id": "nonexistent",
            "mapping_config_ids": [mapping_id],
            "target_connection_string": "postgresql://localhost/omop",
        })
        assert response.status_code == 400

    def test_get_nonexistent_pipeline(self, client):
        response = client.get("/api/v1/pipelines/nonexistent-id")
        assert response.status_code == 404
