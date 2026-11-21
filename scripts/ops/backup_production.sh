#!/usr/bin/env bash
# Consistent PostgreSQL dump plus the raw store, verified by restoring into a throwaway database.
# Usage: scripts/backup_production.sh <output-dir>
# Env: COMPOSE (default "docker compose -f compose.prod.yaml"), RAW_SERVICE (default worker),
#      KEEP_DAYS (default 14). The copies are not encrypted: keep the directory private.
set -euo pipefail
umask 077
output=${1:?output directory is required}
compose=${COMPOSE:-docker compose -f compose.prod.yaml}
raw_service=${RAW_SERVICE:-worker}
keep_days=${KEEP_DAYS:-14}
stamp=$(date -u +%Y%m%dT%H%M%SZ)
target="$output/$stamp"
mkdir -p "$target"

$compose exec -T db pg_dump -Fc -U admitflow admitflow > "$target/db.dump"
$compose exec -T "$raw_service" tar -C /app/var -cf - raw > "$target/raw.tar"
tar -tf "$target/raw.tar" > /dev/null

count_rows='SELECT table_name, (xpath($$/row/c/text()$$, query_to_xml(format($$SELECT count(*) AS c FROM %I$$, table_name), false, true, $$$$)))[1]::text FROM information_schema.tables WHERE table_schema = $$public$$ ORDER BY 1'
check=admitflow_restore_check
$compose exec -T db psql -qAt -U admitflow -d admitflow -c "$count_rows" > "$target/source-counts.txt"
$compose exec -T db dropdb --if-exists -U admitflow "$check"
$compose exec -T db createdb -U admitflow "$check"
$compose exec -T db pg_restore --no-owner -U admitflow -d "$check" < "$target/db.dump"
$compose exec -T db psql -qAt -U admitflow -d "$check" -c "$count_rows" > "$target/restored-counts.txt"
$compose exec -T db dropdb -U admitflow "$check"
if ! diff -q "$target/source-counts.txt" "$target/restored-counts.txt" > /dev/null; then
  echo "backup_verification_failed: row counts differ" >&2
  exit 1
fi

find "$output" -mindepth 1 -maxdepth 1 -type d -mtime "+$keep_days" -exec rm -rf {} +
echo "{\"backup\":\"$target\",\"verified\":true,\"tables\":$(wc -l < "$target/source-counts.txt")}"
