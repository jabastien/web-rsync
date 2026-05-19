#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Activate venv
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv..."
  uv venv .venv
  uv pip install -e backend/
fi

source .venv/bin/activate

# Ensure data dirs
mkdir -p data/logs data/ssh

# Load env
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "Starting web-RSync backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
