"""
PostgreSQL OMOP Writer Adapter

Architectural Intent:
- Infrastructure adapter implementing OMOPWriterPort
- Writes transformed OMOP records to PostgreSQL
- Handles schema validation against OMOP CDM v5.4
- Supports incremental loading (Phase 1 default)
"""
from __future__ import annotations

from typing import Any

import asyncpg

from src.domain.value_objects.omop import OMOPRecord, OMOPTable

# OMOP CDM v5.4 required columns per table
OMOP_SCHEMA: dict[str, list[str]] = {
    "person": [
        "person_id", "gender_concept_id", "year_of_birth", "month_of_birth",
        "day_of_birth", "race_concept_id", "ethnicity_concept_id",
        "person_source_value", "gender_source_value",
    ],
    "visit_occurrence": [
        "visit_occurrence_id", "person_id", "visit_concept_id",
        "visit_start_date", "visit_end_date", "visit_type_concept_id",
        "visit_source_value",
    ],
    "condition_occurrence": [
        "condition_occurrence_id", "person_id", "condition_concept_id",
        "condition_start_date", "condition_type_concept_id",
        "condition_source_value",
    ],
    "measurement": [
        "measurement_id", "person_id", "measurement_concept_id",
        "measurement_date", "measurement_type_concept_id",
        "value_as_number", "unit_concept_id", "measurement_source_value",
    ],
    "observation": [
        "observation_id", "person_id", "observation_concept_id",
        "observation_date", "observation_type_concept_id",
        "observation_source_value",
    ],
}


class PostgreSQLOMOPWriter:
    """Adapter for writing OMOP records to PostgreSQL."""

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._connection_string, min_size=2, max_size=10)
        return self._pool

    async def test_connection(self) -> tuple[bool, str]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                return True, f"Connected: {version}"
        except Exception as e:
            return False, f"Connection failed: {e}"

    async def validate_schema(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                for table_name, columns in OMOP_SCHEMA.items():
                    exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
                        table_name,
                    )
                    if not exists:
                        errors.append(f"Table '{table_name}' not found")
                        continue

                    existing_cols = await conn.fetch(
                        "SELECT column_name FROM information_schema.columns WHERE table_name = $1",
                        table_name,
                    )
                    existing_names = {row["column_name"] for row in existing_cols}
                    for col in columns:
                        if col not in existing_names:
                            errors.append(f"Column '{table_name}.{col}' not found")
        except Exception as e:
            errors.append(f"Schema validation error: {e}")

        return len(errors) == 0, errors

    async def write_records(self, records: list[OMOPRecord]) -> int:
        if not records:
            return 0

        pool = await self._get_pool()
        written = 0

        # Group records by table
        by_table: dict[str, list[dict]] = {}
        for record in records:
            table = record.target_table.value
            if table not in by_table:
                by_table[table] = []
            by_table[table].append(record.data)

        async with pool.acquire() as conn:
            for table_name, rows in by_table.items():
                if not rows:
                    continue
                # Use first row to determine columns
                columns = list(rows[0].keys())
                placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
                col_names = ", ".join(columns)
                query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

                for row in rows:
                    try:
                        values = [row.get(col) for col in columns]
                        await conn.execute(query, *values)
                        written += 1
                    except Exception:
                        # Record goes to dead-letter queue in Phase 2
                        continue

        return written

    async def get_record_count(self, table: OMOPTable) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(f"SELECT COUNT(*) FROM {table.value}")

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
