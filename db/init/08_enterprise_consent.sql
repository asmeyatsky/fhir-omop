-- Enterprise Consent Management (PDPL)
-- Patient consent tracking for data processing

CREATE TABLE IF NOT EXISTS consent (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      VARCHAR(255) NOT NULL,
    tenant_id       UUID NOT NULL,
    purpose         VARCHAR(50) NOT NULL CHECK (purpose IN ('treatment', 'research', 'analytics', 'public_health', 'quality_improvement')),
    scope           VARCHAR(50) NOT NULL CHECK (scope IN ('all_data', 'clinical_only', 'demographics_only', 'specific_resources')),
    status          VARCHAR(50) NOT NULL CHECK (status IN ('active', 'revoked', 'expired')),
    granted_by      UUID NOT NULL,
    granted_at      TIMESTAMPTZ NOT NULL,
    expires_at      TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    revoked_by      UUID,
    resource_types  JSONB,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consent_patient ON consent(patient_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_consent_tenant ON consent(tenant_id);
CREATE INDEX IF NOT EXISTS idx_consent_status ON consent(status, tenant_id);
