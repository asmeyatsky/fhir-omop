# FHIR-to-OMOP Data Accelerator

Transforms FHIR R4 clinical data into OMOP CDM v5.4 datasets. Extracts from any FHIR R4 server, maps via a Whistle-compatible engine, and loads into PostgreSQL.

## Architecture

Clean Architecture (hexagonal) with four layers:

```
Presentation (FastAPI)  →  Application (Use Cases)  →  Domain (Entities, Ports)
                                                          ↑
                                                    Infrastructure (Adapters)
```

**Phase 1 scope:** Patient, Encounter, Condition, Observation resources mapped to OMOP person, visit_occurrence, condition_occurrence, measurement tables.

## Quick Start

```bash
# Start PostgreSQL (OMOP schema) + API
docker compose up -d --build

# Run the end-to-end demo against HAPI FHIR public server
pip install httpx
python scripts/demo.py
```

The demo extracts ~6700 resources from [HAPI FHIR R4](https://hapi.fhir.org/baseR4), transforms them, and loads all records into PostgreSQL. Takes about 30 seconds.

## API

Base URL: `http://localhost:8000/api/v1` | Swagger UI: `http://localhost:8000/docs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/sources` | Create FHIR source connection |
| GET | `/api/v1/sources` | List source connections |
| POST | `/api/v1/sources/{id}/test` | Test FHIR connectivity |
| GET | `/api/v1/mappings/templates` | List pre-built mapping templates |
| POST | `/api/v1/mappings` | Create mapping from template |
| GET | `/api/v1/mappings` | List mapping configurations |
| POST | `/api/v1/pipelines` | Execute FHIR-to-OMOP pipeline |
| GET | `/api/v1/pipelines` | List pipelines |
| GET | `/api/v1/pipelines/{id}` | Get pipeline status |

### Pipeline execution

```bash
# 1. Create a source connection
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{"name": "HAPI FHIR", "base_url": "https://hapi.fhir.org/baseR4", "server_type": "hapi", "auth_method": "api_key"}'

# 2. Create mappings from templates
curl -X POST http://localhost:8000/api/v1/mappings \
  -H "Content-Type: application/json" \
  -d '{"name": "Patient to Person", "template_id": "patient-to-person"}'

# 3. Run pipeline
curl -X POST http://localhost:8000/api/v1/pipelines \
  -H "Content-Type: application/json" \
  -d '{"name": "Demo", "source_connection_id": "<source-id>", "mapping_config_ids": ["<mapping-id>"], "target_connection_string": "postgresql://omop:omop@omop-db:5432/omop"}'
```

## Mapping Templates

| Template | FHIR Resource | OMOP Table |
|----------|---------------|------------|
| `patient-to-person` | Patient | person |
| `encounter-to-visit` | Encounter | visit_occurrence |
| `condition-to-condition-occurrence` | Condition | condition_occurrence |
| `observation-to-measurement` | Observation | measurement |

## Development

```bash
# Create venv and install
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests (86 tests)
pytest

# Run with coverage
pytest --cov=src

# Lint
ruff check src/ tests/
mypy src/
```

### Project structure

```
src/
├── domain/           # Entities, value objects, ports, services, events
├── application/      # Use cases (commands + queries), DTOs
├── infrastructure/   # Adapters (FHIR, OMOP, Whistle), repositories, config
└── presentation/     # FastAPI app, routers, schemas
tests/
├── domain/           # Entity and value object tests
├── application/      # Use case tests
├── infrastructure/   # Adapter and repository tests
└── integration/      # API endpoint tests
db/init/              # OMOP CDM v5.4 schema SQL
scripts/              # Demo and utility scripts
```

## Query OMOP Data

```bash
docker compose exec omop-db psql -U omop -c "SELECT count(*) FROM person;"
docker compose exec omop-db psql -U omop -c "SELECT * FROM visit_occurrence LIMIT 5;"
```

## Tech Stack

- **Python 3.11+**, FastAPI, Pydantic v2
- **asyncpg** for PostgreSQL async I/O
- **httpx** for FHIR server communication
- **PostgreSQL 16** with OMOP CDM v5.4 schema
- **Docker Compose** for local development
