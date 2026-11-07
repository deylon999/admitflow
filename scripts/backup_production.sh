#!/usr/bin/env bash
# Compatibility entry point. Python 3 is also required by scripts/ops_check.py.
set -euo pipefail
exec python3 "$(dirname "$0")/backup_production.py" "$@"
