#!/bin/bash
# Builds a runnable deployment from the released Solr 5.1.0 binary distribution
# instead of a full lucene-solr source checkout. The two changes carried by
# patches/lucene_solr_5_1_0.patch are applied to the distribution:
#   * FacetField: deep copy the term BytesRef before sub-faceting
#   * jetty.xml: cap maxThreads at 100
set -e

SOLR_VERSION=5.1.0
MIRROR=${MIRROR:-https://archive.apache.org/dist/lucene/solr}
BASE=$(cd "$(dirname "$0")" && pwd)
DOWNLOADS=${DOWNLOADS:-$BASE/downloads}
WORK=$BASE/.solr-dist
SOLR_HOME=$BASE/lucene-solr/solr

mkdir -p "$DOWNLOADS" "$WORK"

for archive in solr-$SOLR_VERSION.tgz solr-$SOLR_VERSION-src.tgz; do
    if [ ! -f "$DOWNLOADS/$archive" ]; then
        echo "Downloading $archive..."
        curl -fL -o "$DOWNLOADS/$archive" "$MIRROR/$SOLR_VERSION/$archive"
    fi
done

echo "Unpacking Solr $SOLR_VERSION..."
rm -rf "$WORK/solr-$SOLR_VERSION" "$WORK/src" "$WORK/classes" "$WORK/warlib"
tar xzf "$DOWNLOADS/solr-$SOLR_VERSION.tgz" -C "$WORK"
mkdir -p "$WORK/src"
tar xzf "$DOWNLOADS/solr-$SOLR_VERSION-src.tgz" -C "$WORK/src" \
    "solr-$SOLR_VERSION/solr/core/src/java/org/apache/solr/search/facet"

DIST=$WORK/solr-$SOLR_VERSION
FACET_DIR=$WORK/src/solr-$SOLR_VERSION/solr/core/src/java/org/apache/solr/search/facet

echo "Patching FacetField and jetty.xml..."
sed -i.bak 's/new Term(sf.getName(), br.clone())/new Term(sf.getName(), BytesRef.deepCopyOf(br))/' \
    "$FACET_DIR/FacetField.java"
sed -i.bak 's|<Set name="maxThreads">10000</Set>|<Set name="maxThreads">100</Set>|' \
    "$DIST/server/etc/jetty.xml"

mkdir -p "$WORK/warlib" "$WORK/classes"
(cd "$WORK/warlib" && jar xf "$DIST/server/webapps/solr.war" WEB-INF/lib)
CLASSPATH_JARS=$(ls "$WORK"/warlib/WEB-INF/lib/*.jar "$DIST"/dist/*.jar "$DIST"/dist/solrj-lib/*.jar | tr '\n' ':')
javac -nowarn -cp "$CLASSPATH_JARS" -d "$WORK/classes" "$FACET_DIR"/*.java
(cd "$WORK/classes" && jar uf "$WORK/warlib/WEB-INF/lib/solr-core-$SOLR_VERSION.jar" org/apache/solr/search/facet)
(cd "$WORK/warlib" && jar uf "$DIST/server/webapps/solr.war" "WEB-INF/lib/solr-core-$SOLR_VERSION.jar")

echo "Laying out $SOLR_HOME..."
rm -rf "$SOLR_HOME"
mkdir -p "$SOLR_HOME/bin"
cp -r "$DIST/server" "$SOLR_HOME/"
cp "$DIST/bin/solr" "$SOLR_HOME/bin/"

echo "Building the knowledge-graph plugin..."
(cd "$BASE/knowledge-graph" && mvn clean package)

echo "Packaging the deployment..."
(cd "$BASE" && ant package-nobuild)
rm -f "$BASE/deploy/solr/server/lib/original-knowledge-graph"*.jar
chmod +x "$BASE"/deploy/*.sh "$BASE/deploy/solr/bin/solr"

echo "Done. Start Solr with: cd deploy && ./restart-solr.sh"
