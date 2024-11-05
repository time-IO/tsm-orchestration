BEGIN;


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_contact (
    id              integer not null,
    organization    varchar(1024),
    given_name      varchar(256),
    family_name     varchar(256),
    email           varchar(256),
    orcid           varchar(32)
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'contact');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_configuration (
    id                      integer not null,
    label                   varchar(256),
    description             text,
    persistent_identifier    varchar(256),
    status                  varchar(256),
    project                 varchar(256),
    is_internal         boolean,
    is_public           boolean
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'configuration');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_configuration_contact_role (
    configuration_id    integer not null,
    contact_id          integer not null
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'configuration_contact_role');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_configuration_dynamic_location_begin_action (
    id                      integer not null,
    label                   varchar(256),
    configuration_id        integer not null,
    begin_date              timestamp with time zone not null,
    x_property_id           integer,
    y_property_id           integer,
    z_property_id           integer,
    epsg_code               varchar(256),
    elevation_datum_name    varchar(256),
    begin_description       text,
    end_date                timestamp with time zone
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'configuration_dynamic_location_begin_action');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_configuration_static_location_begin_action (
    id                  integer not null,
    x                   double precision,
    y                   double precision,
    z                   double precision,
    label               varchar(256),
    configuration_id    integer not null,
    begin_date          timestamp with time zone,
    begin_description   text,
    end_date            timestamp with time zone
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'configuration_static_location_begin_action');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device (
    id                  integer not null,
    short_name          varchar(256),
    description         text,
    device_type_name    varchar(256),
    manufacturer_name   varchar(256),
    model               varchar(256),
    serial_number       varchar(256),
    persistent_identifier varchar(256),
    is_internal         boolean,
    is_public           boolean
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'device');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device_mount_action (
    id                  integer not null,
    configuration_id    integer not null,
    device_id           integer not null,
    offset_x            double precision,
    offset_y            double precision,
    offset_z            double precision,
    begin_date          timestamp with time zone not null,
    end_date            timestamp with time zone
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'device_mount_action');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device_property (
	id		                integer not null,
    device_id               integer not null,
    property_name           varchar(256) not null,
    property_uri            varchar(256),
	label		            varchar(256),
	unit_name	            varchar(256),
    unit_uri                varchar(256),
    resolution              double precision,
    resolution_unit_name    varchar(256),
    accuracy                double precision,
    measuring_range_min     double precision,
    measuring_range_max     double precision,
    aggregation_type_name   varchar(256)
)
    SERVER sms_db OPTIONS(schema_name 'public', table_name 'device_property');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_datastream_link (
    id                  integer not null,
    thing_id            uuid,
    device_property_id  integer not null,
    device_mount_action_id  integer not null,
    datasource_id       varchar(256),
    datastream_id       integer not null,
    begin_date          timestamp with time zone,
    end_date            timestamp with time zone,
    aggregation_period  double precision,
    license_uri         varchar(256),
    license_name        varchar(256)
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'datastream_link');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device_contact_role (
    id          integer not null,
    role_uri    varchar(256) not null,
    role_name   varchar(256) not null,
    contact_id  integer not null,
    device_id   integer not null
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'device_contact_role');


COMMIT;
