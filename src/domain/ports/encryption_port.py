"""
Encryption Ports

Architectural Intent:
- Interfaces for field-level encryption and credential vault
- Defined in domain layer, implemented in infrastructure
"""
from __future__ import annotations

from typing import Protocol


class FieldEncryptionPort(Protocol):
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string, return base64-encoded ciphertext."""
        ...

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64-encoded ciphertext, return plaintext."""
        ...

    def encrypt_fields(self, data: dict, field_paths: list[str]) -> dict:
        """Encrypt specific fields in a dict by path."""
        ...

    def decrypt_fields(self, data: dict, field_paths: list[str]) -> dict:
        """Decrypt specific fields in a dict by path."""
        ...


class CredentialVaultPort(Protocol):
    async def store(self, key: str, credential: str, tenant_id: str) -> None:
        """Store an encrypted credential."""
        ...

    async def retrieve(self, key: str, tenant_id: str) -> str | None:
        """Retrieve and decrypt a credential."""
        ...

    async def delete(self, key: str, tenant_id: str) -> None:
        """Delete a stored credential."""
        ...

    async def list_keys(self, tenant_id: str) -> list[str]:
        """List all credential keys for a tenant."""
        ...
