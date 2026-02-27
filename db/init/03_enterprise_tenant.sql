-- Enterprise Tenant Isolation
-- Multi-tenancy support for hospital chain

CREATE TABLE IF NOT EXISTS tenant (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                        VARCHAR(255) NOT NULL UNIQUE,
    hospital_name               VARCHAR(500) NOT NULL,
    nphies_facility_id          VARCHAR(100),
    is_active                   BOOLEAN NOT NULL DEFAULT TRUE,
    max_pipelines_concurrent    INTEGER DEFAULT 5,
    data_retention_days         INTEGER DEFAULT 2555,
    allowed_fhir_servers        JSONB DEFAULT '[]',
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add tenant_id to all entity tables
ALTER TABLE source_connection ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE mapping_configuration ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE pipeline ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE domain_event ADD COLUMN IF NOT EXISTS tenant_id UUID;

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_source_tenant ON source_connection(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mapping_tenant ON mapping_configuration(tenant_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_tenant ON pipeline(tenant_id);
CREATE INDEX IF NOT EXISTS idx_event_tenant ON domain_event(tenant_id);
