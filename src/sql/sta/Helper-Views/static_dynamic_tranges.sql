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

COMMIT;