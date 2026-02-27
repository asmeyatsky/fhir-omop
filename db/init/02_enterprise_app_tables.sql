-- Enterprise Application Tables
-- Persistent storage for domain entities (replaces in-memory repositories)

-- ============================================================
-- SOURCE_CONNECTION
-- ============================================================
CREATE TABLE IF NOT EXISTS source_connection (
    id                  UUID PRIMARY KEY,
    name                VARCHAR(255) NOT NULL,
    base_url            TEXT NOT NULL,
    server_type         VARCHAR(50) NOT NULL,
    auth_method         VARCHAR(50) NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'created',
    created_at          TIMESTAMPTZ NOT NULL,
    last_tested_at      TIMESTAMPTZ,
    capabilities        JSONB DEFAULT '[]',
    error_message       TEXT
);

CREATE INDEX IF NOT EXISTS idx_source_status ON source_connection(status);

-- ============================================================
-- MAPPING_CONFIGURATION
-- ============================================================
CREATE TABLE IF NOT EXISTS mapping_configuration (
    id                  UUID PRIMARY KEY,
    name                VARCHAR(255) NOT NULL,
    source_resource     VARCHAR(50) NOT NULL,
    target_table        VARCHAR(50) NOT NULL,
    field_mappings      JSONB NOT NULL,
    whistle_code        TEXT NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft',
    version             VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    template_id         VARCHAR(100),
    created_at          TIMESTAMPTZ NOT NULL,
    updated_at          TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mapping_status ON mapping_configuration(status);

-- ============================================================
-- PIPELINE
-- ============================================================
CREATE TABLE IF NOT EXISTS pipeline (
    id                      UUID PRIMARY KEY,
    name                    VARCHAR(255) NOT NULL,
    source_connection_id    UUID NOT NULL,
    mapping_config_ids      JSONB NOT NULL,
    target_connection_string TEXT NOT NULL,
    status                  VARCHAR(20) NOT NULL DEFAULT 'created',
    created_at              TIMESTAMPTZ NOT NULL,
    started_at              TIMESTAMPTZ,
    completed_at            TIMESTAMPTZ,
    current_stage           VARCHAR(20),
    stage_results           JSONB DEFAULT '[]',
    error_message           TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_status ON pipeline(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_source ON pipeline(source_connection_id);

-- ============================================================
-- DOMAIN_EVENT (persisted event log)
-- ============================================================
CREATE TABLE IF NOT EXISTS domain_event (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id    VARCHAR(255) NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    payload         JSONB NOT NULL,
    occurred_at     TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_event_aggregate ON domain_event(aggregate_id);
CREATE INDEX IF NOT EXISTS idx_event_type ON domain_event(event_type);
CREATE INDEX IF NOT EXISTS idx_event_occurred ON domain_event(occurred_at);
