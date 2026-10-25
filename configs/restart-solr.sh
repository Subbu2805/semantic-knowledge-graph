#!/bin/bash
# Env: SOLR_HEAP (default 5g), SOLR_PORT (default 8983), SOLR_FOREGROUND=1 to run in the foreground (containers)
cd "$(dirname "${BASH_SOURCE[0]}")"
HEAP="${SOLR_HEAP:-5g}"
PORT="${SOLR_PORT:-8983}"
if [ "${SOLR_FOREGROUND:-0}" = "1" ]; then
  exec solr/bin/solr start -f -m "$HEAP" -p "$PORT" -a "-server"
fi
solr/bin/solr restart -m "$HEAP" -p "$PORT" -a "-server"
