#!/usr/bin/env bash
# Launch the Streamlit dashboard.
# Usage: ./scripts/run_app.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -f "${ROOT}/.env" ]; then
  echo "⚠️  No .env file found. Copy .env.example to .env and fill in credentials."
  exit 1
fi

STREAMLIT="${ROOT}/.venv/bin/streamlit"
if [ ! -f "${STREAMLIT}" ]; then
  echo "⚠️  .venv/bin/streamlit not found. Activate your venv: source .venv/bin/activate"
  exit 1
fi

echo "▶ Starting Streamlit app on http://localhost:8501 ..."
"${STREAMLIT}" run "${ROOT}/app/main.py"
