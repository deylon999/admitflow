#!/usr/bin/env bash
# Compatibility entrypoint for existing backup commands and cron jobs.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec bash "$script_dir/ops/backup_production.sh" "$@"
