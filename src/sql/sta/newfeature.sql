DROP VIEW IF EXISTS FEATURE CASCADE;
CREATE OR REPLACE VIEW FEATURE AS


SELECT DISTINCT

   ('x' || MD5(crd.coordinates::text || crd.action_id))::bit(63)::bigint AS "ID", -- action_type
 	CONCAT(c.label, '_', crd.begin_date) AS "NAME",
	crd.action_type AS "DESCRIPTION",
    'application/geo+json' AS "ENCODING_TYPE",
	jsonb_build_object(
		'type', 'Feature',
		'geometry', jsonb_build_object(
			'type', 'Polygon',
			'coordinates',jsonb_build_array(crd.coordinates)
			)
		) AS "FEATURE",
	jsonb_build_object()  AS "PROPERTIES",
    crd.result_time








FROM public.sms_datastream_link dsl
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
JOIN public.sms_configuration c ON c.id =dma.configuration_id
JOIN public.sms_device d ON d.id = dma.device_id
JOIN ts_coordinates crd ON crd.datastream_id = dsl.datastream_id
GROUP BY crd.action_type, crd.coordinates, crd.action_id, c."label", crd.begin_date,  crd.result_time
ORDER BY "ID";