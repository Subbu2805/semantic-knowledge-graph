#!/bin/bash
# Indexes datasets/<core>.csv into the matching Solr core for every use-case corpus.
# Usage: scripts/load-datasets.sh [core ...]     (default: all corpora)
# Env:   SOLR_URL (default http://localhost:8983/solr)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOLR_URL="${SOLR_URL:-http://localhost:8983/solr}"
CORES=("$@")
[ ${#CORES[@]} -eq 0 ] && CORES=(jobs ecommerce healthcare support)

for core in "${CORES[@]}"; do
  csv="$ROOT/datasets/$core.csv"
  [ -f "$csv" ] || { echo "missing dataset $csv" >&2; exit 1; }
  echo "indexing $(($(wc -l < "$csv") - 1)) docs into $core"
  curl -fsS "$SOLR_URL/$core/update?commit=true" \
    -H 'Content-type: text/csv; charset=utf-8' --data-binary @"$csv" > /dev/null
  count=$(curl -fsS "$SOLR_URL/$core/select?q=*:*&rows=0&wt=json" | python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["numFound"])')
  echo "  $core now has $count docs"
done
