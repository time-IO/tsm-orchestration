BEGIN;

CREATE FOREIGN TABLE IF NOT EXISTS public.measured_quantity (
    id                  int4 not null,
    term                varchar(255) not null,
    provenance_uri      varchar(255),
    definition          text
)
    SERVER sms_cv_db OPTIONS (schema_name 'public', table_name 'measured_quantity');

COMMIT;