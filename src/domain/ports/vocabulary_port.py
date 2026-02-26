"""
Vocabulary Lookup Port

Architectural Intent:
- Interface for OMOP vocabulary lookups (Athena)
- Defined in domain layer, implemented in infrastructure
- Maps source codes to OMOP Standard Concepts
"""
from __future__ import annotations

from typing import Protocol

from src.domain.value_objects.omop import ConceptId


class VocabularyLookupPort(Protocol):
    """Port for OMOP vocabulary lookups."""

    async def find_standard_concept(
        self,
        source_code: str,
        source_vocabulary_id: str,
    ) -> ConceptId | None:
        """Find the OMOP Standard Concept for a source code. Returns None if not found."""
        ...

    async def search_concepts(
        self,
        query: str,
        vocabulary_id: str | None = None,
        domain_id: str | None = None,
        limit: int = 20,
    ) -> list[ConceptId]:
        """Search for OMOP concepts by name or code."""
        ...
