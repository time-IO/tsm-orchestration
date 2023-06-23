#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE extension postgres_fdw;
    CREATE SERVER sms_db
      FOREIGN DATA WRAPPER postgres_fdw
      OPTIONS (host '$SMS_DB_HOST', dbname '$SMS_DB_DB', port '$SMS_DB_PORT');
    CREATE USER MAPPING FOR $POSTGRES_USER
      SERVER sms_db
      OPTIONS (user '$SMS_DB_USER', password '$SMS_DB_PASSWORD');
EOSQL