CREATE MATERIALIZED VIEW sms_configuration_static_location_begin_action_newRange AS
SELECT *,
       tstzrange(begin_date, COALESCE(end_date,'infinity'::timestamptz)) AS valid_range
FROM public.configuration_static_location_begin_action;

CREATE MATERIALIZED VIEW sms_configuration_dynamic_location_begin_action_newRange AS
SELECT *,
       tstzrange(begin_date, COALESCE(end_date,'infinity'::timestamptz)) AS valid_range
FROM public.configuration_dynamic_location_begin_action;


CREATE UNIQUE INDEX IF NOT EXISTS idx_sla_id
ON sms_configuration_static_location_begin_action_newRange (id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dla_id
ON sms_configuration_dynamic_location_begin_action_newRange (id);

CREATE INDEX IF NOT EXISTS idx_sla_configuration_id
ON sms_configuration_static_location_begin_action_newRange (configuration_id);
CREATE INDEX IF NOT EXISTS idx_dla_configuration_id
ON sms_configuration_dynamic_location_begin_action_newRange (configuration_id);

CREATE INDEX IF NOT EXISTS idx_sla_valid_range
ON sms_configuration_static_location_begin_action_newRange (valid_range);
CREATE INDEX IF NOT EXISTS idx_dla_valid_range
ON sms_configuration_dynamic_location_begin_action_newRange (valid_range);

CREATE INDEX IF NOT EXISTS idx_dsl_datastream
ON sms_datastream_link(datastream_id);
CREATE INDEX IF NOT EXISTS idx_dsl_device_mount_action_id
ON sms_datastream_link(device_mount_action_id);
CREATE INDEX IF NOT EXISTS idx_dsl_device_property_id
ON sms_datastream_link(device_property_id);
CREATE INDEX IF NOT EXISTS idx_dsl_datasource_id
ON sms_datastream_link(datasource_id);

CREATE INDEX IF NOT EXISTS idx_dma_device_id
ON sms_device_mount_action(device_id);
CREATE INDEX IF NOT EXISTS idx_dma_configuration_id
ON sms_device_mount_action(configuration_id);

CREATE INDEX IF NOT EXISTS idx_dp_device_id
ON sms_device_property(device_id);

CREATE INDEX IF NOT EXISTS idx_ccr_configuration_id
ON sms_configuration_contact_role(configuration_id);
CREATE INDEX IF NOT EXISTS idx_ccr_contact_id
ON sms_configuration_contact_role(contact_id);


