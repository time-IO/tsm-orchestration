#!/bin/bash
set -e

if [ "$SMS_ACCESS_TYPE" == "db" ]; then
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -f /sql/sms/sms_ddl.sql
    echo 'setting up sms foreign data wrapper and remote tables'
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" <<-EOSQL
        CREATE extension if not exists postgres_fdw;
        CREATE SERVER sms_db
            FOREIGN DATA WRAPPER postgres_fdw
            OPTIONS (host '$SMS_DB_HOST', dbname '$SMS_DB_DB', port '$SMS_DB_PORT');
        CREATE USER MAPPING FOR $POSTGRES_USER
            SERVER sms_db
            OPTIONS (user '$SMS_DB_USER', password '$SMS_DB_PASSWORD');
EOSQL
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -f /sql/sms/sms_foreign_tables.sql
    echo 'sms remote tables created'
fi