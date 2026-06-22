#!/usr/bin/env bash
set -euo pipefail

sudo journalctl -u ais-backend.service -u ais-frontend.service -f
