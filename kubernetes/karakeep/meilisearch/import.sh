#!/bin/sh

MEILI_DATA_DIR=/meili_data

if [ ! -f $MEILI_DATA_DIR/migration/VERSION ]; then
  echo "$MEILI_DATA_DIR/migration/VERSION not found. Exiting"
  exit 0
fi

if [ ! -d $MEILI_DATA_DIR/dumps ] || [ -z "$(ls -A $MEILI_DATA_DIR/dumps 2>/dev/null)" ]; then
  echo "dump not found at $MEILI_DATA_DIR/dumps. Exiting"
  exit 0
fi

MEILI_LATESET_DUMP=$(ls -1 $MEILI_DATA_DIR/dumps | sort -r | head -1)

cmd_version=$(meilisearch --version | awk '{print $2}')

file_version=$(cat $MEILI_DATA_DIR/migration/VERSION)

if [ "$cmd_version" = "$file_version" ]; then
  echo "dump version is the same as the current binary version, wiping dump data and start"
  rm -rf $MEILI_DATA_DIR/dumps/*
  rm -rf $MEILI_DATA_DIR/migration
  exit 0
fi

mv $MEILI_DATA_DIR/data.ms $MEILI_DATA_DIR/data.ms.bk

# copied from https://github.com/meilisearch/meilisearch-migration/blob/16027aff41137f0644a3c385df8f74e219776264/scripts/update_meilisearch_version.sh#L261-L303

meilisearch --import-dump=$MEILI_DATA_DIR/dumps/$MEILI_LATESET_DUMP --master-key="$MEILI_MASTER_KEY" 2>logs &
echo -e "Run local binary importing the dump and creating the new data.ms."
sleep 2

if ps | grep "meilisearch" -q; then
  echo -e "Meilisearch started successfully and is importing the dump."
else
  echo -e "Meilisearch could not start"
  exit 1
fi

while true
do
  curl -X GET 'http://localhost:7700/health' \
    --header "Authorization: Bearer $MEILI_MASTER_KEY" --show-error -s -i > curl_dump_index_response
  cat curl_dump_index_response | grep "200 OK" -q
  if cat curl_dump_index_response | grep '"status":"available"' -q; then
    rm curl_dump_index_response
    break
  else
    echo "Failed to index the dump: $(cat curl_dump_index_response)"
    rm curl_dump_index_response
  fi
  sleep 2
done
echo -e "Meilisearch is done indexing the dump."

rm -r $MEILI_DATA_DIR/dumps
rm -r $MEILI_DATA_DIR/migration

# Kill local Meilisearch process
echo -e "Kill local Meilisearch process."
pkill meilisearch
