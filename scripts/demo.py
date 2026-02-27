#!/usr/bin/env python3
"""
FHIR-to-OMOP Accelerator — End-to-End Demo Script

Demonstrates the full pipeline:
1. Create a source connection to HAPI FHIR public R4 server
2. Test the connection (auto-discovers capabilities)
3. Create mapping configurations from pre-built templates
4. Execute a pipeline: Extract FHIR → Transform via Whistle → Load to OMOP PostgreSQL
5. Query results

Usage — full stack in Docker (API + OMOP DB):
    docker compose up -d
    python scripts/demo.py

Usage — API on your machine, OMOP DB in Docker (local dev):
    docker compose up -d omop-db
    # In another terminal: STORAGE_BACKEND=memory uvicorn src.presentation.api.app:app --host 0.0.0.0 --port 8000
    python scripts/demo.py --omop-url postgresql://omop:omop@localhost:5433/omop
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import httpx

DEFAULT_API_URL = "http://localhost:8000"
HAPI_FHIR_URL = "https://hapi.fhir.org/baseR4"
# Default when API runs in Docker (same network as omop-db)
OMOP_CONNECTION_DOCKER = "postgresql://omop:omop@omop-db:5432/omop"
# When API runs on host, DB is at localhost:5433 (docker compose maps 5433:5432)
OMOP_CONNECTION_LOCAL = "postgresql://omop:omop@localhost:5433/omop"


def print_header(text: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_json(data: dict) -> None:
    print(json.dumps(data, indent=2, default=str))


def wait_for_api(base_url: str, timeout: int = 30) -> None:
    """Wait for the API to become healthy."""
    print(f"Waiting for API at {base_url}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = httpx.get(f"{base_url}/health", timeout=3)
            if r.status_code == 200:
                print(f"  API is healthy: {r.json()}")
                return
        except httpx.ConnectError:
            pass
        time.sleep(1)
    print("ERROR: API did not become healthy in time")
    sys.exit(1)


def run_demo(base_url: str, omop_connection: str) -> None:
    api = f"{base_url}/api/v1"
    client = httpx.Client(timeout=120)  # Long timeout for FHIR extraction

    # ============================================================
    # Step 1: Create Source Connection
    # ============================================================
    print_header("Step 1: Create FHIR Source Connection")
    r = client.post(f"{api}/sources", json={
        "name": "HAPI FHIR R4 Public Server",
        "base_url": HAPI_FHIR_URL,
        "server_type": "hapi",
        "auth_method": "api_key",
    })
    r.raise_for_status()
    source = r.json()
    source_id = source["id"]
    print(f"  Created source connection: {source['name']}")
    print(f"  ID: {source_id}")
    print(f"  Status: {source['status']}")

    # ============================================================
    # Step 2: Test Source Connection
    # ============================================================
    print_header("Step 2: Test Connection to HAPI FHIR")
    r = client.post(f"{api}/sources/{source_id}/test")
    r.raise_for_status()
    source = r.json()
    print(f"  Status: {source['status']}")
    print(f"  Capabilities: {len(source['capabilities'])} resource types supported")
    if source["capabilities"]:
        print(f"  Sample: {', '.join(source['capabilities'][:10])}...")

    if source["status"] != "active":
        print(f"  ERROR: Connection test failed: {source.get('error_message')}")
        sys.exit(1)

    # ============================================================
    # Step 3: List Available Templates
    # ============================================================
    print_header("Step 3: Available Mapping Templates")
    r = client.get(f"{api}/mappings/templates")
    r.raise_for_status()
    templates = r.json()
    for t in templates:
        print(f"  [{t['template_id']}] {t['name']}")
        print(f"    {t['source_resource']} -> {t['target_table']} ({t['field_count']} fields)")

    # ============================================================
    # Step 4: Create Mappings from Templates
    # ============================================================
    print_header("Step 4: Create Mapping Configurations")
    mapping_ids = []
    template_configs = [
        ("Patient Demographics", "patient-to-person"),
        ("Encounter to Visit", "encounter-to-visit"),
        ("Condition Mapping", "condition-to-condition-occurrence"),
        ("Lab Observations", "observation-to-measurement"),
    ]

    for name, template_id in template_configs:
        r = client.post(f"{api}/mappings", json={
            "name": name,
            "template_id": template_id,
        })
        r.raise_for_status()
        mapping = r.json()
        mapping_ids.append(mapping["id"])
        print(f"  Created: {mapping['name']} ({mapping['source_resource']} -> {mapping['target_table']})")
        print(f"    Status: {mapping['status']}, Fields: {mapping['field_count']}")

    # ============================================================
    # Step 5: Execute Pipeline
    # ============================================================
    print_header("Step 5: Execute FHIR-to-OMOP Pipeline")
    print("  Connecting to HAPI FHIR, extracting resources...")
    print("  This may take 30-60 seconds depending on HAPI server load.")
    print()

    r = client.post(f"{api}/pipelines", json={
        "name": "HAPI FHIR Demo Pipeline",
        "source_connection_id": source_id,
        "mapping_config_ids": mapping_ids,
        "target_connection_string": omop_connection,
    })
    r.raise_for_status()
    pipeline = r.json()

    print(f"  Pipeline: {pipeline['name']}")
    print(f"  Status: {pipeline['status']}")
    print(f"  Total Records: {pipeline['total_records']}")
    print(f"  Total Errors: {pipeline['total_errors']}")
    print()

    if pipeline["stage_results"]:
        print("  Stage Results:")
        for stage in pipeline["stage_results"]:
            status_icon = "OK" if stage["error_count"] == 0 else f"{stage['error_count']} errors"
            print(f"    {stage['stage']:>12}: {stage['records_in']:>6} in -> {stage['records_out']:>6} out  [{status_icon}]")

    if pipeline.get("error_message"):
        print(f"\n  Pipeline Error: {pipeline['error_message']}")

    # ============================================================
    # Step 6: Verify Results
    # ============================================================
    print_header("Step 6: Pipeline Summary")
    r = client.get(f"{api}/pipelines/{pipeline['id']}")
    r.raise_for_status()
    final = r.json()

    print(f"  Pipeline ID: {final['id']}")
    print(f"  Status: {final['status']}")
    print(f"  Started: {final.get('started_at', 'N/A')}")
    print(f"  Completed: {final.get('completed_at', 'N/A')}")
    print(f"  Records Loaded: {final['total_records']}")
    print(f"  Errors: {final['total_errors']}")

    # ============================================================
    # Summary
    # ============================================================
    print_header("Demo Complete")
    if final["status"] == "completed":
        print("  FHIR-to-OMOP pipeline executed successfully!")
        print(f"  {final['total_records']} OMOP records loaded to PostgreSQL")
        print()
        print("  Explore the API:")
        print(f"    Swagger UI:  {base_url}/docs")
        print(f"    Sources:     GET {api}/sources")
        print(f"    Mappings:    GET {api}/mappings")
        print(f"    Templates:   GET {api}/mappings/templates")
        print(f"    Pipelines:   GET {api}/pipelines")
        print()
        print("  Query OMOP data directly:")
        if "localhost" in omop_connection:
            print("    psql postgresql://omop:omop@localhost:5433/omop -c 'SELECT count(*) FROM person;'")
            print("    psql postgresql://omop:omop@localhost:5433/omop -c 'SELECT * FROM person LIMIT 5;'")
        else:
            print("    docker compose exec omop-db psql -U omop -c 'SELECT count(*) FROM person;'")
            print("    docker compose exec omop-db psql -U omop -c 'SELECT * FROM person LIMIT 5;'")
    else:
        print(f"  Pipeline finished with status: {final['status']}")
        if final.get("error_message"):
            print(f"  Error: {final['error_message']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="FHIR-to-OMOP Demo")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API base URL")
    parser.add_argument(
        "--omop-url",
        default=os.environ.get("OMOP_CONNECTION", OMOP_CONNECTION_DOCKER),
        help="OMOP PostgreSQL connection string (default: omop-db:5432 for Docker; use postgresql://omop:omop@localhost:5433/omop when API runs on host)",
    )
    parser.add_argument("--skip-wait", action="store_true", help="Skip API health check wait")
    args = parser.parse_args()

    omop_connection = args.omop_url

    print_header("FHIR-to-OMOP Data Accelerator — Live Demo")
    print(f"  API: {args.api_url}")
    print(f"  FHIR Source: {HAPI_FHIR_URL}")
    print(f"  OMOP Target: {omop_connection}")

    if not args.skip_wait:
        wait_for_api(args.api_url)

    run_demo(args.api_url, omop_connection)


if __name__ == "__main__":
    main()
