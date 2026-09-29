#!/bin/bash
# Builds the patched Solr 5.1.0 server and packages it with the knowledge-graph
# plugin into ./deploy. Several repositories referenced by Solr 5.1.0's ivy
# configuration are gone (uk.maven.org, maven.restlet.org, the old Cloudera
# layout) and repo1 rejects plain HTTP, so the resolvers are rewritten below.
set -e

SOLR_TAG=releases/lucene-solr/5.1.0
IVY_VERSION=2.3.0
MIRROR=https://maven-central.storage-download.googleapis.com/maven2

if [ ! -d lucene-solr ]; then
  git clone --depth 1 --branch "$SOLR_TAG" https://github.com/apache/lucene-solr lucene-solr
  git apply patches/lucene_solr_5_1_0.patch --directory=lucene-solr
fi

mkdir -p ~/.ant/lib
[ -f ~/.ant/lib/ivy-$IVY_VERSION.jar ] || \
  curl -fsSL -o ~/.ant/lib/ivy-$IVY_VERSION.jar \
    "$MIRROR/org/apache/ivy/ivy/$IVY_VERSION/ivy-$IVY_VERSION.jar"

SETTINGS=lucene-solr/lucene/ivy-settings.xml
if ! grep -q gcs-central "$SETTINGS"; then
  sed -i \
    -e "s#<resolvers>#<resolvers>\n    <ibiblio name=\"gcs-central\" root=\"$MIRROR\" m2compatible=\"true\" />#" \
    -e 's#<resolver ref="local"/>#<resolver ref="local"/>\n      <resolver ref="gcs-central"/>#' \
    -e 's#root="http://maven.restlet.org"#root="https://maven.restlet.talend.com"#' \
    -e 's#root="http://repository.cloudera.com/content/repositories/releases"#root="https://repository.cloudera.com/artifactory/cloudera-repos"#' \
    "$SETTINGS"
fi

(cd lucene-solr/solr && ant example)
(cd knowledge-graph && mvn -B clean package)
ant package-nobuild
rm -f deploy/solr/server/lib/original-knowledge-graph-*.jar
chmod +x deploy/*.sh deploy/solr/bin/solr
