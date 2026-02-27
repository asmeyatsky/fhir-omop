"""
Target Records API Router

Read-only paginated view of records loaded into the OMOP target database.
Uses OMOP_TARGET_READ_URL (default: postgresql://omop:omop@localhost:5433/omop).
"""
from __future__ import annotations

import os
from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException, Query

# OMOP CDM tables we allow (whitelist to prevent SQL injection)
ALLOWED_TABLES = frozenset({
    "person",
    "visit_occurrence",
    "condition_occurrence",
    "measurement",
    "observation",
    "location",
    "care_site",
    "provider",
})

router = APIRouter(prefix="/target-records", tags=["Target Records"])

_pool: asyncpg.Pool | None = None


def _get_connection_url() -> str | None:
    return os.environ.get(
        "OMOP_TARGET_READ_URL",
        "postgresql://omop:omop@localhost:5433/omop",
    )


async def _get_pool() -> asyncpg.Pool:
    global _pool
    url = _get_connection_url()
    if not url:
        raise HTTPException(
            status_code=503,
            detail="Target records are not configured. Set OMOP_TARGET_READ_URL.",
        )
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                url,
                min_size=1,
                max_size=5,
                command_timeout=30,
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to OMOP target: {e!s}",
            )
    return _pool


@router.get("/tables")
async def list_tables() -> list[dict[str, Any]]:
    """List OMOP tables available for viewing (with row counts)."""
    pool = await _get_pool()
    tables = []
    async with pool.acquire() as conn:
        for name in sorted(ALLOWED_TABLES):
            try:
                count = await conn.fetchval(
                    "SELECT count(*) FROM " + _quote_ident(name),
                )
                tables.append({"name": name, "count": count})
            except asyncpg.UndefinedTableError:
                continue
            except Exception:
                tables.append({"name": name, "count": None})
    return tables


def _quote_ident(name: str) -> str:
    """Quote identifier; name must be in ALLOWED_TABLES."""
    if name not in ALLOWED_TABLES:
        raise ValueError("Invalid table")
    return f'"{name}"'


@router.get("")
async def get_records(
    table: str = Query(..., description="OMOP table name"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Return paginated rows from an OMOP table."""
    if table not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail="Invalid table name")
    pool = await _get_pool()
    qtable = _quote_ident(table)
    async with pool.acquire() as conn:
        try:
            total = await conn.fetchval(f"SELECT count(*) FROM {qtable}")
        except asyncpg.UndefinedTableError:
            raise HTTPException(status_code=404, detail=f"Table {table} not found")
        rows = await conn.fetch(
            f"SELECT * FROM {qtable} ORDER BY 1 LIMIT $1 OFFSET $2",
            limit,
            offset,
        )
    columns = list(rows[0].keys()) if rows else []
    # Serialize rows: asyncpg Record -> dict, handle dates/decimals
    data = []
    for r in rows:
        row_dict = {}
        for k in columns:
            v = r[k]
            if hasattr(v, "isoformat"):
                v = v.isoformat()
            elif hasattr(v, "__float__") and type(v).__name__ in ("Decimal",):
                v = float(v)
            row_dict[k] = v
        data.append(row_dict)
    return {
        "table": table,
        "columns": columns,
        "rows": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
