"""
Athena Vocabulary Service Adapter

Architectural Intent:
- Infrastructure adapter implementing VocabularyLookupPort
- Queries OHDSI Athena for standard concept lookups
- Phase 1: uses local vocabulary cache (PostgreSQL-backed)
- Phase 2: adds USAGI-style fuzzy matching
"""
from __future__ import annotations

import asyncpg

from src.domain.value_objects.omop import ConceptId


class AthenaVocabularyService:
    """Adapter for OMOP vocabulary lookups via local Athena cache."""

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._connection_string, min_size=1, max_size=5)
        return self._pool

    async def find_standard_concept(
        self,
        source_code: str,
        source_vocabulary_id: str,
    ) -> ConceptId | None:
        """
        Find the OMOP Standard Concept for a source code.

        Uses CONCEPT + CONCEPT_RELATIONSHIP tables:
        1. Find source concept by code + vocabulary
        2. Follow 'Maps to' relationship to standard concept
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Find standard concept via Maps to relationship
            row = await conn.fetchrow(
                """
                SELECT c2.concept_id, c2.concept_name, c2.vocabulary_id, c2.domain_id
                FROM concept c1
                JOIN concept_relationship cr ON c1.concept_id = cr.concept_id_1
                JOIN concept c2 ON cr.concept_id_2 = c2.concept_id
                WHERE c1.concept_code = $1
                  AND c1.vocabulary_id = $2
                  AND cr.relationship_id = 'Maps to'
                  AND c2.standard_concept = 'S'
                  AND c2.invalid_reason IS NULL
                LIMIT 1
                """,
                source_code,
                source_vocabulary_id,
            )
            if row:
                return ConceptId(
                    concept_id=row["concept_id"],
                    concept_name=row["concept_name"],
                    vocabulary_id=row["vocabulary_id"],
                    domain_id=row["domain_id"],
                )
            return None

    async def search_concepts(
        self,
        query: str,
        vocabulary_id: str | None = None,
        domain_id: str | None = None,
        limit: int = 20,
    ) -> list[ConceptId]:
        pool = await self._get_pool()
        conditions = ["c.standard_concept = 'S'", "c.invalid_reason IS NULL"]
        params: list = []
        idx = 1

        conditions.append(f"c.concept_name ILIKE ${idx}")
        params.append(f"%{query}%")
        idx += 1

        if vocabulary_id:
            conditions.append(f"c.vocabulary_id = ${idx}")
            params.append(vocabulary_id)
            idx += 1

        if domain_id:
            conditions.append(f"c.domain_id = ${idx}")
            params.append(domain_id)
            idx += 1

        where = " AND ".join(conditions)
        sql = f"""
            SELECT concept_id, concept_name, vocabulary_id, domain_id
            FROM concept c
            WHERE {where}
            ORDER BY concept_name
            LIMIT {limit}
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [
                ConceptId(
                    concept_id=row["concept_id"],
                    concept_name=row["concept_name"],
                    vocabulary_id=row["vocabulary_id"],
                    domain_id=row["domain_id"],
                )
                for row in rows
            ]

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
