#!/bin/bash
set -e

if [ "$CV_API_ACCESS" == "false" ]; then
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -f /sql/sms_cv/sms_cv_ddl.sql
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" <<-EOSQL
        CREATE extension if not exists postgres_fdw;
        CREATE SERVER sms_cv_db
            FOREIGN DATA WRAPPER postgres_fdw
            OPTIONS (host '$CV_DB_HOST', dbname '$CV_DB_DB', port '$CV_DB_PORT');
        CREATE USER MAPPING FOR $POSTGRES_USER 
            SERVER sms_cv_db
            OPTIONS (user '$CV_DB_USER', password '$CV_DB_PASSWORD');
EOSQL
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -f /sql/sms_cv/sms_cv_foreign_tables.sql
fi