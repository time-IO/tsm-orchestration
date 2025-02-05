-- Purpose: Create a foreign server pointing to the SMS-CV database.
DO $$
BEGIN
    IF '${cv_access_type}' = 'db' THEN
        RAISE NOTICE 'Creating foreign server sms_cv_db';
        CREATE extension IF NOT EXISTS postgres_fdw;
        CREATE SERVER sms_cv_db
            FOREIGN DATA WRAPPER postgres_fdw
            OPTIONS (host '${cv_db_host}', dbname '${cv_db_db}', port '${cv_db_port}');
        CREATE USER MAPPING FOR ${flyway:user}
            SERVER sms_cv_db
            OPTIONS (user '${cv_db_user}', password '${cv_db_password}');
    ELSE
        RAISE NOTICE 'Skipping creation of foreign server sms_cv_db because cv_access_type is not db';
    END IF;
END $$;

-- Purpose: Create local tables to mock the SMS-CV database
BEGIN;

CREATE TABLE public.measured_quantity (
	id              serial4 NOT NULL PRIMARY KEY,
	term            varchar(255) NOT NULL,
    provenance_uri  varchar(255),
    definition      text
);

COMMIT;

-- Purpose: Create foreign tables for the SMS-CV database.
DO $$
BEGIN
    IF '${cv_access_type}' = 'db' THEN
        RAISE NOTICE 'Creating foreign tables for sms_cv';

        CREATE FOREIGN TABLE IF NOT EXISTS public.sms_cv_measured_quantity (
            id                  int4 not null,
            term                varchar(255) not null,
            provenance_uri      varchar(255),
            definition          text
        )
            SERVER sms_cv_db OPTIONS (schema_name 'public', table_name 'measured_quantity');

    ELSE
        RAISE NOTICE 'Skipping creation of foreign tables for sms because sms_access_type is not db';
    END IF;
END $$;