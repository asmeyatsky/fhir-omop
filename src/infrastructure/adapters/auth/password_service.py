"""
Password Service

Architectural Intent:
- Implements PasswordPort using bcrypt
- Secure password hashing for NCA ECC-2:2024 compliance
"""
from __future__ import annotations

import bcrypt


class BcryptPasswordService:
    """Password hashing and verification using bcrypt."""

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
