"""
Vocabulary Domain Service

Architectural Intent:
- Domain service for concept mapping logic
- Maps source codes (SNOMED, LOINC, ICD-10, RxNorm) to OMOP concept_ids
- Business rules for vocabulary resolution live here
- Infrastructure (Athena API) is behind a port
"""
from __future__ import annotations

from src.domain.ports.vocabulary_port import VocabularyLookupPort
from src.domain.value_objects.omop import ConceptId


class VocabularyDomainService:
    """Resolves source terminology codes to OMOP Standard Concepts."""

    def __init__(self, vocabulary_lookup: VocabularyLookupPort) -> None:
        self._lookup = vocabulary_lookup

    async def resolve_concept(
        self,
        source_code: str,
        source_vocabulary: str,
    ) -> ConceptId:
        """Resolve a source code to an OMOP concept, falling back to unmapped."""
        concept = await self._lookup.find_standard_concept(
            source_code=source_code,
            source_vocabulary_id=source_vocabulary,
        )
        return concept if concept is not None else ConceptId.unmapped()

    async def resolve_batch(
        self,
        codes: list[tuple[str, str]],
    ) -> list[ConceptId]:
        """Resolve multiple (code, vocabulary) pairs. Returns in same order."""
        results: list[ConceptId] = []
        for code, vocab in codes:
            results.append(await self.resolve_concept(code, vocab))
        return results
