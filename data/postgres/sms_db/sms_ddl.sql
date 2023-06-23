BEGIN;


-- public.contact definition

CREATE TABLE public.contact (
	id serial4 NOT NULL PRIMARY KEY,
	given_name varchar(256) NOT NULL,
	family_name varchar(256) NOT NULL,
	website varchar(1024) NULL,
	email varchar(256) NOT NULL,
	active bool NULL,
	created_at timestamptz NULL,
	updated_at timestamptz NULL,
	created_by_id int4 NULL,
	updated_by_id int4 NULL
);


-- public."user" definition

CREATE TABLE public."user" (
	id serial4 NOT NULL PRIMARY KEY,
	subject varchar(256) NOT NULL,
	contact_id int4 NOT NULL,
	active bool NULL,
	is_superuser bool NULL,
	apikey varchar(256) NULL
);


-- public.device definition


CREATE TABLE public.device (
	created_at timestamptz NULL,
	updated_at timestamptz NULL,
	id serial4 NOT NULL PRIMARY KEY,
	description text NULL,
	short_name varchar(256) NOT NULL,
	long_name varchar(256) NULL,
	serial_number varchar(256) NULL,
	manufacturer_uri varchar(256) NULL,
	manufacturer_name varchar(256) NOT NULL,
	dual_use bool NULL,
	model varchar(256) NULL,
	inventory_number varchar(256) NULL,
	persistent_identifier varchar(256) NULL,
	website varchar(1024) NULL,
	device_type_uri varchar(256) NULL,
	device_type_name varchar(256) NULL,
	status_uri varchar(256) NULL,
	status_name varchar(256) NULL,
	created_by_id int4 NULL,
	updated_by_id int4 NULL,
	group_ids _varchar NULL,
	is_private bool NULL,
	is_internal bool NULL,
	is_public bool NULL,
	update_description varchar(256) NULL,
	archived bool NULL,
	identifier_type varchar(256) NULL,
	schema_version varchar(256) NULL
);


-- public.device_property definition

CREATE TABLE public.device_property (
	id serial4 NOT NULL PRIMARY KEY,
	measuring_range_min float8 NULL,
	measuring_range_max float8 NULL,
	failure_value float8 NULL,
	accuracy float8 NULL,
	"label" varchar(256) NULL,
	unit_uri varchar(256) NULL,
	unit_name varchar(256) NULL,
	compartment_uri varchar(256) NULL,
	compartment_name varchar(256) NULL,
	property_uri varchar(256) NULL,
	property_name varchar(256) NOT NULL,
	sampling_media_uri varchar(256) NULL,
	sampling_media_name varchar(256) NULL,
	device_id int4 NOT NULL,
	resolution float8 NULL,
	resolution_unit_name varchar(256) NULL,
	resolution_unit_uri varchar(256) NULL
);



-- public.platform definition


CREATE TABLE public.platform (
	created_at timestamptz NULL,
	updated_at timestamptz NULL,
	id serial4 NOT NULL PRIMARY KEY,
	description text NULL,
	short_name varchar(256) NOT NULL,
	long_name varchar(256) NULL,
	manufacturer_uri varchar(256) NULL,
	manufacturer_name varchar(256) NOT NULL,
	model varchar(256) NULL,
	platform_type_uri varchar(256) NULL,
	platform_type_name varchar(256) NULL,
	status_uri varchar(256) NULL,
	status_name varchar(256) NULL,
	website varchar(1024) NULL,
	inventory_number varchar(256) NULL,
	serial_number varchar(256) NULL,
	persistent_identifier varchar(256) NULL,
	created_by_id int4 NULL,
	updated_by_id int4 NULL,
	group_ids _varchar NULL,
	is_private bool NULL,
	is_internal bool NULL,
	is_public bool NULL,
	update_description varchar(256) NULL,
	archived bool NULL,
	identifier_type varchar(256) NULL,
	schema_version varchar(256) NULL
);


-- public."configuration" definition

CREATE TABLE public."configuration" (
	created_at timestamptz NULL,
	updated_at timestamptz NULL,
	id serial4 NOT NULL PRIMARY KEY,
	start_date timestamptz NULL,
	end_date timestamptz NULL,
	created_by_id int4 NULL,
	updated_by_id int4 NULL,
	"label" varchar(256) NULL,
	status varchar(256) NULL,
	cfg_permission_group varchar NULL,
	is_internal bool NULL,
	is_public bool NULL,
	update_description varchar(256) NULL,
	archived bool NULL,
	site_id int4 NULL
);


-- public.device_mount_action definition

CREATE TABLE public.device_mount_action (
	created_at timestamptz NULL,
	updated_at timestamptz NULL,
	id serial4 NOT NULL PRIMARY KEY,
	configuration_id int4 NOT NULL,
	device_id int4 NOT NULL,
	parent_platform_id int4 NULL,
	begin_date timestamptz NOT NULL,
	begin_description text NULL,
	begin_contact_id int4 NOT NULL,
	offset_x float8 NULL,
	offset_y float8 NULL,
	offset_z float8 NULL,
	created_by_id int4 NULL,
	updated_by_id int4 NULL,
	end_date timestamptz NULL,
	end_description text NULL,
	end_contact_id int4 NULL
);


-- public.platform_mount_action definition

CREATE TABLE public.platform_mount_action (
	created_at timestamptz NULL,
	updated_at timestamptz NULL,
	id serial4 NOT NULL PRIMARY KEY,
	configuration_id int4 NOT NULL,
	platform_id int4 NOT NULL,
	parent_platform_id int4 NULL,
	begin_date timestamptz NOT NULL,
	begin_description text NULL,
	begin_contact_id int4 NOT NULL,
	offset_x float8 NULL,
	offset_y float8 NULL,
	offset_z float8 NULL,
	created_by_id int4 NULL,
	updated_by_id int4 NULL,
	end_date timestamptz NULL,
	end_description text NULL,
	end_contact_id int4 NULL
);


-- public.datastream_link definition

CREATE TABLE public.datastream_link (
	created_at timestamptz NULL,
	updated_at timestamptz NULL,
	id serial4 NOT NULL PRIMARY KEY,
	device_property_id int4 NOT NULL,
	device_mount_action_id int4 NOT NULL,
	tsm_endpoint varchar(256) NULL,
	datasource_id varchar(256) NOT NULL,
	thing_id varchar(256) NOT NULL,
	datastream_id varchar(256) NOT NULL,
	begin_date timestamptz NULL,
	end_date timestamptz NULL,
	created_by_id int4 NULL,
	updated_by_id int4 NULL
);





-- public.contact foreign keys

ALTER TABLE public.contact ADD CONSTRAINT "fk_Contact_created_by_id" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
ALTER TABLE public.contact ADD CONSTRAINT "fk_Contact_updated_by_id" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);


-- public."user" foreign keys

ALTER TABLE public."user" ADD CONSTRAINT user_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contact(id);


-- public.device foreign keys

ALTER TABLE public.device ADD CONSTRAINT "fk_Device_created_by_id" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
ALTER TABLE public.device ADD CONSTRAINT "fk_Device_updated_by_id" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);


-- public.device_property foreign keys

ALTER TABLE public.device_property ADD CONSTRAINT device_property_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id);


-- public.platform foreign keys

ALTER TABLE public.platform ADD CONSTRAINT "fk_Platform_created_by_id" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
ALTER TABLE public.platform ADD CONSTRAINT "fk_Platform_updated_by_id" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);


-- public."configuration" foreign keys

ALTER TABLE public."configuration" ADD CONSTRAINT "fk_Configuration_created_by_id" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
ALTER TABLE public."configuration" ADD CONSTRAINT "fk_Configuration_updated_by_id" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);


-- public.device_mount_action foreign keys

ALTER TABLE public.device_mount_action ADD CONSTRAINT device_mount_action_begin_contact_id_fkey FOREIGN KEY (begin_contact_id) REFERENCES public.contact(id);
ALTER TABLE public.device_mount_action ADD CONSTRAINT device_mount_action_configuration_id_fkey FOREIGN KEY (configuration_id) REFERENCES public."configuration"(id);
ALTER TABLE public.device_mount_action ADD CONSTRAINT device_mount_action_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id);
ALTER TABLE public.device_mount_action ADD CONSTRAINT device_mount_action_end_contact_id_fkey FOREIGN KEY (end_contact_id) REFERENCES public.contact(id);
ALTER TABLE public.device_mount_action ADD CONSTRAINT device_mount_action_parent_platform_id_fkey FOREIGN KEY (parent_platform_id) REFERENCES public.platform(id);
ALTER TABLE public.device_mount_action ADD CONSTRAINT "fk_DeviceMountAction_created_by_id" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
ALTER TABLE public.device_mount_action ADD CONSTRAINT "fk_DeviceMountAction_updated_by_id" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);


-- public.platform_mount_action foreign keys

ALTER TABLE public.platform_mount_action ADD CONSTRAINT "fk_PlatformMountAction_created_by_id" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
ALTER TABLE public.platform_mount_action ADD CONSTRAINT "fk_PlatformMountAction_updated_by_id" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
ALTER TABLE public.platform_mount_action ADD CONSTRAINT platform_mount_action_begin_contact_id_fkey FOREIGN KEY (begin_contact_id) REFERENCES public.contact(id);
ALTER TABLE public.platform_mount_action ADD CONSTRAINT platform_mount_action_configuration_id_fkey FOREIGN KEY (configuration_id) REFERENCES public."configuration"(id);
ALTER TABLE public.platform_mount_action ADD CONSTRAINT platform_mount_action_end_contact_id_fkey FOREIGN KEY (end_contact_id) REFERENCES public.contact(id);
ALTER TABLE public.platform_mount_action ADD CONSTRAINT platform_mount_action_parent_platform_id_fkey FOREIGN KEY (parent_platform_id) REFERENCES public.platform(id);
ALTER TABLE public.platform_mount_action ADD CONSTRAINT platform_mount_action_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.platform(id);


-- public.datastream_link foreign keys

ALTER TABLE public.datastream_link ADD CONSTRAINT datastream_link_device_mount_action_id_fkey FOREIGN KEY (device_mount_action_id) REFERENCES public.device_mount_action(id);
ALTER TABLE public.datastream_link ADD CONSTRAINT datastream_link_device_property_id_fkey FOREIGN KEY (device_property_id) REFERENCES public.device_property(id);


COMMIT;
