#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -x "$ROOT_DIR/.venv310/bin/python" ]; then
  PYTHON="$ROOT_DIR/.venv310/bin/python"
elif [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON="$ROOT_DIR/.venv/bin/python"
elif [ -x "$ROOT_DIR/venv/bin/python" ]; then
  PYTHON="$ROOT_DIR/venv/bin/python"
else
  PYTHON="python3"
fi

exec "$PYTHON" -m uvicorn main:app \
  --host "${AIS_BACKEND_HOST:-0.0.0.0}" \
  --port "${AIS_BACKEND_PORT:-2222}" \
  --http h11
