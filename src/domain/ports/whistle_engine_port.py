"""
Whistle Engine Port

Architectural Intent:
- Interface for Google Whistle mapping engine
- Defined in domain layer, implemented in infrastructure
- Executes .wstl code against FHIR resources to produce OMOP-structured output
"""
from __future__ import annotations

from typing import Protocol


class WhistleEnginePort(Protocol):
    """Port for the Whistle data transformation engine."""

    async def execute(
        self,
        whistle_code: str,
        input_resource: dict,
    ) -> dict | None:
        """Execute Whistle code against a single FHIR resource. Returns transformed dict or None on skip."""
        ...

    async def validate_code(self, whistle_code: str) -> tuple[bool, list[str]]:
        """Validate Whistle code syntax. Returns (is_valid, errors)."""
        ...
