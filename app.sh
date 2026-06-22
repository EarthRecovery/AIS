#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sudo install -m 0644 "$ROOT_DIR/systemd/ais-backend.service" /etc/systemd/system/ais-backend.service
sudo systemctl daemon-reload
sudo systemctl enable ais-backend.service
sudo systemctl restart ais-backend.service
sudo systemctl --no-pager --full status ais-backend.service
