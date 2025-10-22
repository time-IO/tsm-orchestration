-- Helper-View to get x/y/z-coordinates for dyn-action
-- Helper-View to get x-coordinate for dyn-action

DROP VIEW IF EXISTS ts_coordinates_x_koor CASCADE;
CREATE VIEW ts_coordinates_x_koor  AS

            SELECT
                o.result_time,
                o.result_number AS x_koor,
                o.datastream_id
            FROM public.sms_datastream_link dsl
            JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
            JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
            JOIN observation o ON o.datastream_id = dsl.datastream_id
            WHERE dsl.device_property_id = dla.x_property_id;

-- Helper-View to get y-coordinate for dyn-action
DROP VIEW IF EXISTS ts_coordinates_y_koor CASCADE;
CREATE VIEW ts_coordinates_y_koor  AS

  SELECT
                o.result_time,
                o.result_number AS y_koor,
                o.datastream_id
            FROM public.sms_datastream_link dsl
            JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
            JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
            JOIN observation o ON o.datastream_id = dsl.datastream_id
            WHERE dsl.device_property_id = dla.y_property_id;

-- Helper-View to get z-coordinate for dyn-action
DROP VIEW IF EXISTS ts_coordinates_z_koor CASCADE;
CREATE VIEW ts_coordinates_z_koor  AS

            SELECT
                o.result_time,
                o.result_number AS z_koor,
                o.datastream_id
            FROM public.sms_datastream_link dsl
            JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
            JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
            JOIN observation o ON o.datastream_id = dsl.datastream_id
            WHERE dsl.device_property_id = dla.z_property_id;
