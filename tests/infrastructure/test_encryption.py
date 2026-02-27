"""Tests for AES-256-GCM Field Encryptor and Credential Vault."""
import pytest

from src.infrastructure.adapters.encryption.aes_field_encryptor import AESFieldEncryptor
from src.infrastructure.adapters.encryption.credential_vault import InMemoryCredentialVault


class TestAESFieldEncryptor:
    def setup_method(self):
        # Use a fixed 32-byte key for testing
        self.key = bytes.fromhex("00" * 32)
        self.encryptor = AESFieldEncryptor(master_key=self.key)

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "Ahmed Al-Rashid"
        encrypted = self.encryptor.encrypt(plaintext)
        assert encrypted != plaintext
        decrypted = self.encryptor.decrypt(encrypted)
        assert decrypted == plaintext

    def test_different_nonces(self):
        plaintext = "same-value"
        enc1 = self.encryptor.encrypt(plaintext)
        enc2 = self.encryptor.encrypt(plaintext)
        assert enc1 != enc2  # Different nonces should produce different ciphertexts

    def test_encrypt_unicode(self):
        plaintext = "أحمد الرشيد"  # Arabic name
        encrypted = self.encryptor.encrypt(plaintext)
        decrypted = self.encryptor.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_fields(self):
        data = {
            "person_source_value": "12345",
            "year_of_birth": "1990",
            "gender_concept_id": 8507,
        }
        encrypted = self.encryptor.encrypt_fields(
            data, ["person_source_value", "year_of_birth"]
        )
        assert encrypted["person_source_value"] != "12345"
        assert encrypted["year_of_birth"] != "1990"
        assert encrypted["gender_concept_id"] == 8507  # Not encrypted

    def test_decrypt_fields(self):
        data = {"person_source_value": "12345", "other": "value"}
        encrypted = self.encryptor.encrypt_fields(data, ["person_source_value"])
        decrypted = self.encryptor.decrypt_fields(encrypted, ["person_source_value"])
        assert decrypted["person_source_value"] == "12345"
        assert decrypted["other"] == "value"

    def test_encrypt_fields_skips_none(self):
        data = {"person_source_value": None, "other": "value"}
        encrypted = self.encryptor.encrypt_fields(data, ["person_source_value"])
        assert encrypted["person_source_value"] is None

    def test_encrypt_fields_skips_missing(self):
        data = {"other": "value"}
        encrypted = self.encryptor.encrypt_fields(data, ["person_source_value"])
        assert "person_source_value" not in encrypted

    def test_invalid_key_length(self):
        with pytest.raises(ValueError, match="32 bytes"):
            AESFieldEncryptor(master_key=b"tooshort")

    def test_original_data_unchanged(self):
        data = {"person_source_value": "12345"}
        self.encryptor.encrypt_fields(data, ["person_source_value"])
        assert data["person_source_value"] == "12345"  # Deep copy preserves original


class TestCredentialVault:
    def setup_method(self):
        key = bytes.fromhex("00" * 32)
        encryptor = AESFieldEncryptor(master_key=key)
        self.vault = InMemoryCredentialVault(encryptor=encryptor)

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self):
        await self.vault.store("fhir-api-key", "secret-key-123", "t-001")
        result = await self.vault.retrieve("fhir-api-key", "t-001")
        assert result == "secret-key-123"

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent(self):
        result = await self.vault.retrieve("nonexistent", "t-001")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self):
        await self.vault.store("temp-key", "temp-secret", "t-001")
        await self.vault.delete("temp-key", "t-001")
        result = await self.vault.retrieve("temp-key", "t-001")
        assert result is None

    @pytest.mark.asyncio
    async def test_tenant_isolation(self):
        await self.vault.store("shared-key", "secret-a", "t-001")
        await self.vault.store("shared-key", "secret-b", "t-002")
        assert await self.vault.retrieve("shared-key", "t-001") == "secret-a"
        assert await self.vault.retrieve("shared-key", "t-002") == "secret-b"

    @pytest.mark.asyncio
    async def test_list_keys(self):
        await self.vault.store("key-1", "s1", "t-001")
        await self.vault.store("key-2", "s2", "t-001")
        await self.vault.store("key-3", "s3", "t-002")
        keys = await self.vault.list_keys("t-001")
        assert sorted(keys) == ["key-1", "key-2"]

    @pytest.mark.asyncio
    async def test_stored_value_is_encrypted(self):
        await self.vault.store("api-key", "plaintext-secret", "t-001")
        vault_key = "t-001:api-key"
        raw_stored = self.vault._store[vault_key]
        assert raw_stored != "plaintext-secret"
