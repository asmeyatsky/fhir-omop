#!/usr/bin/env bash
#
# Single script to run the full FHIR→OMOP demo locally:
#   1. Start OMOP DB (Docker)
#   2. Start API (uvicorn on host)
#   3. Run demo (sources, mappings, pipeline)
#
# Usage: from repo root, run:
#   ./scripts/demo-local.sh
# or
#   bash scripts/demo-local.sh
#
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

API_URL="${API_URL:-http://localhost:8000}"
OMOP_URL="${OMOP_URL:-postgresql://omop:omop@localhost:5433/omop}"
VENV="${VENV:-$REPO_ROOT/.venv}"

echo "============================================================"
echo "  FHIR-to-OMOP Demo (local: API on host + OMOP DB in Docker)"
echo "============================================================"
echo "  Repo:  $REPO_ROOT"
echo "  API:   $API_URL"
echo "  OMOP:  $OMOP_URL"
echo "============================================================"

# Use docker-compose (hyphen) or docker compose (plugin)
if command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
else
  echo "ERROR: Need 'docker-compose' or 'docker compose'. Install Docker Compose."
  exit 1
fi

# --- 1. Start OMOP database ---
echo ""
echo "[1/4] Starting OMOP database ($DOCKER_COMPOSE up -d omop-db)..."
$DOCKER_COMPOSE up -d omop-db

echo "      Waiting for Postgres on port 5433..."
for i in {1..30}; do
  if (command -v nc >/dev/null 2>&1 && nc -z localhost 5433 2>/dev/null) || \
     (command -v pg_isready >/dev/null 2>&1 && pg_isready -h localhost -p 5433 -U omop 2>/dev/null); then
    echo "      Postgres is ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "      WARNING: Postgres may not be ready yet; continuing anyway."
  fi
  sleep 1
done

# --- 2. Start API in background ---
echo ""
echo "[2/4] Starting API (uvicorn, STORAGE_BACKEND=memory)..."

if [ -d "$VENV" ]; then
  set +u
  source "$VENV/bin/activate"
  set -u
fi

# Kill any existing process on 8000 so we can bind
if command -v lsof >/dev/null 2>&1; then
  lsof -ti :8000 | xargs kill -9 2>/dev/null || true
fi

STORAGE_BACKEND=memory uvicorn src.presentation.api.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!
echo "      API PID: $API_PID"

# --- 3. Wait for API health ---
echo ""
echo "[3/4] Waiting for API to be healthy..."
for i in {1..30}; do
  if curl -s -f "$API_URL/health" >/dev/null 2>&1; then
    echo "      API is healthy."
    break
  fi
  if [ "$i" -eq 30 ]; then
    kill $API_PID 2>/dev/null || true
    echo "ERROR: API did not become healthy in time."
    exit 1
  fi
  sleep 1
done

# --- 4. Run demo ---
echo ""
echo "[4/4] Running demo (sources → mappings → pipeline)..."
python scripts/demo.py --api-url "$API_URL" --omop-url "$OMOP_URL" --skip-wait

echo ""
echo "============================================================"
echo "  Demo finished. API is still running (PID $API_PID)."
echo "  Dashboard: $API_URL"
echo "  Stop API:  kill $API_PID"
echo "============================================================"
