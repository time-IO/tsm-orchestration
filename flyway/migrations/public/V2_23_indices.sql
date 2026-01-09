CREATE UNIQUE INDEX IF NOT EXISTS idx_sla_id
ON sms_configuration_static_location_begin_action (id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dla_id
ON sms_configuration_dynamic_location_begin_action (id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sla_begin_date
ON sms_configuration_static_location_begin_action (begin_date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dla_begin_date
ON sms_configuration_dynamic_location_begin_action (begin_date);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sla_end_date
ON sms_configuration_static_location_begin_action (end_date)
WHERE end_date IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_dla_end_date
ON sms_configuration_dynamic_location_begin_action (end_date)
WHERE end_date IS NOT NULL
;

CREATE INDEX IF NOT EXISTS idx_sla_configuration_id
ON sms_configuration_static_location_begin_action (configuration_id);
CREATE INDEX IF NOT EXISTS idx_dla_configuration_id
ON sms_configuration_dynamic_location_begin_action (configuration_id);


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


