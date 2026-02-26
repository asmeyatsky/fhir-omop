# Enterprise Branch: Saudi Hospital Chain Deployment

## Context

The FHIR-to-OMOP Accelerator Phase 1 MVP is working (6718/6718 records, 100% load rate). A large hospital chain in Saudi Arabia needs this deployed as an enterprise-grade solution. Saudi regulations require compliance with PDPL (data privacy), NCA ECC-2:2024 (cybersecurity), NPHIES (national health exchange), NDMO (data governance), and strict data residency within KSA.

The current MVP has no auth, no audit logging, in-memory repos (data lost on restart), CORS `*`, and no encryption. This plan upgrades it to enterprise grade on a new `enterprise` branch.

---

## Saudi Compliance Coverage

| Regulation | Governing Body | Features Addressing It |
|---|---|---|
| **PDPL** — Health data as sensitive data, consent, DPO, breach notification | SDAIA | Consent Management (#7), Encryption (#6), Audit (#4) |
| **NCA ECC-2:2024** — 110 cybersecurity controls for CNI | NCA | Auth/RBAC (#3), Encryption (#6), Rate Limiting (#10), Audit (#4) |
| **NPHIES** — FHIR R4.0.1 national platform integration | CHI / NHIC | NPHIES Profiles (#9) |
| **NDMO** — Data governance, classification, lifecycle | SDAIA / NDMO | Data Classification (#5), Tenant Isolation (#2) |
| **Data Residency** — All health data within KSA borders | SDAIA / CST | Residency Controls (#8) |
| **HIE Policies** — ISO 27789 audit trails, SNOMED CT/ICD-10/LOINC | MOH / NHIC | Audit Logging (#4), existing vocabulary support |
| **MOH eHealth** — Interoperability via IHE profiles | MOH / NHIC | NPHIES (#9), existing FHIR R4 support |

---

## Build Order (dependency-driven)

### 1. Persistent PostgreSQL Repositories + Database Foundation
*All other features need durable storage.*

**New files:**
- `src/infrastructure/config/database.py` — SQLAlchemy async engine, session factory, pool config
- `src/infrastructure/repositories/postgresql_repos.py` — `PostgreSQLSourceConnectionRepository`, `PostgreSQLMappingConfigRepository`, `PostgreSQLPipelineRepository`
- `src/infrastructure/repositories/postgresql_event_bus.py` — Persists domain events
- `db/init/02_enterprise_app_tables.sql` — `source_connection`, `mapping_configuration`, `pipeline`, `domain_event` tables

**Modify:**
- `src/infrastructure/config/container.py` — Swap in-memory repos for PostgreSQL repos (env-driven: `STORAGE_BACKEND=postgresql|memory`)
- `src/presentation/api/app.py` — Init DB engine in lifespan
- `pyproject.toml` — Add `alembic>=1.14.0`

**Tests:** `tests/infrastructure/test_postgresql_repos.py`, `tests/infrastructure/test_database.py`

---

### 2. Tenant Isolation
*All data must be scoped per hospital before anything else writes data.*

**New files:**
- `src/domain/entities/tenant.py` — `Tenant` frozen dataclass (id, name, hospital_name, nphies_facility_id, settings)
- `src/domain/ports/tenant_port.py` — `TenantRepositoryPort`
- `src/domain/value_objects/tenant_context.py` — `TenantContext` frozen dataclass
- `src/infrastructure/repositories/tenant_context.py` — `contextvars.ContextVar` for current tenant, `get_current_tenant_id()`
- `src/infrastructure/middleware/tenant_middleware.py` — Extracts tenant_id from JWT, sets context var
- `src/presentation/api/tenant_router.py` — CRUD `/api/v1/tenants` (ADMIN only)
- `db/init/03_enterprise_tenant.sql` — `tenant` table, add `tenant_id` columns + indexes to all entity tables

**Modify:**
- `src/infrastructure/repositories/postgresql_repos.py` — All queries filtered by `tenant_id`
- `src/presentation/api/app.py` — Add TenantMiddleware
- `src/infrastructure/config/container.py` — Wire tenant repo

**Tests:** `tests/domain/test_tenant.py`, `tests/infrastructure/test_tenant_middleware.py`, `tests/infrastructure/test_tenant_repo_filtering.py`, `tests/integration/test_tenant_api.py`

---

### 3. Authentication & Authorization (JWT + RBAC)
*Needed before audit (captures actor), consent (who grants), endpoint protection.*

**New files:**
- `src/domain/entities/user.py` — `User` entity, `UserRole` enum (ADMIN, DATA_STEWARD, OPERATOR, AUDITOR)
- `src/domain/value_objects/auth.py` — `TokenClaims`, `Permission`, `ROLE_PERMISSIONS` mapping
- `src/domain/ports/auth_port.py` — `AuthenticationPort`, `TokenPort`, `UserRepositoryPort`
- `src/application/commands/authenticate_user.py` — `AuthenticateUserUseCase`
- `src/application/commands/manage_users.py` — `CreateUserUseCase`, `DeactivateUserUseCase`
- `src/application/dtos/auth_dtos.py` — Login/token/user DTOs
- `src/infrastructure/adapters/auth/jwt_token_service.py` — RS256 JWT via PyJWT
- `src/infrastructure/adapters/auth/password_service.py` — bcrypt hashing
- `src/infrastructure/repositories/postgresql_user_repo.py` — User CRUD
- `src/presentation/api/dependencies.py` — `get_current_user()`, `require_role()`, `require_permission()`
- `src/presentation/api/auth_router.py` — `/api/v1/auth/login`, `/auth/refresh`, `/auth/me`
- `src/presentation/api/user_router.py` — `/api/v1/users` CRUD (ADMIN)
- `db/init/04_enterprise_auth.sql` — `app_user` table

**Modify:**
- `src/presentation/api/app.py` — Register routers, replace CORS `*` with configurable origins
- `src/presentation/api/source_router.py` — Add `Depends(require_role(ADMIN, OPERATOR))`
- `src/presentation/api/mapping_router.py` — Add `Depends(require_role(ADMIN, DATA_STEWARD))`
- `src/presentation/api/pipeline_router.py` — Add `Depends(require_role(ADMIN, OPERATOR))`
- `src/presentation/api/schemas.py` — Add auth request/response models
- `src/infrastructure/config/container.py` — Wire auth services
- `pyproject.toml` — Add `PyJWT>=2.8.0`, `cryptography>=41.0.0`, `bcrypt>=4.1.0`

**RBAC Matrix:**

| Endpoint | ADMIN | DATA_STEWARD | OPERATOR | AUDITOR |
|---|---|---|---|---|
| Manage users | Yes | - | - | - |
| Manage tenants | Yes | - | - | - |
| Manage sources | Yes | - | Yes | - |
| Manage mappings | Yes | Yes | - | - |
| Execute pipelines | Yes | - | Yes | - |
| View pipelines | Yes | Yes | Yes | Yes |
| Manage consent | Yes | Yes | - | - |
| Query audit log | Yes | - | - | Yes |

**Tests:** `tests/domain/test_user.py`, `tests/application/test_authenticate_user.py`, `tests/application/test_manage_users.py`, `tests/infrastructure/test_jwt_token_service.py`, `tests/integration/test_auth_api.py`

---

### 4. Audit Logging (ISO 27789)
*Immutable, tamper-evident audit trail for all operations.*

**New files:**
- `src/domain/entities/audit_entry.py` — `AuditEntry` with SHA-256 checksum, `AuditEventType`, `AuditAction` enums
- `src/domain/ports/audit_port.py` — `AuditLogPort` (record, query, verify_integrity)
- `src/application/commands/record_audit.py` — Used by middleware
- `src/application/queries/query_audit_log.py` — For auditors to search logs
- `src/application/dtos/audit_dtos.py`
- `src/infrastructure/adapters/audit/postgresql_audit_log.py` — Append-only table, checksum verification
- `src/infrastructure/middleware/audit_middleware.py` — Intercepts all requests, captures actor/IP/method/path/status
- `src/presentation/api/audit_router.py` — `GET /api/v1/audit` (AUDITOR/ADMIN), `GET /api/v1/audit/{id}/verify`
- `db/init/05_enterprise_audit.sql` — `audit_log` table (REVOKE UPDATE/DELETE for app role)

**Audit entry fields (ISO 27789):**
- `timestamp`, `event_type`, `actor_id`, `actor_email`, `actor_role`
- `tenant_id`, `resource_type`, `resource_id`, `action`
- `source_ip`, `user_agent`, `request_method`, `request_path`, `status_code`
- `data_classification`, `before_state` (JSONB), `after_state` (JSONB)
- `checksum` (SHA-256 of concatenated fields — tamper detection)

**Modify:**
- `src/presentation/api/app.py` — Add AuditMiddleware
- `src/infrastructure/config/container.py` — Wire audit services

**Tests:** `tests/domain/test_audit_entry.py`, `tests/infrastructure/test_audit_middleware.py`, `tests/infrastructure/test_postgresql_audit_log.py`, `tests/integration/test_audit_api.py`

---

### 5. Data Classification (NDMO)
*Labels all data flows: PUBLIC, INTERNAL, CONFIDENTIAL, TOP_SECRET.*

**New files:**
- `src/domain/value_objects/classification.py` — `DataClassification` enum, `ClassificationPolicy`
- `src/domain/ports/classification_port.py` — `DataClassificationPort`
- `src/domain/services/classification_service.py` — Default rules:
  - Patient identifiers (MRN, SSN, name) → `TOP_SECRET`
  - Clinical data (conditions, observations, measurements) → `CONFIDENTIAL`
  - Administrative data (visit types, care sites) → `INTERNAL`
  - Aggregated/anonymized data → `PUBLIC`
- `src/infrastructure/adapters/classification/policy_store.py` — PostgreSQL-backed policies
- `db/init/06_enterprise_classification.sql` — `classification_policy` table with default rows

**Modify:**
- `src/domain/value_objects/omop.py` — Add `classification: DataClassification` to `OMOPRecord`
- `src/domain/services/mapping_service.py` — Classify records after transform
- `src/infrastructure/config/container.py` — Wire classification service

**Tests:** `tests/domain/test_classification_service.py`, `tests/domain/test_classification_value_objects.py`

---

### 6. Encryption (Field-Level PII + Credential Vault)
*AES-256-GCM for PII fields, encrypted credential storage.*

**New files:**
- `src/domain/ports/encryption_port.py` — `FieldEncryptionPort`, `CredentialVaultPort`
- `src/domain/value_objects/encryption.py` — `EncryptedField`, `PII_FIELD_PATHS` per resource type
- `src/infrastructure/adapters/encryption/aes_field_encryptor.py` — AES-256-GCM via `cryptography` lib, master key from `ENCRYPTION_MASTER_KEY` env var
- `src/infrastructure/adapters/encryption/credential_vault.py` — Encrypted PostgreSQL store (interface designed for HashiCorp Vault swap)
- `db/init/07_enterprise_encryption.sql` — `credential_vault` table

**PII fields encrypted:**
- `Patient`: `identifier[*].value`, `name[*].family`, `name[*].given`, `telecom[*].value`, `address[*]`
- `person` (OMOP): `person_source_value`

**Modify:**
- `src/domain/services/mapping_service.py` — Encrypt PII fields before load
- `src/domain/value_objects/fhir.py` — Add `credentials_vault_key` to `FHIREndpoint`
- `src/infrastructure/config/container.py` — Wire encryption services

**Tests:** `tests/infrastructure/test_aes_field_encryptor.py`, `tests/infrastructure/test_credential_vault.py`

---

### 7. PDPL Consent Management
*Track and enforce patient consent before processing.*

**New files:**
- `src/domain/entities/consent.py` — `Consent` entity with:
  - `ConsentPurpose`: TREATMENT, RESEARCH, ANALYTICS, DATA_SHARING, NPHIES_EXCHANGE
  - `ConsentScope`: ALL_DATA, CLINICAL_ONLY, DEMOGRAPHICS_ONLY, SPECIFIC_RESOURCES
  - `ConsentStatus`: ACTIVE, REVOKED, EXPIRED, PENDING
- `src/domain/ports/consent_port.py` — `ConsentRepositoryPort`
- `src/domain/services/consent_service.py` — `check_consent()`, `enforce_consent()` (raises `ConsentRequiredError`)
- `src/domain/events/consent_events.py` — `ConsentGrantedEvent`, `ConsentRevokedEvent`
- `src/application/commands/manage_consent.py` — Grant/revoke use cases
- `src/application/queries/query_consent.py` — Patient consent queries
- `src/application/dtos/consent_dtos.py`
- `src/presentation/api/consent_router.py` — `/api/v1/consent` CRUD
- `db/init/08_enterprise_consent.sql` — `consent` table with unique active constraint per patient+purpose

**Modify:**
- `src/application/commands/execute_pipeline.py` — Consent enforcement before extraction
- `src/infrastructure/config/container.py` — Wire consent services

**Tests:** `tests/domain/test_consent.py`, `tests/domain/test_consent_service.py`, `tests/application/test_manage_consent.py`, `tests/integration/test_consent_api.py`

---

### 8. Data Residency Controls
*Enforce KSA-only data processing.*

**New files:**
- `src/domain/value_objects/residency.py` — `ResidencyPolicy` (allowed_regions defaults to `("SA",)`)
- `src/domain/ports/residency_port.py` — `GeoLocationPort`, `ResidencyEnforcementPort`
- `src/domain/services/residency_service.py` — `enforce_data_residency()`, raises `DataResidencyViolationError` if target outside KSA
- `src/infrastructure/adapters/residency/ip_geolocation.py` — DNS resolution + config-based allow-list of KSA IP ranges/hostnames
- `src/infrastructure/middleware/residency_middleware.py` — Checks outbound connections, configurable via `DATA_RESIDENCY_ENFORCE=true|false`

**Modify:**
- `src/application/commands/execute_pipeline.py` — Residency check on target + source URLs
- `src/application/commands/create_source_connection.py` — Validate source URL residency on creation
- `src/infrastructure/config/container.py` — Wire residency services

**Tests:** `tests/domain/test_residency_service.py`, `tests/infrastructure/test_residency_middleware.py`

---

### 9. NPHIES-Ready FHIR Profiles
*Saudi national health exchange compatibility (FHIR R4.0.1).*

**New files:**
- `src/domain/value_objects/nphies.py` — `NPHIESProfile`, `NPHIESValidationResult`, profile URL constants (e.g., `http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/patient|1.0.0`)
- `src/domain/ports/nphies_port.py` — `NPHIESClientPort` (validate_resource, submit_claim, check_eligibility)
- `src/domain/services/nphies_service.py` — Validate and enrich resources with Saudi-specific extensions
- `src/infrastructure/adapters/fhir/nphies_client.py` — HTTP client for NPHIES endpoints
- `src/presentation/api/nphies_router.py` — `POST /api/v1/nphies/validate`, `GET /api/v1/nphies/profiles`

**Modify:**
- `src/domain/value_objects/fhir.py` — Add `NPHIES = "nphies"` to `FHIRServerType`
- `src/infrastructure/config/container.py` — Wire NPHIES services

**Tests:** `tests/domain/test_nphies_service.py`, `tests/integration/test_nphies_api.py`

---

### 10. Rate Limiting & API Security Hardening
*Final hardening layer.*

**New files:**
- `src/infrastructure/middleware/rate_limiter.py` — Redis token-bucket, per-tenant limits (100 req/min, 10 pipeline exec/min)
- `src/infrastructure/middleware/security_headers.py` — HSTS, X-Content-Type-Options, X-Frame-Options, CSP, X-Request-ID
- `src/infrastructure/middleware/input_validation.py` — 10MB body size limit, JSON depth limit, SQL injection pattern detection

**Modify:**
- `src/presentation/api/app.py` — Full middleware stack order: SecurityHeaders → RateLimiter → Tenant → Audit → InputValidation
- `src/presentation/api/schemas.py` — Stricter Pydantic validators (max lengths, regex patterns, URL validation)
- `docker-compose.yml` — Add Redis 7 service, add separate app-db PostgreSQL for application data

**Tests:** `tests/infrastructure/test_rate_limiter.py`, `tests/infrastructure/test_security_headers.py`, `tests/infrastructure/test_input_validation.py`, `tests/integration/test_api_security.py`

---

## New Dependencies

```toml
"PyJWT>=2.8.0"          # JWT token creation/verification
"cryptography>=41.0.0"  # AES-256-GCM encryption, RSA key signing
"bcrypt>=4.1.0"         # Password hashing
"alembic>=1.14.0"       # Database migrations
```

## Summary

| Metric | Count |
|---|---|
| New source files | ~52 |
| Modified source files | ~13 |
| New DB migration scripts | 7 |
| New test files | ~34 |
| New dependencies | 4 |
| New API endpoints | ~20 |
| New middleware layers | 6 |

## Verification

After each feature:
1. `pytest` — all tests pass
2. `ruff check src/ tests/` — no lint errors
3. `docker compose up --build` — services start clean
4. `python scripts/demo.py` — E2E pipeline still works (regression)

Final E2E: login → create tenant → create source → configure mappings → grant consent → run pipeline → query audit log → verify integrity.
