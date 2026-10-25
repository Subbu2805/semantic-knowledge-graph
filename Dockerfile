# Runtime image for the Semantic Knowledge Graph (Solr 5.1.0 + plugin + use-case data).
# Build the distribution first (./build-solr.sh), then: docker compose up --build
FROM eclipse-temurin:8-jre-jammy

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl lsof procps python3 unzip \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --shell /bin/bash skg

WORKDIR /opt/skg
COPY --chown=skg:skg deploy/ ./
USER skg

ENV SOLR_HEAP=2g SOLR_PORT=8983 SOLR_FOREGROUND=1
EXPOSE 8983 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -fsS "http://localhost:${SOLR_PORT}/solr/jobs/admin/ping?wt=json" || exit 1
CMD ["./restart-solr.sh"]
