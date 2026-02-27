-- Enterprise Credential Vault
-- Encrypted storage for sensitive credentials

CREATE TABLE IF NOT EXISTS credential_vault (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vault_key       VARCHAR(255) NOT NULL,
    tenant_id       UUID NOT NULL,
    encrypted_value TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(vault_key, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_vault_tenant ON credential_vault(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vault_key ON credential_vault(vault_key, tenant_id);
