#!/usr/bin/env bash
set -euo pipefail

sudo systemctl stop ais-backend.service ais-frontend.service
sudo systemctl --no-pager --full status ais-backend.service ais-frontend.service || true
