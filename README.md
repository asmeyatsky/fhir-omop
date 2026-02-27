# FHIR-to-OMOP Data Accelerator

Enterprise platform for transforming FHIR R4 clinical data into OMOP CDM v5.4 datasets. Built for Saudi healthcare compliance (NCA ECC-2:2024, PDPL, NPHIES).

Extracts from any FHIR R4 server, maps via a Whistle-compatible DSL engine, and loads into PostgreSQL — with a full-featured web dashboard, JWT authentication, RBAC, audit logging, and multi-tenant isolation.

## Screenshots

The frontend is a single-page application with a navy/teal enterprise design:

- **Login** — JWT-based authentication with role assignment
- **Dashboard** — KPI cards, system health, recent pipelines and sources
- **Sources** — FHIR R4 server connections with connectivity testing
- **Mappings** — Pre-built template browser and configuration management
- **Pipelines** — Create, execute, and monitor ETL pipelines with stage progress
- **Consent** — PDPL-compliant patient consent grant and revoke
- **Users / Audit / Tenants** — Admin pages for user management, audit trail, and hospital tenants

## Quick Start

### Option A: In-Memory (No Database Required)

```bash
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
STORAGE_BACKEND=memory uvicorn src.presentation.api.app:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** — the frontend login page loads immediately.

**First run:** If no users exist, the app creates a default admin so you can log in:

- **Email:** `admin@local.dev` (or set `BOOTSTRAP_ADMIN_EMAIL`)
- **Password:** `Admin123!` (or set `BOOTSTRAP_ADMIN_PASSWORD`)

### Option B: Docker Compose (Full Stack)

```bash
docker compose up -d --build
# PostgreSQL (OMOP schema) on port 5433
# API + Frontend on port 8000
```

Open **http://localhost:8000** or Swagger UI at **http://localhost:8000/docs**. The same bootstrap admin is created when using in-memory user/tenant storage (default in this setup).

### Running the demo locally (full pipeline: FHIR → OMOP)

The demo script creates a FHIR source, mappings, and runs a pipeline that loads into an OMOP PostgreSQL database. You can run it entirely on your machine in two ways:

**1. Full stack in Docker (easiest)**

```bash
docker compose up -d --build
python scripts/demo.py
```

The API and OMOP DB run in Docker; the script talks to the API at localhost:8000. No extra flags needed.

**2. API on your machine, OMOP DB in Docker (single script)**

One command does it all: starts the OMOP DB, starts the API, runs the demo.

```bash
./scripts/demo-local.sh
```

The script starts `omop-db` with Docker, runs the API in the background, then runs the demo. When it finishes, the API stays running at http://localhost:8000 (you can stop it with the printed `kill` command). Requires: Docker, Python venv with deps installed (`pip install -e ".[dev]"`).

**2b. Manual (three terminals)**

Use this when you want to run the API and demo steps yourself:

```bash
# Terminal 1: start only the OMOP database (port 5433 on host)
docker compose up -d omop-db

# Terminal 2: run the API
STORAGE_BACKEND=memory uvicorn src.presentation.api.app:app --host 0.0.0.0 --port 8000

# Terminal 3: run the demo, pointing the pipeline at localhost:5433
python scripts/demo.py --omop-url postgresql://omop:omop@localhost:5433/omop
```

The pipeline will connect to the OMOP DB at localhost:5433. You can also set `OMOP_CONNECTION` instead of `--omop-url`.

## Architecture

Clean Architecture (hexagonal) with four layers and strict dependency inversion:

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (Static SPA)                                       │
│  Tailwind CSS · Vanilla JS · Hash Router · JWT Auth          │
├──────────────────────────────────────────────────────────────┤
│  Presentation (FastAPI)                                      │
│  8 routers · Pydantic schemas · Auth dependencies            │
├──────────────────────────────────────────────────────────────┤
│  Application (Use Cases)                                     │
│  Commands (create, execute, authenticate)                    │
│  Queries (list, get)                                         │
├──────────────────────────────────────────────────────────────┤
│  Domain (Pure Business Logic)                                │
│  Entities · Value Objects · Services · Ports · Events        │
├──────────────────────────────────────────────────────────────┤
│  Infrastructure (Adapters)                                   │
│  FHIR Client · Whistle Engine · OMOP Writer · PostgreSQL     │
│  JWT · bcrypt · AES-256-GCM · Middleware                     │
└──────────────────────────────────────────────────────────────┘
```

> For comprehensive documentation see [ARCHITECTURE.md](ARCHITECTURE.md) — covers database schema, all API endpoints, auth/RBAC matrix, data flow diagrams, mapping templates, compliance details, and a step-by-step demo runbook.

## API

Base URL: `http://localhost:8000/api/v1` | Swagger: `http://localhost:8000/docs`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | — | Health check |
| POST | `/api/v1/auth/login` | — | Authenticate, receive JWT tokens |
| GET | `/api/v1/auth/me` | Bearer | Current user info |
| POST | `/api/v1/sources` | — | Create FHIR source connection |
| GET | `/api/v1/sources` | — | List source connections |
| POST | `/api/v1/sources/{id}/test` | — | Test FHIR connectivity |
| GET | `/api/v1/mappings/templates` | — | List pre-built mapping templates |
| POST | `/api/v1/mappings` | — | Create mapping from template |
| GET | `/api/v1/mappings` | — | List mapping configurations |
| POST | `/api/v1/pipelines` | — | Execute FHIR-to-OMOP pipeline |
| GET | `/api/v1/pipelines` | — | List pipelines |
| GET | `/api/v1/pipelines/{id}` | — | Get pipeline status with stage results |
| POST | `/api/v1/users` | ADMIN | Create user |
| GET | `/api/v1/users` | ADMIN | List users |
| GET | `/api/v1/audit` | ADMIN/AUDITOR | Query audit log |
| GET | `/api/v1/audit/{id}/verify` | ADMIN/AUDITOR | Verify audit entry integrity |
| POST | `/api/v1/consent` | consent:create | Grant patient consent |
| GET | `/api/v1/consent` | consent:read | List consents |
| POST | `/api/v1/consent/{id}/revoke` | consent:create | Revoke consent |
| POST | `/api/v1/tenants` | — | Create tenant |
| GET | `/api/v1/tenants` | — | List tenants |

### Pipeline Execution

```bash
# 1. Create a source connection
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{"name":"HAPI FHIR","base_url":"https://hapi.fhir.org/baseR4","server_type":"hapi","auth_method":"none"}'

# 2. Create mappings from templates
curl -X POST http://localhost:8000/api/v1/mappings \
  -H "Content-Type: application/json" \
  -d '{"name":"Patient to Person","template_id":"patient-to-person"}'

# 3. Run pipeline (extracts → transforms → loads)
curl -X POST http://localhost:8000/api/v1/pipelines \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Run","source_connection_id":"<id>","mapping_config_ids":["<id>"],"target_connection_string":"postgresql://omop:omop@localhost:5433/omop"}'
```

## Mapping Templates

Four pre-built FHIR R4 → OMOP CDM v5.4 templates:

| Template | FHIR Resource | OMOP Table | Fields |
|----------|---------------|------------|--------|
| `patient-to-person` | Patient | person | gender, birth date, identifiers |
| `encounter-to-visit` | Encounter | visit_occurrence | visit type, period, class |
| `condition-to-condition-occurrence` | Condition | condition_occurrence | SNOMED codes, onset date |
| `observation-to-measurement` | Observation | measurement | LOINC codes, values, units |

## Frontend

Zero-build static SPA served by FastAPI — no Node.js required.

- **Styling**: Tailwind CSS via CDN
- **Font**: Inter (Google Fonts, Arabic-compatible)
- **Routing**: Hash-based SPA (`#/dashboard`, `#/sources`, etc.)
- **Auth**: JWT in localStorage, auto-injected on all API calls, 401 → redirect to login
- **Role Filtering**: Admin-only pages hidden from non-admin users

```
frontend/
├── index.html              # App shell: sidebar nav, router mount
├── css/app.css             # Design tokens, component classes
└── js/
    ├── main.js             # Boot: route registration, sidebar init
    ├── core/               # api.js, auth.js, router.js, utils.js
    └── pages/              # login, dashboard, sources, mappings,
                            # pipelines, users, audit, consent, tenants
```

## Security & Compliance

| Feature | Implementation |
|---------|----------------|
| Authentication | JWT (HS256) — 30m access + 24h refresh tokens |
| Authorization | RBAC — ADMIN, DATA_STEWARD, OPERATOR, AUDITOR |
| Audit Trail | ISO 27789 — immutable entries with SHA-256 checksums |
| Encryption | AES-256-GCM for PII fields at rest |
| Consent | PDPL — purpose, scope, expiry, grant/revoke |
| Multi-Tenancy | Tenant-scoped data isolation |
| Security Headers | NCA ECC-2:2024 — CSP, HSTS, X-Frame-Options |
| Rate Limiting | Token bucket — 100 req/min, 20-burst per IP |
| Data Classification | NDMO 4-level — PUBLIC → TOP_SECRET |
| NPHIES | Profile validation, identifier systems, code systems |

## Development

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests (244 tests, ~7s)
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Lint & type check
ruff check src/ tests/
mypy src/
```

### Project Structure

```
src/
├── domain/               # Entities, value objects, ports, services, events
├── application/          # Use cases (commands + queries), DTOs
├── infrastructure/       # Adapters, repositories, middleware, config, templates
└── presentation/         # FastAPI app, routers, schemas, dependencies
frontend/
├── index.html            # SPA shell
├── css/app.css           # Tailwind extensions
└── js/                   # ES modules (core + 9 page modules)
tests/
├── domain/               # Pure business logic tests
├── application/          # Use case tests with mock ports
├── infrastructure/       # Adapter, middleware, repository tests
└── integration/          # End-to-end API tests
db/init/                  # PostgreSQL schema (OMOP CDM v5.4 + enterprise tables)
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `STORAGE_BACKEND` | `postgresql` | `postgresql` or `memory` |
| `APP_DATABASE_URL` | `postgresql://omop:omop@localhost:5433/omop` | Database connection |
| `JWT_SECRET_KEY` | `dev-secret-...` | JWT signing key (≥32 chars in production) |
| `ENCRYPTION_MASTER_KEY` | — | Hex-encoded 32-byte AES key |

## Tech Stack

- **Python 3.11+** with async/await throughout
- **FastAPI** + **Pydantic v2** for REST API
- **asyncpg** for PostgreSQL async I/O (pool: min=2, max=20)
- **PostgreSQL 16** with OMOP CDM v5.4 schema
- **PyJWT** + **bcrypt** + **cryptography** for auth/encryption
- **httpx** for async FHIR server communication
- **Tailwind CSS** + **Vanilla JS** for zero-build frontend
- **Docker Compose** for containerized deployment

## License

Proprietary. All rights reserved.
