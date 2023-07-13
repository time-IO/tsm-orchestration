#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE extension postgres_fdw;
    CREATE SERVER sms_cv_db
      FOREIGN DATA WRAPPER postgres_fdw
      OPTIONS (host '$CV_DB_HOST', dbname '$CV_DB_DB', port '$CV_DB_PORT');
    CREATE USER MAPPING FOR $POSTGRES_USER
      SERVER sms_cv_db
      OPTIONS (user '$CV_DB_USER', password '$CV_DB_PASSWORD');
EOSQL