#!/bin/bash
set -e

# check if SMS_API_ACCESS is true
if [ "$SMS_API_ACCESS" == "true" ]; then
    echo "POSTGRES_USER=$POSTGRES_USER" >> my_crontab
    echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> my_crontab
    echo "SMS_URL=$SMS_URL" >> my_crontab
    echo "0 * * * * /usr/bin/python3 /home/postgres/update_sms_tables.py > /proc/1/fd/1 2>/proc/1/fd/2" >> my_crontab
    crontab my_crontab
else
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -f /sql/sms/sms_ddl.sql
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
fi