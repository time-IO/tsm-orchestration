#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE SCHEMA postgis;
    CREATE EXTENSION postgis SCHEMA postgis;
    ALTER ROLE $POSTGRES_USER SET search_path TO public, postgis;
EOSQL
