"""
Data Residency Service

Architectural Intent:
- Enforces KSA data residency requirements
- Validates source and target endpoints are within allowed regions
- Supports allowed hostname patterns and internal network exemption
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from src.domain.value_objects.residency import ResidencyPolicy


class DataResidencyViolationError(Exception):
    """Raised when data would leave an approved region."""

    def __init__(self, hostname: str, reason: str):
        self.hostname = hostname
        self.reason = reason
        super().__init__(
            f"Data residency violation for '{hostname}': {reason}"
        )


class ResidencyService:
    """Enforces data residency policies for Saudi compliance."""

    def __init__(
        self,
        policy: ResidencyPolicy | None = None,
        allowed_hostnames: tuple[str, ...] | None = None,
    ) -> None:
        self._policy = policy or ResidencyPolicy()
        # Allowed hostname patterns (e.g., internal FHIR servers)
        self._allowed_hostnames = allowed_hostnames or (
            "localhost",
            "127.0.0.1",
            "*.kfshrc.sa",
            "*.moh.gov.sa",
            "*.nphies.sa",
        )

    def validate_url(self, url: str) -> bool:
        """Validate that a URL's host is within allowed regions."""
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        return self.validate_endpoint(hostname)

    def validate_endpoint(self, hostname: str) -> bool:
        """Check if a hostname is within allowed data residency regions."""
        # Check allowed hostname patterns
        for pattern in self._allowed_hostnames:
            if pattern.startswith("*."):
                if hostname.endswith(pattern[1:]):
                    return True
            elif hostname == pattern:
                return True

        # Check internal/private networks
        if self._policy.allow_internal_networks and self._is_private_ip(hostname):
            return True

        # For .sa TLD domains, allow
        if hostname.endswith(".sa"):
            return True

        return False

    def is_internal_network(self, hostname: str) -> bool:
        """Check if hostname is on a private/internal network."""
        return self._is_private_ip(hostname)

    def enforce_source(self, source_url: str) -> None:
        """Enforce residency policy on a FHIR source endpoint."""
        if not self._policy.enforce_on_source:
            return
        if not self.validate_url(source_url):
            parsed = urlparse(source_url)
            raise DataResidencyViolationError(
                parsed.hostname or source_url,
                "Source FHIR server is not within approved Saudi data residency regions. "
                "Only .sa domains, internal networks, and explicitly allowed hosts are permitted.",
            )

    def enforce_target(self, target_url: str) -> None:
        """Enforce residency policy on a target database endpoint."""
        if not self._policy.enforce_on_target:
            return
        if not self.validate_url(target_url):
            parsed = urlparse(target_url)
            raise DataResidencyViolationError(
                parsed.hostname or target_url,
                "Target database is not within approved Saudi data residency regions.",
            )

    @staticmethod
    def _is_private_ip(hostname: str) -> bool:
        """Check if a hostname resolves to a private/internal IP."""
        try:
            addr = ipaddress.ip_address(hostname)
            return addr.is_private or addr.is_loopback
        except ValueError:
            pass

        # Try DNS resolution
        try:
            resolved = socket.gethostbyname(hostname)
            addr = ipaddress.ip_address(resolved)
            return addr.is_private or addr.is_loopback
        except (socket.gaierror, ValueError):
            return False
