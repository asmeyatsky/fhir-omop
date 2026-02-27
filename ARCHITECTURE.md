# FHIR-to-OMOP Data Accelerator — Technical Architecture & Demo Runbook

> Enterprise Clinical Data Transformation Platform
> Version 0.2.0 | Saudi Healthcare Compliance (NCA ECC-2:2024, PDPL, NPHIES)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [Architecture Layers](#3-architecture-layers)
4. [Database Schema](#4-database-schema)
5. [API Reference](#5-api-reference)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [Frontend Architecture](#7-frontend-architecture)
8. [Data Flow: End-to-End Pipeline](#8-data-flow-end-to-end-pipeline)
9. [Middleware Stack](#9-middleware-stack)
10. [Mapping Templates](#10-mapping-templates)
11. [Compliance & Security](#11-compliance--security)
12. [Deployment](#12-deployment)
13. [Environment Variables](#13-environment-variables)
14. [Testing](#14-testing)
15. [Demo Runbook](#15-demo-runbook)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FHIR-to-OMOP Accelerator                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐     ┌──────────────────────────────────────────┐        │
│   │ Frontend  │     │           FastAPI Backend                 │        │
│   │ (SPA)     │────▶│                                          │        │
│   │           │     │  ┌────────┐  ┌──────────┐  ┌─────────┐  │        │
│   │ Tailwind  │     │  │ Auth   │  │ Pipeline │  │ Audit   │  │        │
│   │ Vanilla JS│     │  │ Router │  │ Router   │  │ Router  │  │        │
│   │ Hash SPA  │     │  └───┬────┘  └────┬─────┘  └────┬────┘  │        │
│   └──────────┘     │      │             │              │       │        │
│                     │  ┌───▼─────────────▼──────────────▼───┐  │        │
│                     │  │        Application Layer            │  │        │
│                     │  │   Use Cases (Commands + Queries)    │  │        │
│                     │  └───┬─────────────┬──────────────┬───┘  │        │
│                     │      │             │              │       │        │
│                     │  ┌───▼─────────────▼──────────────▼───┐  │        │
│                     │  │          Domain Layer                │  │        │
│                     │  │  Entities · Value Objects · Events  │  │        │
│                     │  │  Services · Ports (Interfaces)      │  │        │
│                     │  └───┬─────────────┬──────────────┬───┘  │        │
│                     │      │             │              │       │        │
│                     │  ┌───▼───┐   ┌────▼────┐   ┌────▼────┐  │        │
│                     │  │ FHIR  │   │ Whistle │   │  OMOP   │  │        │
│                     │  │Client │   │ Engine  │   │ Writer  │  │        │
│                     │  └───┬───┘   └─────────┘   └────┬────┘  │        │
│                     └──────┼──────────────────────────┼───────┘        │
│                            │                          │                 │
│                    ┌───────▼────────┐        ┌───────▼────────┐        │
│                    │  FHIR R4       │        │  OMOP CDM v5.4 │        │
│                    │  Server        │        │  PostgreSQL     │        │
│                    │  (HAPI/Epic/   │        │  Target DB      │        │
│                    │   Cerner)      │        │                 │        │
│                    └────────────────┘        └────────────────┘        │
│                                                                         │
│                    ┌────────────────────────────────────┐               │
│                    │  App PostgreSQL (port 5433)         │               │
│                    │  - source_connection                │               │
│                    │  - mapping_configuration            │               │
│                    │  - pipeline, domain_event           │               │
│                    │  - tenant, app_user                 │               │
│                    │  - audit_log, consent               │               │
│                    │  - OMOP CDM v5.4 tables             │               │
│                    └────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11+ | Async-first with type hints |
| **API Framework** | FastAPI 0.115+ | REST API, OpenAPI docs, Pydantic validation |
| **ASGI Server** | Uvicorn | Production-grade ASGI |
| **Database** | PostgreSQL 16 | Application state + OMOP CDM v5.4 |
| **DB Driver** | asyncpg | Async PostgreSQL with connection pooling |
| **Auth** | PyJWT (HS256) | JWT access (30m) + refresh (24h) tokens |
| **Passwords** | bcrypt | Salted password hashing |
| **Encryption** | AES-256-GCM | Field-level PII encryption at rest |
| **FHIR** | httpx | Async HTTP client for FHIR R4 servers |
| **Transform** | Whistle (Python DSL) | FHIR→OMOP field transformation engine |
| **Frontend** | Tailwind CSS + Vanilla JS | Zero-build static SPA |
| **Container** | Docker + Compose | Multi-container deployment |

---

## 3. Architecture Layers

The system follows **Clean Architecture** with strict dependency rules: outer layers depend inward, never the reverse.

### 3.1 Domain Layer (`src/domain/`)

Pure business logic. Zero framework dependencies. All entities are **immutable** (`dataclass(frozen=True)`).

#### Entities (Aggregate Roots)

| Entity | File | State Machine | Key Business Rules |
|--------|------|---------------|-------------------|
| **SourceConnection** | `entities/source_connection.py` | CREATED → TESTING → ACTIVE\|FAILED → DISABLED | Must be tested before pipeline use; immutable transitions return new instances |
| **Pipeline** | `entities/pipeline.py` | CREATED → RUNNING → COMPLETED\|FAILED\|CANCELLED | Stages: EXTRACT → TRANSFORM → LOAD; requires active source + active mappings |
| **MappingConfiguration** | `entities/mapping_config.py` | DRAFT → VALIDATED → ACTIVE | Created from templates; cannot activate without field mappings |
| **User** | `entities/user.py` | Active/Inactive | Roles: ADMIN, DATA_STEWARD, OPERATOR, AUDITOR; email normalized to lowercase |
| **Tenant** | `entities/tenant.py` | Active/Inactive | Hospital org unit; NPHIES facility ID; default 7-year retention |
| **AuditEntry** | `entities/audit_entry.py` | Immutable | SHA-256 checksum for tamper evidence; ISO 27789 compliant |
| **Consent** | `entities/consent.py` | ACTIVE → REVOKED\|EXPIRED | PDPL compliant; purpose + scope + expiry; resource-type filtering |

#### Value Objects

| Value Object | File | Purpose |
|-------------|------|---------|
| `FieldMapping` | `value_objects/mapping.py` | source_path → target_column with transformation type |
| `MappingTemplate` | `value_objects/mapping.py` | Pre-built template with Whistle code |
| `FHIREndpoint`, `FHIRBundle` | `value_objects/fhir.py` | FHIR server config and resource collection |
| `OMOPRecord`, `ConceptId` | `value_objects/omop.py` | Transformed record with data classification |
| `TokenClaims`, `Permission` | `value_objects/auth.py` | JWT payload and RBAC permission model |
| `DataClassification` | `value_objects/classification.py` | PUBLIC → INTERNAL → CONFIDENTIAL → TOP_SECRET |

#### Domain Ports (Interfaces)

| Port | File | Contract |
|------|------|----------|
| `SourceConnectionRepositoryPort` | `ports/repository_ports.py` | save, get_by_id, list_all, delete |
| `MappingConfigRepositoryPort` | `ports/repository_ports.py` | save, get_by_id, list_all, delete |
| `PipelineRepositoryPort` | `ports/repository_ports.py` | save, get_by_id, list_all, delete |
| `FHIRClientPort` | `ports/fhir_client_port.py` | test_connection, extract_resources, get_capabilities |
| `WhistleEnginePort` | `ports/whistle_engine_port.py` | execute(whistle_code, resource), validate_code |
| `OMOPWriterPort` | `ports/omop_writer_port.py` | write_records, validate_schema, test_connection |
| `TokenPort` | `ports/auth_port.py` | create_access_token, create_refresh_token, verify_token |
| `PasswordPort` | `ports/auth_port.py` | hash_password, verify_password |

#### Domain Services

| Service | Purpose |
|---------|---------|
| `MappingDomainService` | Orchestrates Whistle engine + vocabulary resolution + classification for bundle transformation |
| `VocabularyDomainService` | SNOMED/LOINC/ICD-10 → OMOP concept mapping (Phase 1: stubbed, returns concept_id=0) |
| `ClassificationService` | Applies 36 default policies to auto-classify FHIR fields by sensitivity |
| `ConsentService` | Validates active, non-expired consent before patient data processing |
| `NphiesService` | Validates FHIR resources against Saudi NPHIES profiles |

### 3.2 Application Layer (`src/application/`)

Orchestrates domain logic via **Commands** (write) and **Queries** (read). No direct infrastructure access.

#### Commands

| Use Case | Trigger | Flow |
|----------|---------|------|
| `CreateSourceConnectionUseCase` | POST /sources | Validate → Create entity → Persist → Publish events |
| `VerifySourceConnectionUseCase` | POST /sources/{id}/test | Fetch → Mark TESTING → Call FHIR server → Mark ACTIVE or FAILED |
| `CreateMappingFromTemplateUseCase` | POST /mappings | Lookup template → Create config → Auto-activate → Persist |
| `ExecutePipelineUseCase` | POST /pipelines | **Full ETL**: Validate → EXTRACT (FHIR) → TRANSFORM (Whistle) → LOAD (OMOP) → Complete |
| `AuthenticateUserUseCase` | POST /auth/login | Fetch user → Verify bcrypt → Build claims → Issue JWT pair |
| `CreateUserUseCase` | POST /users | Hash password → Create entity → Persist |

#### Queries

| Query | Returns |
|-------|---------|
| `ListSourceConnectionsQuery` | All FHIR source connections |
| `ListMappingTemplatesQuery` | Pre-built template registry |
| `ListMappingConfigsQuery` | All mapping configurations |
| `GetPipelineQuery` | Single pipeline with stage results |
| `ListPipelinesQuery` | All pipelines (newest first) |

### 3.3 Infrastructure Layer (`src/infrastructure/`)

Implements all domain ports with concrete technology.

#### Adapters

| Adapter | Implements | Technology |
|---------|-----------|------------|
| `HAPIFHIRClient` | FHIRClientPort | httpx async HTTP; FHIR R4 /metadata + resource pagination |
| `GoogleHealthcareFHIRClient` | FHIRClientPort | Google Cloud Healthcare API with service account auth |
| `WhistleEngine` | WhistleEnginePort | Python JSON-DSL interpreter; 12 transformation types |
| `PostgreSQLOMOPWriter` | OMOPWriterPort | asyncpg INSERT with ON CONFLICT; auto-PK generation |
| `JWTTokenService` | TokenPort | PyJWT HS256; 30m access / 24h refresh |
| `BcryptPasswordService` | PasswordPort | bcrypt with auto-salt |
| `AESFieldEncryptor` | EncryptionPort | AES-256-GCM; 12-byte nonce; base64 storage |

#### Repositories

**PostgreSQL** (production, `STORAGE_BACKEND=postgresql`):
- `PostgreSQLSourceConnectionRepository` — JSONB for capabilities
- `PostgreSQLMappingConfigRepository` — JSONB for field_mappings
- `PostgreSQLPipelineRepository` — JSONB for stage_results and mapping_config_ids
- `PostgreSQLEventBus` — Append-only domain_event table

**In-Memory** (testing/demo, `STORAGE_BACKEND=memory`):
- Dict-backed implementations of all repository ports
- Full query support including filters and pagination
- Used by all 244 tests via `conftest.py` override

#### Dependency Container (`src/infrastructure/config/container.py`)

```
AppContainer (Composition Root)
├── db_manager: DatabaseManager (asyncpg pool min=2, max=20)
├── source_repo, mapping_repo, pipeline_repo, event_bus
├── tenant_repo, user_repo, audit_log, consent_repo
├── token_service: JWTTokenService
├── password_service: BcryptPasswordService
├── fhir_client: HAPIFHIRClient
├── whistle_engine: WhistleEngine
├── omop_writer_factory: PostgreSQLOMOPWriterFactory
└── templates: dict[str, MappingTemplate]
```

### 3.4 Presentation Layer (`src/presentation/`)

FastAPI routers + Pydantic schemas. Thin controllers that delegate to use cases.

---

## 4. Database Schema

PostgreSQL 16. Schema initialized via `db/init/` scripts (executed alphabetically by Docker entrypoint).

### 4.1 OMOP CDM v5.4 Tables (`01_omop_cdm_v54.sql`)

| Table | Primary Key | Purpose |
|-------|------------|---------|
| `person` | person_id (BIGSERIAL) | Patient demographics |
| `visit_occurrence` | visit_occurrence_id (BIGSERIAL) | Encounter/visit records |
| `condition_occurrence` | condition_occurrence_id (BIGSERIAL) | Diagnoses |
| `measurement` | measurement_id (BIGSERIAL) | Lab results, vitals |
| `observation` | observation_id (BIGSERIAL) | Clinical observations |
| `location` | location_id (BIGINT) | Geographic locations |
| `care_site` | care_site_id (BIGINT) | Facilities |
| `provider` | provider_id (BIGINT) | Clinicians |

### 4.2 Application Tables (`02_enterprise_app_tables.sql`)

| Table | Primary Key | Key Columns |
|-------|------------|-------------|
| `source_connection` | id (UUID) | name, base_url, server_type, auth_method, status, capabilities (JSONB) |
| `mapping_configuration` | id (UUID) | source_resource, target_table, field_mappings (JSONB), whistle_code, status |
| `pipeline` | id (UUID) | source_connection_id, mapping_config_ids (JSONB), status, stage_results (JSONB) |
| `domain_event` | id (UUID) | aggregate_id, event_type, payload (JSONB), occurred_at |

### 4.3 Enterprise Tables

| Table | Script | Purpose |
|-------|--------|---------|
| `tenant` | `03_enterprise_tenant.sql` | Hospital orgs; adds tenant_id FK to all entity tables |
| `app_user` | `04_enterprise_auth.sql` | Users with email, password_hash, role, tenant_id |
| `audit_log` | `05_enterprise_audit.sql` | Append-only audit trail with SHA-256 checksums |
| `consent` | `08_enterprise_consent.sql` | PDPL consent records with purpose, scope, expiry |

---

## 5. API Reference

All API routes use prefix `/api/v1`. Responses are JSON.

### 5.1 Authentication

| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| POST | `/api/v1/auth/login` | None | `{email, password}` | `{access_token, refresh_token, token_type}` |
| GET | `/api/v1/auth/me` | Bearer | — | `{user_id, email, role, tenant_id, permissions[]}` |

### 5.2 Source Connections

| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| POST | `/api/v1/sources` | — | `{name, base_url, server_type, auth_method}` | SourceConnection (201) |
| GET | `/api/v1/sources` | — | — | SourceConnection[] |
| POST | `/api/v1/sources/{id}/test` | — | — | SourceConnection (updated status) |

### 5.3 Mappings

| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| GET | `/api/v1/mappings/templates` | — | — | MappingTemplate[] |
| POST | `/api/v1/mappings` | — | `{name, template_id}` | MappingConfig (201) |
| GET | `/api/v1/mappings` | — | — | MappingConfig[] |

### 5.4 Pipelines

| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| POST | `/api/v1/pipelines` | — | `{name, source_connection_id, mapping_config_ids[], target_connection_string}` | Pipeline (201) |
| GET | `/api/v1/pipelines/{id}` | — | — | Pipeline (with stage_results) |
| GET | `/api/v1/pipelines` | — | — | Pipeline[] |

### 5.5 Users (ADMIN only)

| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| POST | `/api/v1/users` | ADMIN | `{email, full_name, password, role, tenant_id}` | User (201) |
| GET | `/api/v1/users` | ADMIN | — | User[] |

### 5.6 Audit (ADMIN/AUDITOR)

| Method | Endpoint | Auth | Query Params | Response |
|--------|----------|------|-------------|----------|
| GET | `/api/v1/audit` | ADMIN/AUDITOR | `event_type, actor_id, limit, offset` | `{entries[], total, limit, offset}` |
| GET | `/api/v1/audit/{id}/verify` | ADMIN/AUDITOR | — | `{id, valid, checksum}` |

### 5.7 Consent

| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| POST | `/api/v1/consent` | consent:create | `{patient_id, purpose, scope, expires_at?, resource_types?, notes?}` | Consent (201) |
| GET | `/api/v1/consent` | consent:read | `patient_id?, limit, offset` | `{consents[], total}` |
| POST | `/api/v1/consent/{id}/revoke` | consent:create | — | Consent (revoked) |

### 5.8 Tenants

| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| POST | `/api/v1/tenants` | — | `{name, hospital_name, nphies_facility_id?}` | Tenant (201) |
| GET | `/api/v1/tenants` | — | — | Tenant[] |
| GET | `/api/v1/tenants/{id}` | — | — | Tenant |

### 5.9 Health

| Method | Endpoint | Auth | Response |
|--------|----------|------|----------|
| GET | `/health` | None | `{status: "healthy", version: "0.2.0", service: "fhir-omop-accelerator"}` |

---

## 6. Authentication & Authorization

### 6.1 Token Flow

```
User                    Frontend                    Backend
  │                        │                           │
  ├─ email + password ────▶│                           │
  │                        ├─ POST /auth/login ──────▶│
  │                        │                           ├─ Lookup user by email
  │                        │                           ├─ bcrypt.verify(password)
  │                        │                           ├─ Build TokenClaims
  │                        │                           ├─ JWT encode (HS256)
  │                        │◀─ {access_token, refresh} ┤
  │                        ├─ localStorage.set()       │
  │                        │                           │
  │                        ├─ GET /auth/me ──────────▶│
  │                        │   Authorization: Bearer   ├─ jwt.decode()
  │                        │◀─ {email, role, perms}   ┤
  │                        ├─ localStorage.set(user)   │
  │                        │                           │
  │  (all subsequent requests include Bearer token)    │
  │                        ├─ GET /api/v1/sources ───▶│
  │                        │   Authorization: Bearer   ├─ Verify + extract claims
  │                        │◀─ 200 OK                 ┤
  │                        │                           │
  │  (on 401 response)     │                           │
  │                        ├─ Clear tokens             │
  │                        ├─ Redirect to #/login      │
```

### 6.2 JWT Token Structure

**Access Token** (30-minute expiry):
```json
{
  "sub": "user-uuid",
  "email": "admin@hospital.sa",
  "role": "admin",
  "tenant_id": "tenant-uuid",
  "permissions": ["pipeline:create", "source:read", ...],
  "exp": 1709123456,
  "type": "access"
}
```

### 6.3 RBAC Permission Matrix

| Permission | ADMIN | DATA_STEWARD | OPERATOR | AUDITOR |
|-----------|-------|-------------|----------|---------|
| pipeline:create | ✓ | | ✓ | |
| pipeline:read | ✓ | ✓ | ✓ | ✓ |
| source:create | ✓ | | ✓ | |
| source:read | ✓ | | ✓ | ✓ |
| mapping:create | ✓ | ✓ | | |
| mapping:read | ✓ | ✓ | ✓ | ✓ |
| user:create | ✓ | | | |
| user:read | ✓ | | | |
| audit:read | ✓ | | | ✓ |
| consent:create | ✓ | ✓ | | |
| consent:read | ✓ | ✓ | | ✓ |
| tenant:create | ✓ | | | |
| tenant:read | ✓ | | | |

---

## 7. Frontend Architecture

### 7.1 Overview

Pure static files served by FastAPI's `StaticFiles` mount. No Node.js, no build step, no bundler.

- **Styling**: Tailwind CSS via CDN (`https://cdn.tailwindcss.com`)
- **Font**: Inter via Google Fonts (clean, Arabic-compatible)
- **Routing**: Hash-based SPA (`#/dashboard`, `#/sources`, etc.)
- **State**: `localStorage` for JWT tokens and user info
- **Modules**: ES module `import`/`export` across all JS files

### 7.2 Design Language

| Token | Value | Usage |
|-------|-------|-------|
| Navy 900 | `#0f172a` | Page background |
| Navy 800 | `#1e293b` | Sidebar, cards |
| Navy 700 | `#334155` | Hover states, borders |
| Teal 500 | `#14b8a6` | Primary actions, active states |
| Gold 500 | `#f59e0b` | Admin badges, accents |
| Inter | Google Fonts | All text |

### 7.3 File Structure

```
frontend/                              Mounted at /static by FastAPI
├── index.html                         App shell: sidebar + router mount + CDN imports
├── css/
│   └── app.css                        Design tokens, component classes, animations
└── js/
    ├── main.js                        Boot: register routes, init sidebar, start router
    ├── core/
    │   ├── api.js                     Fetch wrapper: JWT injection, 401 redirect
    │   ├── auth.js                    Token management: save/get/clear/decode/hasRole
    │   ├── router.js                  Hash-based SPA router with auth + role guards
    │   └── utils.js                   Formatters, toast(), statusBadge(), modal()
    └── pages/
        ├── login.js                   Login form → POST /auth/login
        ├── dashboard.js               KPI cards, recent pipelines, health status
        ├── sources.js                 FHIR connections CRUD + test connectivity
        ├── mappings.js                Templates browser + config creation
        ├── pipelines.js               Pipeline create/run/monitor with stage progress
        ├── users.js                   User management (ADMIN only)
        ├── audit.js                   Audit log with filters + integrity verify
        ├── consent.js                 Patient consent grant/revoke (PDPL)
        └── tenants.js                 Hospital tenant management (ADMIN)
```

### 7.4 Router & Auth Guards

```javascript
// Route registration (main.js)
registerRoute('#/login',     { render: renderLogin });
registerRoute('#/dashboard', { render: renderDashboard });
registerRoute('#/users',     { render: renderUsers, roles: ['admin'] });
registerRoute('#/audit',     { render: renderAudit, roles: ['admin', 'auditor'] });

// Guard logic (router.js)
// 1. Not authenticated + protected route → redirect to #/login
// 2. Authenticated + #/login → redirect to #/dashboard
// 3. Missing required role → redirect to #/dashboard
```

### 7.5 API Client (`api.js`)

```javascript
// Every request auto-attaches JWT from localStorage
// On 401 → clear tokens → redirect to #/login
const api = {
  get:  (path, query) => request('GET',  path, null, query),
  post: (path, body)  => request('POST', path, body),
};
```

### 7.6 Page Components

Each page module exports a single `render(container)` async function that:
1. Sets `container.innerHTML` with the page HTML
2. Fetches data from API
3. Binds event handlers (create buttons, forms, table rows)
4. Returns an optional cleanup function

### 7.7 Sidebar Navigation

- **Collapsible sections**: Data Platform (Sources, Mappings, Pipelines, Consent), Administration (Users, Audit, Tenants)
- **Role filtering**: Admin-only items hidden via `.admin-only` class, audit items via `.audit-visible`
- **Active state**: `.nav-link.active` class with teal highlight

---

## 8. Data Flow: End-to-End Pipeline

This is the core transformation flow — the centerpiece of the platform.

### 8.1 Pipeline Execution Sequence

```
POST /api/v1/pipelines
  │
  ▼
ExecutePipelineUseCase.execute()
  │
  ├─ VALIDATION
  │   ├─ Fetch SourceConnection → assert status == ACTIVE
  │   ├─ Fetch MappingConfigurations[] → assert all status == ACTIVE
  │   ├─ Create OMOPWriter from target_connection_string
  │   ├─ Create Pipeline entity → mark RUNNING
  │   └─ Persist pipeline
  │
  ├─ STAGE 1: EXTRACT
  │   ├─ For each mapping:
  │   │   └─ FHIRClient.extract_resources(endpoint, resource_type, batch_size=1000)
  │   │       └─ GET {base_url}/{resource_type}?_count=1000
  │   │       └─ Follow Link.relation="next" for pagination
  │   │       └─ Return FHIRBundle(resource_type, resources[])
  │   ├─ Record StageResult(EXTRACT, 0, total_extracted, 0)
  │   └─ Persist pipeline
  │
  ├─ STAGE 2: TRANSFORM
  │   ├─ For each (FHIRBundle, MappingConfiguration):
  │   │   └─ MappingDomainService.transform_bundle()
  │   │       └─ For each FHIR resource:
  │   │           ├─ WhistleEngine.execute(whistle_code, resource)
  │   │           │   ├─ Parse JSON-DSL mappings
  │   │           │   ├─ Extract source values (dot-notation paths)
  │   │           │   ├─ Apply transformations:
  │   │           │   │   direct, year_from_date, vocabulary_lookup,
  │   │           │   │   map, constant, person_id_hash, reference_to_person_id
  │   │           │   └─ Return OMOP-structured dict
  │   │           └─ Wrap as OMOPRecord(target_table, data, classification)
  │   ├─ Record StageResult(TRANSFORM, extracted, transformed, errors)
  │   └─ Persist pipeline
  │
  ├─ STAGE 3: LOAD
  │   ├─ OMOPWriter.write_records(all_records)
  │   │   ├─ Group records by target_table
  │   │   ├─ For each table:
  │   │   │   ├─ Build INSERT statement (exclude auto-PK)
  │   │   │   ├─ Coerce types (ISO dates → DATE, floats → ints for concept IDs)
  │   │   │   └─ INSERT ... ON CONFLICT DO NOTHING
  │   │   └─ Return count of records written
  │   ├─ Record StageResult(LOAD, transformed, loaded, errors)
  │   └─ Persist pipeline
  │
  ├─ FINALIZE
  │   ├─ pipeline.complete() → status = COMPLETED
  │   └─ Publish domain events (PipelineCompletedEvent)
  │
  └─ ON ERROR
      ├─ pipeline.fail(current_stage, error_message)
      └─ Publish PipelineFailedEvent
```

### 8.2 Whistle Transformation Types

| Type | Example Source | Output |
|------|---------------|--------|
| `direct` | `Patient.birthDate` | Passthrough |
| `year_from_date` | `"1990-05-15"` | `1990` |
| `month_from_date` | `"1990-05-15"` | `5` |
| `day_from_date` | `"1990-05-15"` | `15` |
| `vocabulary_lookup` | SNOMED code | concept_id (Phase 1: returns 0) |
| `constant` | params.value = `"32817"` | `32817` |
| `map` | `"male"` → mapping `{male: 8507}` | `8507` |
| `first_of_array` | `["John", "James"]` | `"John"` |
| `join` | `["John", "James"]` | `"John James"` |
| `person_id_hash` | `"patient-uuid"` | Deterministic int32 |
| `reference_to_person_id` | `"Patient/abc-123"` | Hashed int32 of `"abc-123"` |

---

## 9. Middleware Stack

Middleware executes in **reverse registration order** (last registered = first executed):

```
Request → SecurityHeaders → RateLimiter → CORS → Audit → InputValidation → Router → Handler
Response ← SecurityHeaders ← RateLimiter ← CORS ← Audit ← InputValidation ← Router ← Handler
```

| Middleware | Purpose | Key Behavior |
|-----------|---------|--------------|
| **SecurityHeadersMiddleware** | NCA ECC-2:2024 headers | CSP, HSTS, X-Frame-Options, X-Request-ID |
| **RateLimiterMiddleware** | DoS protection | Token bucket: 100 req/min, 20-burst per IP |
| **CORSMiddleware** | Cross-origin | `allow_origins=["*"]` (dev; restrict in production) |
| **AuditMiddleware** | ISO 27789 audit trail | Non-blocking; captures actor, action, resource, HTTP context |
| **InputValidationMiddleware** | Payload limits | Content-Type check, body size limit |

---

## 10. Mapping Templates

Four pre-built templates ship with the platform (`src/infrastructure/templates/registry.py`):

### Patient → PERSON

| FHIR Path | OMOP Column | Transform |
|-----------|-------------|-----------|
| `id` | `person_id` | `person_id_hash` |
| `identifier[0].value` | `person_source_value` | `direct` |
| `birthDate` | `year_of_birth` | `year_from_date` (default: 1900) |
| `birthDate` | `month_of_birth` | `month_from_date` (default: 1) |
| `birthDate` | `day_of_birth` | `day_from_date` (default: 1) |
| `gender` | `gender_concept_id` | `map` → male:8507, female:8532, other:8521, unknown:8551 |
| `gender` | `gender_source_value` | `direct` (default: "unknown") |
| — | `race_concept_id` | `constant` → 0 |
| — | `ethnicity_concept_id` | `constant` → 0 |

### Encounter → VISIT_OCCURRENCE

| FHIR Path | OMOP Column | Transform |
|-----------|-------------|-----------|
| `subject.reference` | `person_id` | `reference_to_person_id` |
| `id` | `visit_source_value` | `direct` |
| `period.start` | `visit_start_date` | `direct` (default: 1970-01-01) |
| `period.end` | `visit_end_date` | `direct` (default: 1970-01-01) |
| `class.code` | `visit_concept_id` | `map` → IMP:9201, AMB:9202, EMER:9203, HH:581476 |
| — | `visit_type_concept_id` | `constant` → 32817 (EHR) |

### Condition → CONDITION_OCCURRENCE

| FHIR Path | OMOP Column | Transform |
|-----------|-------------|-----------|
| `subject.reference` | `person_id` | `reference_to_person_id` |
| `code.coding[0].code` | `condition_source_value` | `direct` |
| `code.coding[0].code` | `condition_concept_id` | `vocabulary_lookup` (SNOMED) |
| `onsetDateTime` | `condition_start_date` | `direct` |
| — | `condition_type_concept_id` | `constant` → 32817 (EHR) |

### Observation → MEASUREMENT

| FHIR Path | OMOP Column | Transform |
|-----------|-------------|-----------|
| `subject.reference` | `person_id` | `reference_to_person_id` |
| `code.coding[0].code` | `measurement_source_value` | `direct` |
| `code.coding[0].code` | `measurement_concept_id` | `vocabulary_lookup` (LOINC) |
| `effectiveDateTime` | `measurement_date` | `direct` |
| `valueQuantity.value` | `value_as_number` | `direct` |
| `valueQuantity.unit` | `unit_source_value` | `direct` |
| — | `measurement_type_concept_id` | `constant` → 32817 (EHR) |
| — | `unit_concept_id` | `constant` → 0 |

---

## 11. Compliance & Security

| Requirement | Implementation |
|------------|----------------|
| **NCA ECC-2:2024** | Security headers middleware (CSP, HSTS, X-Frame-Options, X-Content-Type-Options) |
| **Saudi PDPL** | Consent entity with purpose/scope/expiry; grant and revoke API; audit trail |
| **NDMO Classification** | 4-level classification (PUBLIC→TOP_SECRET); 36 default policies; auto-classification during transform |
| **ISO 27789 Audit** | Immutable audit_log table; SHA-256 checksum per entry; verify integrity endpoint |
| **NPHIES** | Profile validation service; identifier systems (National ID, IQAMA, Passport); code systems |
| **RBAC** | 4 roles (ADMIN, DATA_STEWARD, OPERATOR, AUDITOR); fine-grained permissions per resource:action |
| **Encryption at Rest** | AES-256-GCM for PII fields; 12-byte nonce; master key from env variable |
| **Password Security** | bcrypt with auto-salt; min 8 characters enforced |
| **Rate Limiting** | Token bucket: 100 req/min per IP; 20-request burst allowance |
| **Multi-Tenancy** | X-Tenant-ID header; contextvars scoping; tenant_id FK on all entity tables |
| **Data Retention** | Default 2555 days (~7 years per Saudi regulation); configurable per tenant |

---

## 12. Deployment

### 12.1 Docker Compose (Production)

```bash
# Start everything (PostgreSQL + API)
docker compose up -d

# PostgreSQL available at localhost:5433
# API available at http://localhost:8000
# Frontend at http://localhost:8000/ (served by FastAPI)
```

**Services:**
- `omop-db`: PostgreSQL 16 Alpine with OMOP CDM v5.4 schema (auto-init via `db/init/`)
- `api`: FastAPI app (Python 3.12-slim, port 8000)

### 12.2 Local Development (In-Memory)

```bash
# No database required — uses in-memory repositories
STORAGE_BACKEND=memory python3 -m uvicorn src.presentation.api.app:app --reload --port 8000

# Open http://localhost:8000 → Login page
```

### 12.3 Local Development (PostgreSQL)

```bash
# Start only the database
docker compose up -d omop-db

# Run the API locally against Docker PostgreSQL
APP_DATABASE_URL=postgresql://omop:omop@localhost:5433/omop \
python3 -m uvicorn src.presentation.api.app:app --reload --port 8000
```

### 12.4 Static File Serving

FastAPI mounts `frontend/` at `/static`:
- `GET /static/js/main.js` → serves `frontend/js/main.js`
- `GET /static/css/app.css` → serves `frontend/css/app.css`
- `GET /{anything}` (non-API, non-static) → serves `frontend/index.html` (SPA catch-all)

---

## 13. Environment Variables

| Variable | Default | Required | Purpose |
|----------|---------|----------|---------|
| `STORAGE_BACKEND` | `postgresql` | No | `postgresql` or `memory` |
| `APP_DATABASE_URL` | `postgresql://omop:omop@localhost:5433/omop` | For PostgreSQL | App database connection |
| `JWT_SECRET_KEY` | `dev-secret-change-in-production` | **Production** | JWT signing key (≥32 chars) |
| `ENCRYPTION_MASTER_KEY` | — | For encryption | Hex-encoded 32-byte AES key |
| `FHIR_SERVER_BASE_URL` | `https://hapi.fhir.org/baseR4` | No | Default FHIR server |
| `FHIR_CLIENT_TIMEOUT` | `30` | No | HTTP timeout for FHIR calls (seconds) |
| `LOG_LEVEL` | `INFO` | No | Python logging level |

---

## 14. Testing

### 14.1 Test Suite

```bash
# Run all 244 tests
python3 -m pytest

# With coverage
python3 -m pytest --cov=src --cov-report=term-missing

# Specific layer
python3 -m pytest tests/domain/
python3 -m pytest tests/application/
python3 -m pytest tests/infrastructure/
python3 -m pytest tests/integration/
```

### 14.2 Test Categories

| Category | Location | Count | What's Tested |
|----------|----------|-------|---------------|
| **Domain** | `tests/domain/` | ~100 | Entity state machines, value objects, services, classification, consent, NPHIES |
| **Application** | `tests/application/` | ~40 | Use case orchestration with mock ports |
| **Infrastructure** | `tests/infrastructure/` | ~80 | Whistle engine, templates, JWT, encryption, middleware, repositories |
| **Integration** | `tests/integration/` | ~24 | End-to-end API flows via TestClient |

### 14.3 Test Configuration

All tests use `STORAGE_BACKEND=memory` (set in `conftest.py`). No external database or services required.

---

## 15. Demo Runbook

### Prerequisites

- Python 3.11+ installed
- Project dependencies: `pip install -e ".[dev]"`
- No database required (demo uses in-memory storage)

### Step 1: Start the Server

```bash
cd /path/to/fhir-omop
STORAGE_BACKEND=memory python3 -m uvicorn src.presentation.api.app:app --port 8000
```

### Step 2: Seed Demo Data (via API)

In a separate terminal, run these curl commands to create demo data:

```bash
BASE=http://localhost:8000/api/v1

# 1. Create a tenant
curl -s -X POST $BASE/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"riyadh-central","hospital_name":"King Faisal Specialist Hospital","nphies_facility_id":"NPHIES-10001"}' | python3 -m json.tool

# Save the tenant_id from the response, then:
TENANT_ID="<tenant-id-from-response>"

# 2. Create an admin user
curl -s -X POST $BASE/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <bootstrap-token>" \
  -d "{\"email\":\"admin@kfsh.sa\",\"full_name\":\"Dr. Mohammed Al-Rashid\",\"password\":\"SecurePass123!\",\"role\":\"admin\",\"tenant_id\":\"$TENANT_ID\"}"

# 3. Login
curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@kfsh.sa","password":"SecurePass123!"}' | python3 -m json.tool

# Save access_token, then:
TOKEN="<access-token>"

# 4. Create a FHIR source
curl -s -X POST $BASE/sources \
  -H "Content-Type: application/json" \
  -d '{"name":"HAPI FHIR Public Server","base_url":"https://hapi.fhir.org/baseR4","server_type":"hapi","auth_method":"none"}'

# 5. Create mappings from templates
curl -s -X POST $BASE/mappings \
  -H "Content-Type: application/json" \
  -d '{"name":"Patient Demographics","template_id":"patient-to-person"}'

curl -s -X POST $BASE/mappings \
  -H "Content-Type: application/json" \
  -d '{"name":"Visit Records","template_id":"encounter-to-visit"}'
```

### Step 3: Open the Frontend

1. Navigate to `http://localhost:8000`
2. You'll see the **login page** with the FHIR-to-OMOP branding
3. Log in with the credentials you created

### Step 4: Demo Walkthrough

| Step | Page | What to Show |
|------|------|-------------|
| 1 | **Login** | Enter credentials → JWT flow → redirect to dashboard |
| 2 | **Dashboard** | KPI cards (sources, pipelines, records), health status badge |
| 3 | **Sources** | FHIR connections list → click "Add Source" → create form → "Test" button |
| 4 | **Mappings** | Template cards (Patient→Person, Encounter→Visit, etc.) → create config from template |
| 5 | **Pipelines** | Click "New Pipeline" → select source + mappings → execute → stage progress bars |
| 6 | **Consent** | "Grant Consent" → select purpose/scope → grant → show in table → revoke |
| 7 | **Users** | (Admin) User list with role badges → "Add User" → assign role and tenant |
| 8 | **Audit** | (Admin) Audit log table → filter by event type → click verify integrity |
| 9 | **Tenants** | (Admin) Tenant cards with NPHIES facility IDs → "Add Tenant" |

### Step 5: Key Demo Talking Points

1. **Clean Architecture**: "Each layer has zero knowledge of the layers above it. We can swap PostgreSQL for DynamoDB without touching a single line of business logic."

2. **Saudi Compliance**: "Every API call generates an immutable audit entry with SHA-256 checksum — meeting ISO 27789. Patient consent is PDPL-compliant with purpose, scope, and automatic expiry."

3. **Enterprise Security**: "RBAC with four roles, AES-256-GCM encryption for PII at rest, rate limiting, and full NCA ECC-2:2024 security headers."

4. **Transformation Engine**: "We ship four pre-built FHIR R4 → OMOP CDM v5.4 mapping templates. The Whistle DSL engine handles type coercion, vocabulary mapping, and deterministic patient ID hashing."

5. **Multi-Tenancy**: "Each hospital in the chain gets isolated data with tenant-scoped queries. Configurable retention policies default to 7 years per Saudi regulation."

### Step 6: Verify Tests Still Pass

```bash
python3 -m pytest -q
# Expected: 244 passed
```

---

## 16. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `ConnectionRefusedError` on startup | PostgreSQL not running | Use `STORAGE_BACKEND=memory` or start `docker compose up -d omop-db` |
| `401 Unauthorized` on API calls | Token expired or missing | Re-login via POST /auth/login; check localStorage has valid token |
| `403 Forbidden` | User lacks required role/permission | Check user role matches endpoint requirement (see RBAC matrix) |
| Tailwind styles not loading | CSP blocking CDN | Verify security_headers.py allows `cdn.tailwindcss.com` in script-src |
| Frontend shows blank page | Static files not mounted | Verify `frontend/` directory exists at project root; check app.py mount |
| `Address already in use` | Port 8000 occupied | Kill existing process: `lsof -ti:8000 \| xargs kill` |
| Tests fail with import errors | Dependencies not installed | Run `pip install -e ".[dev]"` |
| `InsecureKeyLengthWarning` | Dev JWT secret too short | Set `JWT_SECRET_KEY` to 32+ character string in production |
