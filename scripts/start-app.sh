#!/bin/bash
# One-command startup: launches Solr with the knowledge-graph plugin, indexes the
# use-case datasets if the cores are empty, verifies them with the smoke test and
# starts the SKG Explorer UI.
# Works from the repo root (after ./build-solr.sh) or from inside a deploy/ copy.
# Env: SOLR_PORT (8983), SOLR_HEAP (2g), UI_PORT (8080), SKIP_UI=1, RELOAD_DATA=1
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -x "$ROOT/solr/bin/solr" ]; then DEPLOY="$ROOT"
elif [ -x "$ROOT/deploy/solr/bin/solr" ]; then DEPLOY="$ROOT/deploy"
else echo "Solr distribution not found; run ./build-solr.sh first" >&2; exit 1; fi

export SOLR_PORT="${SOLR_PORT:-8983}"
export SOLR_HEAP="${SOLR_HEAP:-2g}"
export SOLR_URL="http://localhost:$SOLR_PORT/solr"

(cd "$DEPLOY" && ./restart-solr.sh)
"$ROOT/scripts/wait-for-solr.sh"

for core in jobs ecommerce healthcare support; do
  n=$(curl -fsS "$SOLR_URL/$core/select?q=*:*&rows=0&wt=json" | python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["numFound"])')
  if [ "$n" = "0" ] || [ "${RELOAD_DATA:-0}" = "1" ]; then "$ROOT/scripts/load-datasets.sh" "$core"; fi
done
python3 "$ROOT/scripts/smoke_test.py"

if [ "${SKIP_UI:-0}" != "1" ]; then
  echo "starting SKG Explorer on http://localhost:${UI_PORT:-8080}"
  exec python3 "$ROOT/ui/server.py"
fi
