BEGIN;

create table public.contact
(
    id            serial primary key,
    given_name    varchar(256) not null,
    family_name   varchar(256) not null,
    website       varchar(1024),
    email         varchar(256) not null unique,
    active        boolean,
    created_at    timestamp with time zone,
    updated_at    timestamp with time zone,
    created_by_id integer,
    updated_by_id integer,
    organization  varchar(1024),
    orcid         varchar(32) unique
);


create table public.configuration
(
    created_at            timestamp with time zone,
    updated_at            timestamp with time zone,
    id                    serial not null primary key,
    start_date            timestamp with time zone,
    end_date              timestamp with time zone,
    created_by_id         integer,
    updated_by_id         integer,
    label                 varchar(256),
    status                varchar(256),
    cfg_permission_group  varchar,
    is_internal           boolean,
    is_public             boolean,
    update_description    varchar(256),
    archived              boolean,
    site_id               integer,
    project               varchar(256),
    description           text,
    persistent_identifier varchar(256)
        unique
);


create table public.configuration_contact_role
(
    role_name        varchar      not null,
    role_uri         varchar(256) not null,
    id               serial primary key,
    contact_id       integer      not null,
    configuration_id integer      not null
);


create table public.configuration_dynamic_location_begin_action
(
    created_at           timestamp with time zone,
    updated_at           timestamp with time zone,
    id                   serial primary key,
    configuration_id     integer                  not null,
    begin_date           timestamp with time zone not null,
    begin_description    text,
    begin_contact_id     integer                  not null,
    x_property_id        integer,
    y_property_id        integer,
    z_property_id        integer,
    epsg_code            varchar(256),
    elevation_datum_name varchar(256),
    elevation_datum_uri  varchar(256),
    created_by_id        integer,
    updated_by_id        integer,
    end_date             timestamp with time zone,
    end_description      text,
    end_contact_id       integer,
    label                varchar(256)
);


create table public.device
(
    created_at            timestamp with time zone,
    updated_at            timestamp with time zone,
    id                    serial primary key,
    description           text,
    short_name            varchar(256) not null,
    long_name             varchar(256),
    serial_number         varchar(256),
    manufacturer_uri      varchar(256),
    manufacturer_name     varchar(256) not null,
    dual_use              boolean,
    model                 varchar(256),
    inventory_number      varchar(256),
    persistent_identifier varchar(256) unique,
    website               varchar(1024),
    device_type_uri       varchar(256),
    device_type_name      varchar(256),
    status_uri            varchar(256),
    status_name           varchar(256),
    created_by_id         integer,
    updated_by_id         integer,
    group_ids             character varying[],
    is_private            boolean,
    is_internal           boolean,
    is_public             boolean,
    update_description    varchar(256),
    archived              boolean,
    identifier_type       varchar(256),
    schema_version        varchar(256)
);


create table public.device_mount_action
(
    created_at         timestamp with time zone,
    updated_at         timestamp with time zone,
    id                 serial primary key,
    configuration_id   integer                  not null,
    device_id          integer                  not null,
    parent_platform_id integer,
    begin_date         timestamp with time zone not null,
    begin_description  text,
    begin_contact_id   integer                  not null,
    offset_x           double precision,
    offset_y           double precision,
    offset_z           double precision,
    created_by_id      integer,
    updated_by_id      integer,
    end_date           timestamp with time zone,
    end_description    text,
    end_contact_id     integer
);


create table public.device_property
(
    id                    serial primary key,
    measuring_range_min   double precision,
    measuring_range_max   double precision,
    failure_value         double precision,
    accuracy              double precision,
    label                 varchar(256),
    unit_uri              varchar(256),
    unit_name             varchar(256),
    compartment_uri       varchar(256),
    compartment_name      varchar(256),
    property_uri          varchar(256),
    property_name         varchar(256) not null,
    sampling_media_uri    varchar(256),
    sampling_media_name   varchar(256),
    device_id             integer      not null,
    resolution            double precision,
    resolution_unit_name  varchar(256),
    resolution_unit_uri   varchar(256),
    created_at            timestamp with time zone,
    updated_at            timestamp with time zone,
    created_by_id         integer,
    updated_by_id         integer,
    aggregation_type_uri  varchar(256),
    aggregation_type_name varchar(256)
);


create table public.datastream_link
(
    created_at             timestamp with time zone,
    updated_at             timestamp with time zone,
    id                     serial primary key,
    device_property_id     integer      not null,
    device_mount_action_id integer      not null,
    datasource_id          varchar(256) not null,
    thing_id               varchar(256) not null,
    datastream_id          varchar(256) not null,
    begin_date             timestamp with time zone,
    end_date               timestamp with time zone,
    created_by_id          integer,
    updated_by_id          integer,
    datasource_name        varchar(256),
    thing_name             varchar(256),
    datastream_name        varchar(256),
    license_uri            varchar(256),
    license_name           varchar(256),
    aggregation_period     double precision,
    tsm_endpoint_id        integer
);


COMMIT;

-- public.contact foreign keys
--ALTER TABLE public.contact ADD CONSTRAINT "fk_Contact_created_by_id" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
--ALTER TABLE public.contact ADD CONSTRAINT "fk_Contact_updated_by_id" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);

-- public."user" foreign keys
--ALTER TABLE public."user" ADD CONSTRAINT user_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contact(id);

-- public.configuration foreign keys
--ALTER TABLE public.configuration ADD CONSTRAINT "fk_Configuration_created_by_id" REFERENCES public."user";
--ALTER TABLE public.configuration ADD CONSTRAINT "fk_Configuration_updated_by_id" REFERENCES public."user";

-- public.configuration_static_location_begin_action
--ALTER TABLE public.configuration_static_location_begin_action ADD CONSTRAINT configuration_static_location_begin_action_configuration_id_fkey REFERENCES public.configuration;
--ALTER TABLE public.configuration_static_location_begin_action ADD CONSTRAINT configuration_static_location_begin_action_contact_id_fkey REFERENCES public.contact;
--ALTER TABLE public.configuration_static_location_begin_action CONSTRAINT "fk_ConfigurationStaticLocationBeginAction_created_by_id" REFERENCES public."user";
--ALTER TABLE public.configuration_static_location_begin_action CONSTRAINT "fk_ConfigurationStaticLocationBeginAction_updated_by_id" REFERENCES public."user";

-- public.configuration_dynamic_location_begin_action
--ALTER TABLE public.configuration_dynamic_location_begin_action ADD CONSTRAINT configuration_dynamic_location_begin_action_configuration_id_fkey REFERENCES public.configuration;
--ALTER TABLE public.configuration_dynamic_location_begin_action ADD CONSTRAINT configuration_dynamic_location_begin_action_contact_id_fkey REFERENCES public.contact;
--ALTER TABLE public.configuration_dynamic_location_begin_action CONSTRAINT "fk_ConfigurationDynamicLocationBeginAction_created_by_id" REFERENCES public."user";
--ALTER TABLE public.configuration_dymamic_location_begin_action CONSTRAINT "fk_ConfigurationDynamicLocationBeginAction_updated_by_id" REFERENCES public."user";


