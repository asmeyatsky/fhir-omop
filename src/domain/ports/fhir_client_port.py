"""
FHIR Client Port

Architectural Intent:
- Interface for FHIR server communication
- Defined in domain layer, implemented in infrastructure
- Supports connection testing, resource extraction, and capability introspection
"""
from __future__ import annotations

from typing import Protocol

from src.domain.value_objects.fhir import FHIRBundle, FHIREndpoint, FHIRResourceType


class FHIRClientPort(Protocol):
    """Port for interacting with FHIR R4 servers."""

    async def test_connection(self, endpoint: FHIREndpoint) -> tuple[bool, str]:
        """Test connectivity and return (success, message)."""
        ...

    async def get_capability_statement(self, endpoint: FHIREndpoint) -> dict:
        """Fetch the server's CapabilityStatement."""
        ...

    async def get_supported_resources(self, endpoint: FHIREndpoint) -> list[str]:
        """List resource types supported by the server."""
        ...

    async def extract_resources(
        self,
        endpoint: FHIREndpoint,
        resource_type: FHIRResourceType,
        batch_size: int = 1000,
    ) -> FHIRBundle:
        """Extract FHIR resources of the given type."""
        ...
