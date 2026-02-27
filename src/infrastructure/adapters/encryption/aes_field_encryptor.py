"""
AES-256-GCM Field Encryptor

Architectural Intent:
- Encrypts/decrypts individual field values using AES-256-GCM
- Master key loaded from environment variable
- Each encryption uses a unique 12-byte nonce
- Returns base64-encoded nonce+ciphertext+tag
"""
from __future__ import annotations

import base64
import copy
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AESFieldEncryptor:
    """AES-256-GCM field-level encryption for PII data."""

    def __init__(self, master_key: bytes | None = None) -> None:
        if master_key is None:
            key_hex = os.environ.get(
                "ENCRYPTION_MASTER_KEY",
                "0" * 64,  # 32-byte zero key for dev only
            )
            master_key = bytes.fromhex(key_hex)

        if len(master_key) != 32:
            raise ValueError("Master key must be 32 bytes (256 bits)")

        self._aesgcm = AESGCM(master_key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext, return base64(nonce + ciphertext + tag)."""
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, ciphertext_b64: str) -> str:
        """Decrypt base64(nonce + ciphertext + tag), return plaintext."""
        raw = base64.b64decode(ciphertext_b64)
        nonce = raw[:12]
        ciphertext = raw[12:]
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")

    def encrypt_fields(self, data: dict, field_paths: list[str]) -> dict:
        """Encrypt specific fields in a dict (shallow copy, in-place encrypt)."""
        result = copy.deepcopy(data)
        for path in field_paths:
            if path in result and result[path] is not None:
                value = str(result[path])
                result[path] = self.encrypt(value)
        return result

    def decrypt_fields(self, data: dict, field_paths: list[str]) -> dict:
        """Decrypt specific fields in a dict."""
        result = copy.deepcopy(data)
        for path in field_paths:
            if path in result and result[path] is not None:
                try:
                    result[path] = self.decrypt(str(result[path]))
                except Exception:
                    pass  # Leave as-is if decryption fails (not encrypted)
        return result
