"""
HAPI FHIR Client Adapter

Architectural Intent:
- Infrastructure adapter implementing FHIRClientPort
- Communicates with HAPI FHIR R4 servers via REST API
- Zero business logic — pure transport and data conversion

MCP Integration:
- Phase 2 will expose this as an MCP server tool for agent-driven extraction
"""
from __future__ import annotations

import httpx

from src.domain.value_objects.fhir import FHIRBundle, FHIREndpoint, FHIRResourceType


class HAPIFHIRClient:
    """Adapter for HAPI FHIR R4 servers."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    async def test_connection(self, endpoint: FHIREndpoint) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    endpoint.capability_statement_url(),
                    headers={"Accept": "application/fhir+json"},
                )
                if response.status_code == 200:
                    data = response.json()
                    fhir_version = data.get("fhirVersion", "unknown")
                    return True, f"Connected. FHIR version: {fhir_version}"
                return False, f"HTTP {response.status_code}: {response.text[:200]}"
        except httpx.ConnectError as e:
            return False, f"Connection failed: {e}"
        except Exception as e:
            return False, f"Error: {e}"

    async def get_capability_statement(self, endpoint: FHIREndpoint) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                endpoint.capability_statement_url(),
                headers={"Accept": "application/fhir+json"},
            )
            response.raise_for_status()
            return response.json()

    async def get_supported_resources(self, endpoint: FHIREndpoint) -> list[str]:
        cap = await self.get_capability_statement(endpoint)
        resources: list[str] = []
        for rest in cap.get("rest", []):
            for resource in rest.get("resource", []):
                rtype = resource.get("type")
                if rtype:
                    resources.append(rtype)
        return resources

    async def extract_resources(
        self,
        endpoint: FHIREndpoint,
        resource_type: FHIRResourceType,
        batch_size: int = 1000,
    ) -> FHIRBundle:
        resources: list[dict] = []
        url = f"{endpoint.base_url}/{resource_type.value}?_count={batch_size}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            while url:
                response = await client.get(
                    url,
                    headers={"Accept": "application/fhir+json"},
                )
                response.raise_for_status()
                bundle = response.json()

                for entry in bundle.get("entry", []):
                    resource = entry.get("resource")
                    if resource:
                        resources.append(resource)

                # Follow pagination
                url = self._get_next_link(bundle)

        return FHIRBundle(resource_type=resource_type, resources=tuple(resources))

    @staticmethod
    def _get_next_link(bundle: dict) -> str | None:
        for link in bundle.get("link", []):
            if link.get("relation") == "next":
                return link.get("url")
        return None
