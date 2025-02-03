BEGIN;

CREATE FOREIGN TABLE IF NOT EXISTS public.sms_cv_measured_quantity (
    id                  int4 not null,
    term                varchar(255) not null,
    provenance_uri      varchar(255),
    definition          text
)
    SERVER sms_cv_db OPTIONS (schema_name 'public', table_name 'measured_quantity');

CREATE FOREIGN TABLE IF NOT EXISTS public.sms_cv_license (
    id                  int4 not null,
    term                varchar(255) not null,
    provenance_uri      varchar(255),
    provenance          text,
    definition          text
)
    SERVER sms_cv_db OPTIONS (schema_name 'public', table_name 'license');

CREATE FOREIGN TABLE IF NOT EXISTS public.sms_cv_aggregation_type (
    id                  int4 not null,
    term                varchar(255) not null,
    definition          text
)
    SERVER sms_cv_db OPTIONS (schema_name 'public', table_name 'aggregation_type');

CREATE FOREIGN TABLE IF NOT EXISTS public.sms_cv_unit (
    id                  int4 not null,
    term                varchar(255) not null,
    definition          text,
    provenance          text
)
    SERVER sms_cv_db OPTIONS (schema_name 'public', table_name 'unit');

COMMIT;