#!/usr/bin/env bash
set -euo pipefail

sudo systemctl --no-pager --full status ais-backend.service ais-frontend.service
