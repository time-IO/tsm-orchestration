BEGIN;

--- CREATE VIEW FEATURE_OF_INTEREST ---
DROP VIEW IF EXISTS "FEATURES" CASCADE;
CREATE OR REPLACE VIEW "FEATURES" AS
SELECT DISTINCT
    ('x' || MD5(crd.coordinates::text || crd.action_id))::bit(63)::bigint AS "ID",
	CONCAT(c.label, '_', dsl.begin_date) AS "NAME",
	crd."description" AS "DESCRIPTION",
	'application/geo+json' AS "ENCODING_TYPE",
	jsonb_build_object(
		'type', 'Feature',
		'geometry', jsonb_build_object(
			'type', 'Polygon',
			'coordinates',jsonb_build_array(crd.coordinates)
			)
		) AS "FEATURE",
	jsonb_build_object()  AS "PROPERTIES"
FROM public.sms_datastream_link dsl
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
LEFT JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
LEFT JOIN public.sms_configuration_static_location_begin_action sla ON sla.configuration_id = dma.configuration_id
JOIN public.sms_configuration c ON c.id =dma.configuration_id
JOIN public.sms_device d ON d.id = dma.device_id
JOIN observation o ON o.datastream_id = dsl.datastream_id
JOIN ts_coordinates crd on crd.result_time =o.result_time
WHERE dsl.datasource_id = %(tsm_schema)s AND c.is_public AND d.is_public
GROUP BY crd."description", crd.coordinates, crd.action_id, c."label", dsl.begin_date, o.result_time;

COMMIT; 