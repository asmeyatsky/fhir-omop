"""
Residency Ports

Architectural Intent:
- Interfaces for data residency enforcement
"""
from __future__ import annotations

from typing import Protocol


class ResidencyEnforcementPort(Protocol):
    def validate_endpoint(self, hostname: str) -> bool:
        """Check if an endpoint hostname is within allowed regions."""
        ...

    def is_internal_network(self, hostname: str) -> bool:
        """Check if hostname resolves to an internal/private network."""
        ...
