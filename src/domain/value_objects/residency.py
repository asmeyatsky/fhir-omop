"""
Data Residency Value Objects

Architectural Intent:
- Enforces Saudi data residency requirements
- Data must remain within KSA or approved regions
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResidencyPolicy:
    """Data residency policy — controls where data can be stored/processed."""
    allowed_regions: tuple[str, ...] = ("SA",)  # Saudi Arabia by default
    enforce_on_source: bool = True  # Validate source server location
    enforce_on_target: bool = True  # Validate target database location
    allow_internal_networks: bool = True  # Allow 10.x, 172.16.x, 192.168.x
