#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

sudo install -m 0644 "$ROOT_DIR/systemd/ais-backend.service" /etc/systemd/system/ais-backend.service
sudo install -m 0644 "$ROOT_DIR/systemd/ais-frontend.service" /etc/systemd/system/ais-frontend.service

sudo systemctl daemon-reload
sudo systemctl enable ais-backend.service ais-frontend.service
sudo systemctl restart ais-backend.service ais-frontend.service

sudo systemctl --no-pager --full status ais-backend.service ais-frontend.service
