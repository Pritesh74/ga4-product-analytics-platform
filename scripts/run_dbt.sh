#!/usr/bin/env bash
# Run a full dbt build from the repo root.
# Usage: ./scripts/run_dbt.sh [target]   (target defaults to "dev")
set -euo pipefail

TARGET="${1:-dev}"
PROFILES_DIR="$(cd "$(dirname "$0")/.." && pwd)/dbt"
PROJECT_DIR="${PROFILES_DIR}"

echo "▶ Running dbt deps..."
dbt deps --project-dir "${PROJECT_DIR}" --profiles-dir "${PROFILES_DIR}"

echo "▶ Running dbt build (target: ${TARGET})..."
dbt build \
  --project-dir "${PROJECT_DIR}" \
  --profiles-dir "${PROFILES_DIR}" \
  --target "${TARGET}" \
  --select staging intermediate marts experiments

echo "✅ dbt build complete."
