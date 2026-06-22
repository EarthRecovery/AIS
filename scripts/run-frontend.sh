#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/frontend"

exec npm run dev -- \
  --host "${AIS_FRONTEND_HOST:-0.0.0.0}" \
  --port "${AIS_FRONTEND_PORT:-8100}" \
  --strictPort
