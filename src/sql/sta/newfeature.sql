DROP VIEW IF EXISTS FEATURE CASCADE;
CREATE OR REPLACE VIEW FEATURE AS


SELECT DISTINCT

   ('x' || MD5(crd.coordinates::text || crd.action_id))::bit(63)::bigint AS "ID", -- action_type
 	CONCAT(crd.c_label, '_', crd.begin_date) AS "NAME",
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
JOIN ts_coordinates crd ON crd.datastream_id = dsl.datastream_id
-- GROUP BY crd.action_type, crd.coordinates, crd.action_id, c."label", crd.begin_date,  crd.result_time
ORDER BY "ID";