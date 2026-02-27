"""
Credential Vault

Architectural Intent:
- Encrypted storage for sensitive credentials (FHIR server tokens, DB passwords)
- Uses AES-256-GCM to encrypt credentials before storing in memory/DB
- Swappable to HashiCorp Vault in production
"""
from __future__ import annotations

from src.infrastructure.adapters.encryption.aes_field_encryptor import AESFieldEncryptor


class InMemoryCredentialVault:
    """In-memory encrypted credential vault for development/testing."""

    def __init__(self, encryptor: AESFieldEncryptor | None = None) -> None:
        self._encryptor = encryptor or AESFieldEncryptor()
        self._store: dict[str, str] = {}  # key -> encrypted credential

    async def store(self, key: str, credential: str, tenant_id: str) -> None:
        vault_key = f"{tenant_id}:{key}"
        self._store[vault_key] = self._encryptor.encrypt(credential)

    async def retrieve(self, key: str, tenant_id: str) -> str | None:
        vault_key = f"{tenant_id}:{key}"
        encrypted = self._store.get(vault_key)
        if encrypted is None:
            return None
        return self._encryptor.decrypt(encrypted)

    async def delete(self, key: str, tenant_id: str) -> None:
        vault_key = f"{tenant_id}:{key}"
        self._store.pop(vault_key, None)

    async def list_keys(self, tenant_id: str) -> list[str]:
        prefix = f"{tenant_id}:"
        return [k[len(prefix):] for k in self._store if k.startswith(prefix)]
