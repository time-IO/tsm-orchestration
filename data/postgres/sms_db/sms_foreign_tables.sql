BEGIN;

CREATE FOREIGN TABLE IF NOT EXISTS public.sms_platform (
    id                  bigint not null,
    description         text,
    short_name          varchar(256) not null,
    long_name           varchar(256),
    manufacturer_uri    varchar(256),
	manufacturer_name   varchar(256) not null,
	model               varchar(256)
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'platform');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device (
    id              bigint not null,
    description     text,
    short_name      varchar(256) not null,
    long_name       varchar(256),
    serial_number   varchar(256),
    model           varchar(256)
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'device');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_device_property (
	id		        bigint not null,
	label		    varchar(256),
	unit_name	    varchar(256),
	property_name	varchar(256) not null,
    property_uri    varchar(256),
    device_id       bigint not null
)
    SERVER sms_db OPTIONS(schema_name 'public', table_name 'device_property');


CREATE FOREIGN TABLE IF NOT EXISTS public.sms_datastream (
    id                  bigint,
    thing_id            uuid,
    device_property_id  integer,
    datasource_id       varchar(256),
    datastream_id       integer,
    begin_date          timestamp with time zone,
    end_date            timestamp with time zone
)
    SERVER sms_db OPTIONS (schema_name 'public', table_name 'datastream_link');

COMMIT;