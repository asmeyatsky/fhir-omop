# FHIR-to-OMOP Data Accelerator

**Automated clinical data transformation from FHIR R4 to OMOP CDM v5.4**

---

## The Problem

Healthcare organizations using FHIR for clinical data exchange need to convert that data into OMOP Common Data Model for research, analytics, and regulatory reporting. Today this requires months of manual ETL development, deep expertise in both standards, and ongoing maintenance as schemas evolve.

## The Solution

A turnkey accelerator that connects to any FHIR R4 server, applies pre-built mapping templates, and loads validated OMOP records into PostgreSQL — in seconds, not months.

```
FHIR R4 Server  ──►  Extract  ──►  Transform (Whistle Engine)  ──►  Load  ──►  OMOP PostgreSQL
```

## Key Capabilities

| Capability | Details |
|---|---|
| **FHIR Extraction** | Connects to HAPI FHIR, GCP Healthcare API, or any FHIR R4 endpoint. Auto-discovers server capabilities. Handles pagination. |
| **Pre-Built Mappings** | 4 templates ship out of the box: Patient→Person, Encounter→Visit, Condition→Condition Occurrence, Observation→Measurement |
| **Whistle-Compatible Engine** | Uses Google's Whistle mapping language format. Forward-compatible with the full Whistle CLI. Extensible for custom mappings. |
| **OMOP CDM v5.4** | Full schema validation. Vocabulary-aware (Athena-ready). Handles concept ID mapping, date coercion, and NOT NULL constraints. |
| **REST API** | FastAPI with Swagger UI. Create sources, configure mappings, execute pipelines, and query results — all via API. |
| **Docker-Ready** | `docker compose up` gives you a working environment with PostgreSQL and the API in under 60 seconds. |

## Live Demo Results

Tested against the public [HAPI FHIR R4 server](https://hapi.fhir.org/baseR4):

| Stage | Records | Errors | Duration |
|-------|---------|--------|----------|
| Extract | 6,718 FHIR resources | 0 | ~20s |
| Transform | 6,718 OMOP records | 0 | <1s |
| Load | 6,718 rows written | 0 | ~5s |

**100% success rate** across 3,654 persons, 638 visits, 161 conditions, and 2,265 measurements.

## Architecture

Clean Architecture with hexagonal port/adapter pattern. Every external dependency is behind a protocol interface — swap FHIR sources, target databases, or vocabulary services without touching business logic.

| Layer | Responsibility |
|-------|---------------|
| **Domain** | Entities (Pipeline, Source, Mapping), value objects, ports, domain services |
| **Application** | Use cases, DTOs, command/query separation |
| **Infrastructure** | FHIR clients, PostgreSQL writer, Whistle engine, in-memory repos |
| **Presentation** | FastAPI REST API, Pydantic schemas |

**Test coverage:** 86 tests across domain, application, infrastructure, and integration layers.

## Roadmap

| Phase | Scope |
|-------|-------|
| **Phase 1** (current) | Core pipeline, 4 resource types, HAPI FHIR + GCP connectors, PostgreSQL target |
| **Phase 2** | Procedure, Medication, Drug Exposure mappings. Live Athena vocabulary lookup. Batch optimization. |
| **Phase 3** | Streaming mode, parallel extraction, dead-letter queues, observability dashboard |
| **Phase 4** | Multi-tenant, RBAC, audit logging, SOC 2 compliance |

## Get Started

```bash
docker compose up -d --build
python scripts/demo.py
# → Swagger UI at http://localhost:8000/docs
```

---

**Stack:** Python 3.11+ | FastAPI | asyncpg | PostgreSQL 16 | Docker Compose
**Standards:** FHIR R4 | OMOP CDM v5.4 | Google Whistle DSL
