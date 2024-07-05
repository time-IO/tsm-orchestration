#!/bin/bash
set -e

echo 'Create schema-thing-mapping table if not exists'
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" <<-EOSQL
    CREATE TABLE IF NOT EXISTS public."schema_thing_mapping"(
	  "schema_name"		  VARCHAR(100) NOT NULL,
    "thing_uuid"	UUID NOT NULL,
	  UNIQUE("schema_name", "thing_uuid"));
EOSQL
echo 'schema-thing-mapping table created'