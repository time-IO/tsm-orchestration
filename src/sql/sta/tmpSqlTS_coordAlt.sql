BEGIN;


 SET search_path TO %(tsm_schema)s;


--- Helper View to get dateranges for different static and dynamic location actions ---
DROP VIEW IF EXISTS "static_dynamic_tsranges" CASCADE;
CREATE OR REPLACE VIEW "static_dynamic_tsranges" AS
SELECT dma.configuration_id as "configuration_id",
	array_agg(DISTINCT tstzrange(sla.begin_date ,sla.end_date, '[]')) AS "static_ranges",
	array_agg(DISTINCT tstzrange(dla.begin_date ,dla.end_date, '[]')) AS "dynamic_ranges",
	sla.id AS "static_id",
	dla.id AS "dynamic_id"
FROM public.sms_datastream_link dsl
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
JOIN public.sms_configuration c ON c.id = dma.configuration_id
JOIN public.sms_device d ON d.id = dma.device_id
LEFT JOIN public.sms_configuration_static_location_begin_action sla ON sla.configuration_id = dma.configuration_id
LEFT JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
WHERE dsl.datasource_id = %(tsm_schema)s
GROUP BY dma.configuration_id, sla.id, dla.id;


--- Helper View to get action type (static or dynamic) for every tsm_observation.result_time ---
DROP VIEW IF EXISTS "ts_action_type" CASCADE;
CREATE OR REPLACE VIEW "ts_action_type" AS
WITH ts_action_type_unfiltered AS (
    SELECT DISTINCT obs.result_time,
        CASE
            WHEN tstzrange(obs.result_time,obs.result_time, '[]') <@ any(ranges.static_ranges) THEN 'static'
            WHEN tstzrange(obs.result_time,obs.result_time, '[]') <@ any(ranges.dynamic_ranges) THEN 'dynamic'
        END AS "action_type",
        CASE
            WHEN tstzrange(obs.result_time,obs.result_time, '[]') <@ any(ranges.static_ranges) THEN ranges.static_id
            WHEN tstzrange(obs.result_time,obs.result_time, '[]') <@ any(ranges.dynamic_ranges) THEN ranges.dynamic_id
        END AS "action_id"
    FROM public.sms_datastream_link dsl
    JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
    JOIN static_dynamic_tsranges ranges ON ranges.configuration_id = dma.configuration_id
    JOIN observation obs ON obs.datastream_id = dsl.datastream_id
)
SELECT result_time, action_type, action_id FROM ts_action_type_unfiltered
WHERE action_type IS NOT NULL AND action_id IS NOT NULL;


--- Helper View to create order for coordinates (x->1, y->2, z->3) to obtain order for FoI coordinates
DROP VIEW IF EXISTS "location_property_order" CASCADE;
CREATE OR REPLACE VIEW "location_property_order" AS
SELECT DISTINCT
	dsl.device_property_id,
	CASE
		WHEN dsl.device_property_id =dla.x_property_id THEN 1
		WHEN dsl.device_property_id =dla.y_property_id THEN 2
		WHEN dsl.device_property_id =dla.z_property_id THEN 3
	END	AS "location_property_order"
FROM public.sms_datastream_link dsl
JOIN public.sms_device_mount_action dma ON dma.id=dsl.device_mount_action_id
JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id =dma.configuration_id
JOIN public.sms_configuration c ON c.id = dma.configuration_id
JOIN public.sms_device d ON d.id = dma.device_id
WHERE dsl.datasource_id = %(tsm_schema)s AND c.is_public AND d.is_public;


--- Helper view to get coordinates for every tsm_observation.result_time
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
				WHEN sla.z IS NULL THEN array[sla.x ,sl a.y]
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