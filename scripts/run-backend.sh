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

# 热加载：默认开启(改 .py 自动重启 worker，免去手动 systemctl restart)。
# 只 allowlist 源码目录，避免 watchfiles 去 walk .venv310 / data/chroma_db / frontend /
# logs 这些大目录(否则启动慢、inotify watch 爆量)。生产可设 AIS_RELOAD=0 关闭。
# 注意：根目录的 main.py 不在监视范围内(它极少改，且只能整目录监视)，改它仍需手动重启。
RELOAD_ARGS=()
if [ "${AIS_RELOAD:-1}" != "0" ]; then
  RELOAD_ARGS=(--reload
    --reload-dir "$ROOT_DIR/core"
    --reload-dir "$ROOT_DIR/modules"
    --reload-dir "$ROOT_DIR/storage")
fi

exec "$PYTHON" -m uvicorn main:app \
  --host "${AIS_BACKEND_HOST:-0.0.0.0}" \
  --port "${AIS_BACKEND_PORT:-2222}" \
  --http h11 \
  "${RELOAD_ARGS[@]}"
