#!/bin/bash
set -e

dt=$(date '+%d/%m/%Y %H:%M:%S');
echo "$dt - Running init script the 1st time Primary PostgreSql container is created...";

echo "$dt - Running: psql -v ON_ERROR_STOP=1 --username $POSTGRES_USER --dbname $POSTGRES_DB ...";

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
CREATE DATABASE $CUSTOM_DB_NAME;
CREATE USER $CUSTOM_DB_USER WITH PASSWORD '$CUSTOM_DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE "$CUSTOM_DB_NAME" to $CUSTOM_DB_USER;
EOSQL

echo "$dt - Init script is completed";
