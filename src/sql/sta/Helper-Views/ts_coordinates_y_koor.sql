
DROP VIEW IF EXISTS ts_coordinates_y_koor CASCADE;
CREATE OR REPLACE VIEW ts_coordinates_y_koor  AS

  SELECT

                o.result_time,
                o.result_number AS y_koor,
                o.datastream_id
            FROM sms_datastream_link dsl
            JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
            JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
            JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
            WHERE dsl.device_property_id = dla.y_property_id
            -- Bedingung für z-Koordinate