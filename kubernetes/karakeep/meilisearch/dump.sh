#!/bin/sh
set -x

MEILI_DATA_DIR=/meili_data

mkdir -p $MEILI_DATA_DIR/dumps
mkdir -p $MEILI_DATA_DIR/migration

CUR_VERSION=$(curl -s -X GET "http://localhost:$MEILISEARCH_SERVICE_PORT/version" -H "Authorization: Bearer $MEILI_MASTER_KEY" | sed -n 's/.*"pkgVersion":"\([^"]*\)".*/\1/p')

TASKUID=$(curl -s -X POST "http://localhost:$MEILISEARCH_SERVICE_PORT/dumps" -H "Authorization: Bearer $MEILI_MASTER_KEY" | sed -n 's/.*"taskUid":[[:space:]]*\([0-9]*\).*/\1/p')

while :; do
    if curl -s -X GET "http://localhost:$MEILISEARCH_SERVICE_PORT/tasks/$TASKUID" -H "Authorization: Bearer $MEILI_MASTER_KEY" | grep succeeded ; then
        echo "[$(date) dump task '$TASKUID' succeeded"
        break
    fi
    echo "[$(date)] waiting for dump task '$TASKUID' to complete"
    sleep 5
done

echo $CUR_VERSION > $MEILI_DATA_DIR/migration/VERSION
