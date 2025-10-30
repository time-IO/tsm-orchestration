DROP VIEW IF EXISTS "NEW_FEATURES" CASCADE;
CREATE VIEW "NEW_FEATURES" AS


SELECT DISTINCT

   ('x' || MD5(crd.feature_id))::bit(63)::bigint AS "ID",
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
	jsonb_build_object()  AS "PROPERTIES"


FROM public.sms_datastream_link dsl
JOIN foi_ts_coordinates_v2 crd ON crd.datastream_id = dsl.datastream_id
ORDER BY "ID";

