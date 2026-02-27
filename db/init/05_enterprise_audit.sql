-- Enterprise Audit Logging (ISO 27789)
-- Immutable, append-only audit trail

CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type      VARCHAR(50) NOT NULL,
    action          VARCHAR(50) NOT NULL,
    actor_id        UUID,
    actor_email     VARCHAR(255),
    actor_role      VARCHAR(50),
    tenant_id       UUID,
    resource_type   VARCHAR(100),
    resource_id     VARCHAR(255),
    http_method     VARCHAR(10),
    http_path       VARCHAR(2048),
    http_status     INTEGER,
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    details         JSONB,
    checksum        VARCHAR(64) NOT NULL
);

-- Performance indexes for common queries
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id);

-- Revoke UPDATE and DELETE from application role for append-only semantics
-- (Only superuser/owner can modify; application role should be restricted)
-- REVOKE UPDATE, DELETE ON audit_log FROM app_role;
