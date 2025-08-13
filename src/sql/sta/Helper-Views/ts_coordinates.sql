BEGIN;

SET search_path TO %(tsm_schema)s;

-- --- Helper view to get coordinates for every tsm_observation.result_time
DROP VIEW IF EXISTS "ts_coordinates" CASCADE;
CREATE OR REPLACE VIEW "ts_coordinates" AS
SELECT DISTINCT
	o.result_time,
	CASE
	    WHEN ts_action.action_type = 'dynamic' THEN ARRAY_AGG(
	        CASE
                WHEN dsl.device_property_id = dla.x_property_id  THEN o.result_number
                WHEN dsl.device_property_id = dla.y_property_id  THEN o.result_number
                WHEN dsl.device_property_id = dla.z_property_id  THEN o.result_number
            END ORDER BY lpo.location_property_order
            )
		WHEN ts_action.action_type = 'static' THEN
	        CASE
				WHEN sla.z IS NULL THEN array[sla.x ,sla.y]
				ELSE array[sla.x ,sla.y, sla.z]
			END
	END AS "coordinates",
	CASE
		WHEN ts_action.action_type = 'dynamic' THEN dla.begin_description
		WHEN ts_action.action_type = 'static' THEN sla.begin_description
	END AS "description",
    ts_action.action_id
FROM public.sms_datastream_link dsl
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
LEFT JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
LEFT JOIN public.sms_configuration_static_location_begin_action sla ON sla.configuration_id = dma.configuration_id
JOIN observation o ON o.datastream_id = dsl.datastream_id
LEFT JOIN location_property_order lpo ON lpo.device_property_id = dsl.device_property_id
JOIN ts_action_type ts_action ON ts_action.result_time  = o.result_time
WHERE (dla.id = ts_action.action_id OR sla.id = ts_action.action_id)
    AND (dla.x_property_id = dsl.device_property_id
        OR dla.y_property_id = dsl.device_property_id
        OR dla.z_property_id = dsl.device_property_id OR sla.id=ts_action.action_id)
GROUP BY o.result_time, ts_action.action_type, sla.x, sla.y, sla.z, dla.begin_description, sla.begin_description, ts_action.action_id ;


COMMIT;