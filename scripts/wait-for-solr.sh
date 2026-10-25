#!/bin/bash
# Blocks until every use-case core answers /admin/ping (or times out).
# Env: SOLR_URL (default http://localhost:8983/solr), TIMEOUT seconds (default 120)
set -uo pipefail
SOLR_URL="${SOLR_URL:-http://localhost:8983/solr}"
TIMEOUT="${TIMEOUT:-120}"
deadline=$((SECONDS + TIMEOUT))
for core in jobs ecommerce healthcare support; do
  until curl -fsS "$SOLR_URL/$core/admin/ping?wt=json" > /dev/null 2>&1; do
    if [ $SECONDS -ge $deadline ]; then echo "timed out waiting for core $core" >&2; exit 1; fi
    sleep 2
  done
  echo "core $core is up"
done
