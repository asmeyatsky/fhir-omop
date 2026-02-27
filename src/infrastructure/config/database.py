"""
Database Configuration

Architectural Intent:
- SQLAlchemy async engine and session management
- Connection pool configuration for enterprise workloads
- Single source of truth for database connectivity
"""
from __future__ import annotations

import os

import asyncpg


class DatabaseManager:
    """Manages the application database connection pool (asyncpg)."""

    def __init__(self, connection_string: str | None = None) -> None:
        self._connection_string = connection_string or os.environ.get(
            "APP_DATABASE_URL",
            "postgresql://omop:omop@localhost:5433/omop",
        )
        self._pool: asyncpg.Pool | None = None

    async def get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self._connection_string, min_size=2, max_size=20
            )
        return self._pool

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def health_check(self) -> tuple[bool, str]:
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                return True, f"Connected: {version}"
        except Exception as e:
            return False, f"Database connection failed: {e}"
